"""Carga del diccionario de datos (diccionario_datos.csv) para enriquecer el catálogo.

El diccionario aporta definiciones de negocio, clasificación, criticidad y
responsables reales por campo, que el Metadata Agent usa en lugar de heurísticas
cuando está disponible.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pandas as pd

from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)


class DictionaryEntry:
    """Entrada del diccionario para un (tabla, campo)."""

    __slots__ = (
        "business_definition",
        "classification",
        "criticality",
        "data_owner",
        "data_steward",
        "base_rule",
        "source_system",
    )

    def __init__(
        self,
        business_definition: str = "",
        classification: str = "",
        criticality: str = "media",
        data_owner: str = "",
        data_steward: str = "",
        base_rule: str = "",
        source_system: str = "",
    ) -> None:
        self.business_definition = business_definition
        self.classification = classification
        self.criticality = criticality
        self.data_owner = data_owner
        self.data_steward = data_steward
        self.base_rule = base_rule
        self.source_system = source_system


def _normalize_classification(raw: str) -> str:
    """Mapea la clasificación del diccionario al vocabulario de CatalogEntry."""
    key = (raw or "").strip().lower()
    mapping = {
        "personal": "dato personal",
        "sensible": "dato sensible",
        "interno": "dato maestro",
        "financiero": "dato financiero",
        "operativo": "dato operativo",
        "publico": "dato operativo",
        "público": "dato operativo",
    }
    return mapping.get(key, raw.strip() or "dato operativo")


def _criticality_from_flag(es_critico: str) -> str:
    return "alta" if str(es_critico).strip().lower() in {"sí", "si", "true", "1", "x"} else "media"


def load_data_dictionary(path: str | Path | None = None) -> dict[tuple[str, str], DictionaryEntry]:
    """Lee el diccionario y devuelve un mapa (tabla, campo) -> DictionaryEntry.

    Devuelve un dict vacío si el archivo no existe (el Metadata Agent caerá a heurísticas).
    """
    p = Path(path) if path else settings.data_dictionary_path
    if not p.exists():
        logger.info("Diccionario de datos no encontrado en %s; se usarán heurísticas.", p)
        return {}

    df = pd.read_csv(p, encoding="utf-8-sig")
    cols = {c.lower(): c for c in df.columns}

    def get(row, name, default=""):
        col = cols.get(name)
        if col is None or pd.isna(row.get(col)):
            return default
        return str(row[col]).strip()

    out: dict[tuple[str, str], DictionaryEntry] = {}
    for _, row in df.iterrows():
        table = get(row, "tabla").lower()
        field = get(row, "campo").lower()
        if not table or not field:
            continue
        out[(table, field)] = DictionaryEntry(
            business_definition=get(row, "descripcion_negocio"),
            classification=_normalize_classification(get(row, "clasificacion")),
            criticality=_criticality_from_flag(get(row, "es_critico", "No")),
            data_owner=get(row, "data_owner_sugerido"),
            data_steward=get(row, "data_steward_sugerido"),
            base_rule=get(row, "regla_calidad_base"),
            source_system=get(row, "sistema_origen"),
        )
    logger.info("Diccionario de datos cargado: %d campos.", len(out))
    return out


@lru_cache
def get_data_dictionary() -> dict[tuple[str, str], DictionaryEntry]:
    """Diccionario cacheado a nivel de proceso."""
    return load_data_dictionary()
