"""MDM: detección de duplicados y golden record (Módulo 4: MDM Agent).

Técnicas simples y deterministas:
- Coincidencia exacta por clave (DNI/RUC/SKU).
- Similaridad de nombres y correos (rapidfuzz) con normalización.
- Sugerencia de golden record por completitud.
"""

from __future__ import annotations

import pandas as pd
from rapidfuzz import fuzz

from app.schemas.data_schema import GoldenRecord, MdmDuplicateGroup, MdmResult
from app.utils.text_cleaning import normalize_email, normalize_text

# Configuración por entidad: clave exacta, columnas de nombre, id de registro
ENTITY_CONFIG = {
    "cliente": {
        "id": "cliente_id",
        "exact_key": "dni",
        "name_fields": ["nombre", "apellido"],
        "email": "correo",
    },
    "producto": {
        "id": "producto_id",
        "exact_key": "sku",
        "name_fields": ["nombre_producto"],
        "email": None,
    },
    "proveedor": {
        "id": "proveedor_id",
        "exact_key": "ruc",
        "name_fields": ["razon_social"],
        "email": "correo",
    },
    "sucursal": {
        "id": "sucursal_id",
        "exact_key": "sucursal_id",
        "name_fields": ["nombre_sucursal"],
        "email": None,
    },
}

NAME_SIMILARITY_THRESHOLD = 88  # rapidfuzz token_sort_ratio (0-100)


def _col(df: pd.DataFrame, name: str | None) -> str | None:
    if not name:
        return None
    lookup = {c.lower(): c for c in df.columns}
    return lookup.get(name.lower())


def _record_id(row: pd.Series, id_col: str | None, idx: int) -> str:
    if id_col and pd.notna(row.get(id_col)):
        return str(row[id_col])
    return f"row_{idx}"


def detect_duplicates(entity: str, df: pd.DataFrame) -> MdmResult:
    """Detecta grupos de duplicados para una entidad maestra."""
    cfg = ENTITY_CONFIG.get(entity)
    if cfg is None:
        return MdmResult(entity=entity, total_records=int(df.shape[0]))

    id_col = _col(df, cfg["id"])
    key_col = _col(df, cfg["exact_key"])
    name_cols = [c for c in (_col(df, f) for f in cfg["name_fields"]) if c]
    email_col = _col(df, cfg["email"])

    groups: list[MdmDuplicateGroup] = []
    assigned: set[int] = set()

    # 1) Coincidencia exacta por clave (DNI/RUC/SKU)
    if key_col:
        for key_value, sub in df.groupby(df[key_col].astype(str).str.strip()):
            if key_value in ("", "nan", "None") or len(sub) < 2:
                continue
            idxs = list(sub.index)
            assigned.update(idxs)
            groups.append(
                _build_group(
                    entity,
                    df,
                    idxs,
                    id_col,
                    name_cols,
                    match_type="exact_key",
                    confidence=0.98,
                    evidence=[
                        f"{cfg['exact_key']}={key_value} compartido por {len(idxs)} registros"
                    ],
                )
            )

    # 2) Similaridad de nombres entre registros aún no agrupados
    if name_cols:
        remaining = [i for i in df.index if i not in assigned]
        norm_names = {
            i: normalize_text(
                " ".join(str(df.at[i, c]) for c in name_cols if pd.notna(df.at[i, c]))
            )
            for i in remaining
        }
        used: set[int] = set()
        for a_pos, i in enumerate(remaining):
            if i in used or not norm_names[i]:
                continue
            cluster = [i]
            for j in remaining[a_pos + 1 :]:
                if j in used or not norm_names[j]:
                    continue
                score = fuzz.token_sort_ratio(norm_names[i], norm_names[j])
                email_match = (
                    email_col
                    and normalize_email(str(df.at[i, email_col]))
                    == normalize_email(str(df.at[j, email_col]))
                    and normalize_email(str(df.at[i, email_col])) != ""
                )
                if score >= NAME_SIMILARITY_THRESHOLD or email_match:
                    cluster.append(j)
                    used.add(j)
            if len(cluster) > 1:
                used.update(cluster)
                conf = round(
                    min(0.97, NAME_SIMILARITY_THRESHOLD / 100 + 0.02 * (len(cluster) - 1)), 2
                )
                groups.append(
                    _build_group(
                        entity,
                        df,
                        cluster,
                        id_col,
                        name_cols,
                        match_type="fuzzy_name",
                        confidence=conf,
                        evidence=[
                            f"Nombres muy similares ({'; '.join(norm_names[c] for c in cluster)})"
                        ],
                    )
                )

    return MdmResult(entity=entity, total_records=int(df.shape[0]), duplicate_groups=groups)


def _build_group(
    entity, df, idxs, id_col, name_cols, match_type, confidence, evidence
) -> MdmDuplicateGroup:
    member_ids = [_record_id(df.loc[i], id_col, i) for i in idxs]
    golden = _golden_record(df, idxs)
    return MdmDuplicateGroup(
        entity=entity,
        member_ids=member_ids,
        match_type=match_type,
        confidence=confidence,
        golden_record=golden,
        evidence=evidence,
    )


def _golden_record(df: pd.DataFrame, idxs: list[int]) -> GoldenRecord:
    """Construye un golden record eligiendo, por columna, el valor no nulo más frecuente/largo."""
    values: dict[str, object] = {}
    sub = df.loc[idxs]
    for col in df.columns:
        non_null = sub[col].dropna()
        non_null = non_null[non_null.astype(str).str.strip() != ""]
        if non_null.empty:
            continue
        # Preferir el valor más frecuente; ante empate, el más largo (más completo)
        counts = non_null.value_counts()
        top = counts.index[0]
        if counts.iloc[0] == 1:
            top = max(non_null.tolist(), key=lambda v: len(str(v)))
        values[col] = _jsonable(top)
    return GoldenRecord(values=values)


def _jsonable(value):
    import numpy as np

    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    return value


def detect_entity_from_table(table_name: str) -> str | None:
    """Mapea un nombre de tabla a una entidad MDM (clientes->cliente, etc.)."""
    n = table_name.lower()
    for entity in ENTITY_CONFIG:
        if n.startswith(entity):
            return entity
    return None
