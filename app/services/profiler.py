"""Perfilamiento técnico de datasets (Módulo 2: Data Profiling Agent)."""

from __future__ import annotations

import re

import numpy as np
import pandas as pd

from app.schemas.data_schema import ColumnProfile, TableProfile
from app.services.entities import unique_key_fields

# Patrones para detectar datos personales / sensibles
SENSITIVE_NAME_HINTS = {
    "dni": "documento de identidad",
    "ruc": "identificador tributario",
    "correo": "correo electrónico",
    "email": "correo electrónico",
    "mail": "correo electrónico",
    "telefono": "número telefónico",
    "phone": "número telefónico",
    "celular": "número telefónico",
    "direccion": "dirección física",
    "address": "dirección física",
    "nombre": "nombre de persona",
    "apellido": "apellido de persona",
    "tarjeta": "dato financiero",
    "cuenta": "dato financiero",
    "pasaporte": "documento de identidad",
}

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
DIGITS_RE = re.compile(r"^\d+$")

# Columnas que suelen ser identificadores por nombre
ID_NAME_HINTS = ("_id", "id_", "dni", "ruc", "sku", "codigo", "code")

HIGH_CARDINALITY_RATIO = 0.9
CONSTANT_UNIQUE = 1


def _looks_like_identifier(name: str, unique_ratio: float) -> bool:
    n = name.lower()
    if n == "id" or n.endswith("_id") or n.startswith("id_"):
        return True
    if any(h in n for h in ID_NAME_HINTS) and unique_ratio > 0.5:
        return True
    return unique_ratio >= 0.98


def _sensitive_reason(name: str, series: pd.Series) -> str | None:
    n = name.lower()
    for hint, reason in SENSITIVE_NAME_HINTS.items():
        if hint in n:
            return reason
    # Heurística por contenido: muchos valores con forma de email
    sample = series.dropna().astype(str).head(50)
    if len(sample) and (sample.map(lambda v: bool(EMAIL_RE.match(v.strip()))).mean() > 0.6):
        return "correo electrónico"
    return None


def _column_profile(name: str, series: pd.Series, n_rows: int) -> ColumnProfile:
    non_null = int(series.notna().sum())
    null_count = int(series.isna().sum())
    unique_count = int(series.nunique(dropna=True))
    unique_ratio = unique_count / non_null if non_null else 0.0

    cmin = cmax = cmean = None
    if pd.api.types.is_numeric_dtype(series):
        numeric = pd.to_numeric(series, errors="coerce")
        if numeric.notna().any():
            cmin = float(np.nanmin(numeric.values))
            cmax = float(np.nanmax(numeric.values))
            cmean = float(np.nanmean(numeric.values))

    reason = _sensitive_reason(name, series)

    return ColumnProfile(
        name=name,
        dtype=str(series.dtype),
        non_null=non_null,
        null_count=null_count,
        null_pct=round(100 * null_count / n_rows, 2) if n_rows else 0.0,
        unique_count=unique_count,
        is_constant=unique_count <= CONSTANT_UNIQUE,
        is_high_cardinality=unique_ratio >= HIGH_CARDINALITY_RATIO and non_null > 1,
        is_possible_identifier=_looks_like_identifier(name, unique_ratio),
        is_possible_sensitive=reason is not None,
        sensitive_reason=reason,
        min=cmin,
        max=cmax,
        mean=round(cmean, 4) if cmean is not None else None,
        sample_values=[_jsonable(v) for v in series.dropna().head(3).tolist()],
    )


def _jsonable(value):
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    return value


def _key_candidates(table_name: str, df: pd.DataFrame) -> list[str]:
    """Columnas clave para medir duplicados: PK de la tabla + claves de negocio.

    Excluye las claves foráneas (que se repiten legítimamente) usando el modelo
    de datos centralizado en ``app.services.entities``.
    """
    return unique_key_fields(table_name, df.columns)


def profile_dataframe(table_name: str, df: pd.DataFrame) -> TableProfile:
    """Genera un TableProfile completo a partir de un DataFrame."""
    n_rows = int(df.shape[0])
    column_profiles = [_column_profile(col, df[col], n_rows) for col in df.columns]

    nulls = {cp.name: cp.null_count for cp in column_profiles if cp.null_count > 0}

    # Duplicados por columnas clave
    duplicates: dict[str, int] = {}
    for col in _key_candidates(table_name, df):
        dup = int(df[col].dropna().duplicated().sum())
        if dup > 0:
            duplicates[col] = dup

    sensitive = [cp.name for cp in column_profiles if cp.is_possible_sensitive]
    identifiers = [cp.name for cp in column_profiles if cp.is_possible_identifier]
    constants = [cp.name for cp in column_profiles if cp.is_constant]

    return TableProfile(
        table=table_name,
        rows=n_rows,
        columns=int(df.shape[1]),
        duplicate_rows=int(df.duplicated().sum()),
        nulls=nulls,
        duplicates=duplicates,
        possible_sensitive_fields=sensitive,
        possible_identifier_fields=identifiers,
        constant_fields=constants,
        column_profiles=column_profiles,
    )
