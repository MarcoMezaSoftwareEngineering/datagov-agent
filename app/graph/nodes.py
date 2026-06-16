"""Nodos del grafo: cada uno envuelve a un agente y actualiza el estado."""

from __future__ import annotations

from app.agents import (
    mdm_agent,
    metadata_agent,
    profiler_agent,
    quality_agent,
    rag_agent,
    recommendation_agent,
    report_agent,
    supervisor,
)
from app.graph.state import GraphState
from app.services.mdm import detect_entity_from_table
from app.services.vector_store import BaseVectorStore, InMemoryVectorStore


def _log(state: GraphState, message: str) -> list[str]:
    messages = list(state.get("messages", []))
    messages.append(message)
    return messages


def _get_store(state: GraphState) -> BaseVectorStore:
    extra = state.get("extra") or {}
    store = extra.get("vector_store")
    if isinstance(store, BaseVectorStore):
        return store
    store = InMemoryVectorStore()
    state.setdefault("extra", {})["vector_store"] = store
    return store


# --------------------------------------------------------------------------- routing


def load_input(state: GraphState) -> GraphState:
    return {"messages": _log(state, "Entrada cargada.")}


def classify_input(state: GraphState) -> GraphState:
    decision = supervisor.classify_input(
        question=state.get("question"),
        file_name=state.get("file_name"),
        intent=state.get("intent"),
    )
    return {
        "route": decision["route"],
        "route_reason": decision["reason"],
        "messages": _log(state, f"Ruta seleccionada: {decision['route']} ({decision['reason']})"),
    }


def route_decision(state: GraphState) -> str:
    """Función de ruteo condicional para LangGraph."""
    route = state.get("route", "dataset_analysis")
    if route in ("dataset_analysis", "mdm_analysis", "report_generation", "recommendation_request"):
        return "dataset"
    if route == "document_ingestion":
        return "document"
    if route == "rag_question":
        return "question"
    return "dataset"


# --------------------------------------------------------------------------- dataset branch


def profile_data(state: GraphState) -> GraphState:
    tables = state.get("tables", {})
    profiles = [profiler_agent.run_profiler(name, df) for name, df in tables.items()]
    return {"profiles": profiles, "messages": _log(state, f"Perfilados {len(profiles)} datasets.")}


def evaluate_quality(state: GraphState) -> GraphState:
    tables = state.get("tables", {})
    reports = [quality_agent.run_quality(name, df, related=tables) for name, df in tables.items()]
    return {
        "quality_reports": reports,
        "messages": _log(state, f"Calidad evaluada en {len(reports)} tablas."),
    }


def detect_mdm(state: GraphState) -> GraphState:
    tables = state.get("tables", {})
    results = []
    for name, df in tables.items():
        entity = detect_entity_from_table(name)
        if entity:
            results.append(mdm_agent.run_mdm(name, df, entity))
    return {
        "mdm_results": results,
        "messages": _log(state, f"MDM ejecutado en {len(results)} entidades."),
    }


def update_catalog(state: GraphState) -> GraphState:
    profiles = state.get("profiles", [])
    quality_by_table = {q.table: q for q in state.get("quality_reports", [])}
    catalog = []
    for prof in profiles:
        catalog += metadata_agent.run_metadata(prof, quality_by_table.get(prof.table))
    return {"catalog": catalog, "messages": _log(state, f"Catálogo con {len(catalog)} campos.")}


def generate_recommendations(state: GraphState) -> GraphState:
    recs = recommendation_agent.run_recommendations(
        state.get("quality_reports", []), state.get("mdm_results", [])
    )
    return {
        "recommendations": recs,
        "messages": _log(state, f"{len(recs)} recomendaciones generadas."),
    }


def generate_report(state: GraphState) -> GraphState:
    report = report_agent.build_report(
        profiles=state.get("profiles", []),
        quality_reports=state.get("quality_reports", []),
        mdm_results=state.get("mdm_results", []),
        catalog=state.get("catalog", []),
        recommendations=state.get("recommendations", []),
    )
    return {"report": report, "messages": _log(state, "Reporte ejecutivo generado.")}


# --------------------------------------------------------------------------- document branch


def ingest_documents(state: GraphState) -> GraphState:
    store = _get_store(state)
    docs = state.get("documents", [])
    n = rag_agent.ingest_documents(store, docs)
    return {
        "ingested_chunks": n,
        "messages": _log(state, f"{n} chunks indexados en el vector store."),
    }


# --------------------------------------------------------------------------- question branch


def answer_with_rag(state: GraphState) -> GraphState:
    store = _get_store(state)
    answer = rag_agent.answer_question(store, state.get("question", ""))
    return {"rag_answer": answer, "messages": _log(state, "Respuesta RAG generada.")}
