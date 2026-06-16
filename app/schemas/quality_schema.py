"""Esquemas para calidad de datos, catálogo, RAG y recomendaciones."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Severity = Literal["alta", "media", "baja"]
RiskLevel = Literal["alto", "medio", "bajo"]


class QualityFinding(BaseModel):
    """Hallazgo de calidad (Módulo 3: Data Quality Agent)."""

    table: str
    field: str
    problem: str
    quality_dimension: (
        str  # completitud, unicidad, validez, consistencia, integridad, conformidad...
    )
    severity: Severity = "media"
    suggested_rule: str = ""
    affected_count: int = 0


class QualityReport(BaseModel):
    """Reporte de calidad por tabla con score (§24)."""

    table: str
    rows: int = 0
    findings: list[QualityFinding] = Field(default_factory=list)
    quality_score: int = 100
    risk_level: RiskLevel = "bajo"
    main_issues: list[str] = Field(default_factory=list)
    narrative: str = ""


class CatalogEntry(BaseModel):
    """Entrada del catálogo de datos (Módulo 5: Metadata & Catalog Agent)."""

    table: str
    field: str
    business_definition: str = ""
    classification: str = "dato operativo"  # dato personal, dato sensible, dato operativo...
    criticality: str = "media"  # alta | media | baja
    data_owner: str = ""
    data_steward: str = ""
    update_frequency: str = "no definida"
    quality_rules: list[str] = Field(default_factory=list)


class RagAnswer(BaseModel):
    """Respuesta del RAG Policy Agent (Módulo 6)."""

    question: str
    answer: str
    rationale: str = ""
    sources: list[str] = Field(default_factory=list)
    confidence: str = "media"  # alta | media | baja
    grounded: bool = True


class Recommendation(BaseModel):
    """Recomendación ejecutiva (Módulo 7: Recommendation Agent)."""

    priority: str = "media"  # alta | media | baja
    title: str = ""
    risk: str = ""
    suggested_action: str = ""
    responsible: str = ""
    expected_impact: str = ""
    estimated_effort: str = ""
