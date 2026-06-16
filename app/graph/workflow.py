"""Construcción del grafo LangGraph con ruteo condicional (§13)."""

from __future__ import annotations

from functools import lru_cache

from langgraph.graph import END, START, StateGraph

from app.graph import nodes
from app.graph.state import GraphState


def build_workflow():
    """Crea y compila el StateGraph del flujo principal."""
    graph = StateGraph(GraphState)

    # Nodos comunes
    graph.add_node("load_input", nodes.load_input)
    graph.add_node("classify_input", nodes.classify_input)

    # Rama dataset
    graph.add_node("profile_data", nodes.profile_data)
    graph.add_node("evaluate_quality", nodes.evaluate_quality)
    graph.add_node("detect_mdm", nodes.detect_mdm)
    graph.add_node("update_catalog", nodes.update_catalog)
    graph.add_node("generate_recommendations", nodes.generate_recommendations)
    graph.add_node("generate_report", nodes.generate_report)

    # Rama documento
    graph.add_node("ingest_documents", nodes.ingest_documents)

    # Rama pregunta
    graph.add_node("answer_with_rag", nodes.answer_with_rag)

    # Aristas
    graph.add_edge(START, "load_input")
    graph.add_edge("load_input", "classify_input")

    graph.add_conditional_edges(
        "classify_input",
        nodes.route_decision,
        {
            "dataset": "profile_data",
            "document": "ingest_documents",
            "question": "answer_with_rag",
        },
    )

    # Cadena de la rama dataset
    graph.add_edge("profile_data", "evaluate_quality")
    graph.add_edge("evaluate_quality", "detect_mdm")
    graph.add_edge("detect_mdm", "update_catalog")
    graph.add_edge("update_catalog", "generate_recommendations")
    graph.add_edge("generate_recommendations", "generate_report")
    graph.add_edge("generate_report", END)

    # Fin de ramas document / question
    graph.add_edge("ingest_documents", END)
    graph.add_edge("answer_with_rag", END)

    return graph.compile()


@lru_cache
def get_workflow():
    """Workflow compilado y cacheado."""
    return build_workflow()
