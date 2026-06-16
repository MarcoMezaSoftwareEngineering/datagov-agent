"""Esquemas Pydantic compartidos por servicios, agentes, API y UI."""

from app.schemas.data_schema import (
    ColumnProfile,
    FileMetadata,
    GoldenRecord,
    MdmDuplicateGroup,
    MdmResult,
    TableProfile,
)
from app.schemas.quality_schema import (
    CatalogEntry,
    QualityFinding,
    QualityReport,
    RagAnswer,
    Recommendation,
)
from app.schemas.report_schema import ExecutiveReport

__all__ = [
    "FileMetadata",
    "ColumnProfile",
    "TableProfile",
    "GoldenRecord",
    "MdmDuplicateGroup",
    "MdmResult",
    "QualityFinding",
    "QualityReport",
    "CatalogEntry",
    "RagAnswer",
    "Recommendation",
    "ExecutiveReport",
]
