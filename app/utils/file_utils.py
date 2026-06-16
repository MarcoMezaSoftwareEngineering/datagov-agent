"""Helpers para identificar y manejar archivos de entrada."""

from __future__ import annotations

from pathlib import Path

TABULAR_EXTS = {".csv", ".xlsx", ".xls"}
DOCUMENT_EXTS = {".pdf", ".txt", ".md", ".docx"}


def file_extension(path: str | Path) -> str:
    return Path(path).suffix.lower()


def is_tabular(path: str | Path) -> bool:
    return file_extension(path) in TABULAR_EXTS


def is_document(path: str | Path) -> bool:
    return file_extension(path) in DOCUMENT_EXTS


def file_kind(path: str | Path) -> str:
    """Clasifica el archivo en 'tabular', 'document' o 'unknown'."""
    if is_tabular(path):
        return "tabular"
    if is_document(path):
        return "document"
    return "unknown"


def classify_document_type(name: str) -> str:
    """Clasificación documental heurística por el nombre del archivo."""
    n = name.lower()
    if any(k in n for k in ("politica", "policy")):
        return "politica"
    if any(k in n for k in ("manual", "calidad", "quality")):
        return "manual_calidad"
    if "glosario" in n or "glossary" in n:
        return "glosario"
    if any(k in n for k in ("rol", "role", "responsab")):
        return "roles"
    if "diccionario" in n or "dictionary" in n:
        return "diccionario"
    if "roadmap" in n:
        return "roadmap"
    if any(k in n for k in ("arquitectura", "architecture")):
        return "arquitectura"
    if any(k in n for k in ("checklist", "migracion", "migration")):
        return "checklist"
    if any(k in n for k in ("regla", "rule", "negocio")):
        return "reglas_negocio"
    return "documento"
