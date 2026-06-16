"""Estado global del workflow LangGraph."""

from __future__ import annotations

from typing import Any, TypedDict

import pandas as pd

from app.schemas.data_schema import MdmResult, TableProfile
from app.schemas.quality_schema import CatalogEntry, QualityReport, RagAnswer, Recommendation
from app.schemas.report_schema import ExecutiveReport


class GraphState(TypedDict, total=False):
    """Estado compartido entre nodos del grafo."""

    # Entrada
    question: str | None
    file_name: str | None
    intent: str | None
    tables: dict[str, pd.DataFrame]  # nombre -> DataFrame (datasets)
    documents: list[tuple[str, str]]  # (texto, fuente)

    # Decisión del supervisor
    route: str
    route_reason: str

    # Resultados por agente
    profiles: list[TableProfile]
    quality_reports: list[QualityReport]
    mdm_results: list[MdmResult]
    catalog: list[CatalogEntry]
    recommendations: list[Recommendation]
    rag_answer: RagAnswer
    report: ExecutiveReport

    # Misc
    ingested_chunks: int
    messages: list[str]
    error: str | None
    extra: dict[str, Any]
