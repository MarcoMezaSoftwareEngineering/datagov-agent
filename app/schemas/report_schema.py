"""Esquema del reporte ejecutivo final (Módulo 8: Report Agent)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.data_schema import MdmResult, TableProfile
from app.schemas.quality_schema import CatalogEntry, QualityReport, Recommendation


class ExecutiveReport(BaseModel):
    """Reporte ejecutivo de gobierno de datos."""

    title: str = "Reporte Ejecutivo de Gobierno de Datos - DataGov Agent"
    generated_at: datetime = Field(default_factory=datetime.now)
    executive_summary: str = ""
    datasets: list[str] = Field(default_factory=list)
    profiles: list[TableProfile] = Field(default_factory=list)
    quality_reports: list[QualityReport] = Field(default_factory=list)
    mdm_results: list[MdmResult] = Field(default_factory=list)
    catalog: list[CatalogEntry] = Field(default_factory=list)
    recommendations: list[Recommendation] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    roadmap: list[str] = Field(default_factory=list)
    overall_score: int = 100
    kpis: dict[str, float | int] = Field(default_factory=dict)
