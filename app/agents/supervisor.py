"""Supervisor Agent: decide la ruta a ejecutar (§14, §15)."""

from __future__ import annotations

from app.agents.prompts import SUPERVISOR_SYSTEM
from app.services.llm import get_llm
from app.utils.file_utils import file_kind
from app.utils.text_cleaning import extract_json

VALID_ROUTES = {
    "dataset_analysis",
    "document_ingestion",
    "rag_question",
    "mdm_analysis",
    "report_generation",
    "recommendation_request",
}


def classify_input(
    *,
    question: str | None = None,
    file_name: str | None = None,
    intent: str | None = None,
) -> dict:
    """Determina la ruta. Usa heurística determinista y, si hay LLM, lo consulta como apoyo."""
    # 1) Señales deterministas fuertes
    if intent in VALID_ROUTES:
        return {"route": intent, "reason": "Intent explícito del usuario."}

    if file_name:
        kind = file_kind(file_name)
        if kind == "tabular":
            return {
                "route": "dataset_analysis",
                "reason": "Se cargó un archivo tabular (CSV/Excel).",
            }
        if kind == "document":
            return {
                "route": "document_ingestion",
                "reason": "Se cargó un documento (PDF/TXT/MD/DOCX).",
            }

    if question:
        q = question.lower()
        if any(k in q for k in ("duplicad", "golden record", "consolidad", "mdm")):
            return {"route": "mdm_analysis", "reason": "La pregunta menciona duplicados/MDM."}
        if any(k in q for k in ("reporte", "report", "ejecutivo")):
            return {"route": "report_generation", "reason": "Solicita un reporte."}
        if any(k in q for k in ("recomienda", "recomendac", "prioriza", "acciones")):
            return {"route": "recommendation_request", "reason": "Solicita recomendaciones."}
        # 2) Apoyo del LLM para preguntas ambiguas
        llm_route = _llm_route(question)
        if llm_route:
            return llm_route
        return {"route": "rag_question", "reason": "Pregunta de conocimiento → RAG por defecto."}

    return {"route": "dataset_analysis", "reason": "Ruta por defecto."}


def _llm_route(question: str) -> dict | None:
    llm = get_llm()
    raw = llm.complete(SUPERVISOR_SYSTEM, f"Entrada del usuario: {question}", json_mode=True)
    data = extract_json(raw) if raw else None
    if isinstance(data, dict) and data.get("route") in VALID_ROUTES:
        return {
            "route": data["route"],
            "reason": data.get("reason", "Decisión del LLM supervisor."),
        }
    return None
