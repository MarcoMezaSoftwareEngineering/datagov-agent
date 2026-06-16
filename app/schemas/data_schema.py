"""Esquemas para ingestión, perfilamiento y MDM."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, computed_field


class FileMetadata(BaseModel):
    """Metadatos de un archivo cargado (Módulo 1: Data Ingestion)."""

    file_name: str
    file_type: str  # csv, xlsx, pdf, txt, md, docx
    kind: str = "tabular"  # tabular | document
    doc_type: str | None = None  # clasificación documental
    rows: int | None = None
    columns: int | None = None
    loaded_at: datetime = Field(default_factory=datetime.now)
    status: str = "loaded"


class ColumnProfile(BaseModel):
    """Perfil técnico de una columna."""

    name: str
    dtype: str
    non_null: int
    null_count: int
    null_pct: float
    unique_count: int
    is_constant: bool = False
    is_high_cardinality: bool = False
    is_possible_identifier: bool = False
    is_possible_sensitive: bool = False
    sensitive_reason: str | None = None
    min: Any | None = None
    max: Any | None = None
    mean: float | None = None
    sample_values: list[Any] = Field(default_factory=list)


class TableProfile(BaseModel):
    """Perfil técnico de una tabla (Módulo 2: Data Profiling Agent)."""

    table: str
    rows: int
    columns: int
    duplicate_rows: int = 0
    nulls: dict[str, int] = Field(default_factory=dict)
    duplicates: dict[str, int] = Field(default_factory=dict)
    possible_sensitive_fields: list[str] = Field(default_factory=list)
    possible_identifier_fields: list[str] = Field(default_factory=list)
    constant_fields: list[str] = Field(default_factory=list)
    column_profiles: list[ColumnProfile] = Field(default_factory=list)


class GoldenRecord(BaseModel):
    """Registro consolidado sugerido para un grupo de duplicados."""

    values: dict[str, Any] = Field(default_factory=dict)


class MdmDuplicateGroup(BaseModel):
    """Grupo de posibles duplicados de una entidad maestra (Módulo 4: MDM Agent)."""

    entity: str
    member_ids: list[str] = Field(default_factory=list)
    match_type: str = ""  # exact_key | fuzzy_name | fuzzy_email
    confidence: float = 0.0
    golden_record: GoldenRecord = Field(default_factory=GoldenRecord)
    evidence: list[str] = Field(default_factory=list)


class MdmResult(BaseModel):
    """Resultado MDM para una entidad."""

    entity: str
    total_records: int = 0
    duplicate_groups: list[MdmDuplicateGroup] = Field(default_factory=list)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def duplicates_detected(self) -> int:
        return sum(max(0, len(g.member_ids) - 1) for g in self.duplicate_groups)
