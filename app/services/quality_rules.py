"""Reglas de calidad de datos deterministas (Módulo 3) + cálculo de score (§24).

El trabajo pesado es puro pandas, sin depender del LLM. El agente de calidad
añade narrativa encima de estos hallazgos.
"""

from __future__ import annotations

import re
from datetime import datetime

import pandas as pd

from app.schemas.quality_schema import QualityFinding, QualityReport
from app.utils.text_cleaning import normalize_country, normalize_text

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
DNI_RE = re.compile(r"^\d{8}$")
RUC_RE = re.compile(r"^\d{11}$")

SENSITIVE_HINTS = ("dni", "ruc", "correo", "email", "telefono", "direccion", "nombre", "apellido")

# Penalizaciones por dimensión (inspiradas en §24) y tope por dimensión para no
# sobre-penalizar. Los topes suman ~85, de modo que el peor caso aterriza ~15 (no 0)
# y las tablas con menos dimensiones afectadas obtienen scores diferenciados.
PENALTY = {
    "completitud_critico": 10,
    "completitud": 2,
    "unicidad": 18,
    "validez": 7,
    "integridad referencial": 18,
    "consistencia": 5,
    "conformidad": 6,
    "clasificacion": 8,
}
DIMENSION_CAP = {
    "completitud": 16,
    "unicidad": 18,
    "validez": 14,
    "integridad referencial": 18,
    "consistencia": 5,
    "conformidad": 6,
    "clasificacion": 8,
}

# Relaciones FK conocidas: columna -> (tabla_padre, columna_padre)
FK_RELATIONS = {
    "cliente_id": ("clientes", "cliente_id"),
    "producto_id": ("productos", "producto_id"),
    "proveedor_id": ("proveedores", "proveedor_id"),
}


def _is_critical(field: str) -> bool:
    f = field.lower()
    return any(h in f for h in SENSITIVE_HINTS) or f.endswith("_id") or f in {"sku"}


def _empty_mask(series: pd.Series) -> pd.Series:
    """Marca nulos y cadenas vacías como faltantes."""
    as_str = series.astype("string").str.strip()
    return series.isna() | (as_str == "") | (as_str.str.lower() == "nan")


def evaluate_quality(
    table: str,
    df: pd.DataFrame,
    related: dict[str, pd.DataFrame] | None = None,
) -> QualityReport:
    """Evalúa la calidad de una tabla y devuelve hallazgos + score."""
    related = related or {}
    findings: list[QualityFinding] = []
    cols = {c.lower(): c for c in df.columns}

    findings += _check_completeness(table, df)
    findings += _check_uniqueness(table, df)
    findings += _check_validity(table, df, cols)
    findings += _check_consistency(table, df)
    findings += _check_total_calculation(table, df, cols)
    findings += _check_referential_integrity(table, df, related)
    findings += _check_classification(table, df)

    score, risk = _score(findings)
    main_issues = _main_issues(findings)

    return QualityReport(
        table=table,
        rows=int(df.shape[0]),
        findings=findings,
        quality_score=score,
        risk_level=risk,
        main_issues=main_issues,
    )


# --------------------------------------------------------------------------- checks


def _check_completeness(table: str, df: pd.DataFrame) -> list[QualityFinding]:
    out = []
    for col in df.columns:
        missing = int(_empty_mask(df[col]).sum())
        if missing == 0:
            continue
        critical = _is_critical(col)
        out.append(
            QualityFinding(
                table=table,
                field=col,
                problem=f"{missing} valores nulos o vacíos",
                quality_dimension="completitud",
                severity="alta" if critical else "media",
                suggested_rule=f"Campo {'obligatorio' if critical else 'recomendado'}: no permitir vacíos",
                affected_count=missing,
            )
        )
    return out


def _check_uniqueness(table: str, df: pd.DataFrame) -> list[QualityFinding]:
    out = []
    for col in df.columns:
        n = col.lower()
        if not (n.endswith("_id") or n in {"dni", "ruc", "sku"}):
            continue
        non_null = df[col][~_empty_mask(df[col])]
        dup = int(non_null.duplicated().sum())
        if dup > 0:
            out.append(
                QualityFinding(
                    table=table,
                    field=col,
                    problem=f"{dup} valores duplicados en identificador",
                    quality_dimension="unicidad",
                    severity="alta",
                    suggested_rule=f"Validar unicidad de {col}",
                    affected_count=dup,
                )
            )
    return out


def _check_validity(table: str, df: pd.DataFrame, cols: dict[str, str]) -> list[QualityFinding]:
    out = []

    def invalid_count(col: str, pattern: re.Pattern) -> int:
        series = df[col][~_empty_mask(df[col])].astype(str).str.strip()
        return int((~series.map(lambda v: bool(pattern.match(v)))).sum())

    # Email
    for key in ("correo", "email"):
        if key in cols:
            col = cols[key]
            bad = invalid_count(col, EMAIL_RE)
            if bad:
                out.append(
                    QualityFinding(
                        table=table,
                        field=col,
                        problem=f"{bad} correos con formato inválido",
                        quality_dimension="validez",
                        severity="media",
                        suggested_rule="Validar formato de email (regex)",
                        affected_count=bad,
                    )
                )
    # DNI = 8 dígitos
    if "dni" in cols:
        col = cols["dni"]
        bad = invalid_count(col, DNI_RE)
        if bad:
            out.append(
                QualityFinding(
                    table=table,
                    field=col,
                    problem=f"{bad} DNI que no tienen 8 dígitos numéricos",
                    quality_dimension="validez",
                    severity="alta",
                    suggested_rule="DNI debe tener 8 dígitos numéricos",
                    affected_count=bad,
                )
            )
    # RUC = 11 dígitos
    if "ruc" in cols:
        col = cols["ruc"]
        bad = invalid_count(col, RUC_RE)
        if bad:
            out.append(
                QualityFinding(
                    table=table,
                    field=col,
                    problem=f"{bad} RUC que no tienen 11 dígitos numéricos",
                    quality_dimension="validez",
                    severity="alta",
                    suggested_rule="RUC debe tener 11 dígitos numéricos",
                    affected_count=bad,
                )
            )
    # Precios / montos negativos
    for col in df.columns:
        n = col.lower()
        if any(k in n for k in ("precio", "total", "monto")) and pd.api.types.is_numeric_dtype(
            df[col]
        ):
            bad = int((pd.to_numeric(df[col], errors="coerce") < 0).sum())
            if bad:
                out.append(
                    QualityFinding(
                        table=table,
                        field=col,
                        problem=f"{bad} valores negativos",
                        quality_dimension="validez",
                        severity="alta",
                        suggested_rule=f"{col} no puede ser negativo",
                        affected_count=bad,
                    )
                )
    # Cantidad cero
    if "cantidad" in cols:
        col = cols["cantidad"]
        bad = int((pd.to_numeric(df[col], errors="coerce") == 0).sum())
        if bad:
            out.append(
                QualityFinding(
                    table=table,
                    field=col,
                    problem=f"{bad} registros con cantidad cero",
                    quality_dimension="validez",
                    severity="media",
                    suggested_rule="cantidad debe ser mayor a 0",
                    affected_count=bad,
                )
            )
    # Fechas futuras
    today = pd.Timestamp(datetime.now().date())
    for col in df.columns:
        if "fecha" in col.lower():
            parsed = pd.to_datetime(df[col], errors="coerce")
            bad = int((parsed > today).sum())
            if bad:
                out.append(
                    QualityFinding(
                        table=table,
                        field=col,
                        problem=f"{bad} fechas en el futuro",
                        quality_dimension="validez",
                        severity="media",
                        suggested_rule=f"{col} no puede ser una fecha futura",
                        affected_count=bad,
                    )
                )
    return out


def _check_consistency(table: str, df: pd.DataFrame) -> list[QualityFinding]:
    """Detecta inconsistencias de conformidad: mismas categorías escritas de formas distintas."""
    out = []
    for col in df.columns:
        n = col.lower()
        if n not in {
            "pais",
            "moneda",
            "categoria",
            "estado",
            "segmento",
            "canal",
            "estado_cliente",
            "estado_producto",
        }:
            continue
        series = df[col][~_empty_mask(df[col])].astype(str)
        if series.empty:
            continue
        if n == "pais":
            groups: dict[str, set[str]] = {}
            for raw in series.unique():
                groups.setdefault(normalize_country(raw), set()).add(raw)
            inconsistent = {k: v for k, v in groups.items() if len(v) > 1}
            if inconsistent:
                ejemplos = "; ".join("/".join(sorted(v)) for v in inconsistent.values())
                out.append(
                    QualityFinding(
                        table=table,
                        field=col,
                        problem=f"País escrito de formas inconsistentes ({ejemplos})",
                        quality_dimension="conformidad",
                        severity="media",
                        suggested_rule="Normalizar país a un catálogo estándar",
                        affected_count=sum(len(v) for v in inconsistent.values()),
                    )
                )
        else:
            norm_groups: dict[str, set[str]] = {}
            for raw in series.unique():
                norm_groups.setdefault(normalize_text(raw), set()).add(raw)
            inconsistent = {k: v for k, v in norm_groups.items() if len(v) > 1}
            if inconsistent:
                ejemplos = "; ".join("/".join(sorted(v)) for v in list(inconsistent.values())[:3])
                out.append(
                    QualityFinding(
                        table=table,
                        field=col,
                        problem=f"Valores con formato inconsistente ({ejemplos})",
                        quality_dimension="consistencia",
                        severity="baja",
                        suggested_rule=f"Estandarizar valores de {col}",
                        affected_count=len(inconsistent),
                    )
                )
    return out


def _check_total_calculation(
    table: str, df: pd.DataFrame, cols: dict[str, str]
) -> list[QualityFinding]:
    if not {"cantidad", "precio_unitario", "total"}.issubset(cols):
        return []
    cant = pd.to_numeric(df[cols["cantidad"]], errors="coerce")
    pu = pd.to_numeric(df[cols["precio_unitario"]], errors="coerce")
    total = pd.to_numeric(df[cols["total"]], errors="coerce")
    expected = cant * pu
    mismatch = (expected - total).abs() > 0.01
    bad = int((mismatch & expected.notna() & total.notna()).sum())
    if bad:
        return [
            QualityFinding(
                table=table,
                field="total",
                problem=f"{bad} totales mal calculados (cantidad x precio_unitario != total)",
                quality_dimension="exactitud",
                severity="alta",
                suggested_rule="total = cantidad * precio_unitario",
                affected_count=bad,
            )
        ]
    return []


def _check_referential_integrity(
    table: str, df: pd.DataFrame, related: dict[str, pd.DataFrame]
) -> list[QualityFinding]:
    out = []
    cols = {c.lower(): c for c in df.columns}
    for fk, (parent_table, parent_col) in FK_RELATIONS.items():
        if fk not in cols or parent_table not in related:
            continue
        if parent_table == table:  # no autoreferencia para esta verificación
            continue
        parent_df = related[parent_table]
        parent_cols = {c.lower(): c for c in parent_df.columns}
        if parent_col not in parent_cols:
            continue
        child = df[cols[fk]][~_empty_mask(df[cols[fk]])].astype(str).str.strip()
        valid_keys = set(parent_df[parent_cols[parent_col]].dropna().astype(str).str.strip())
        orphans = int((~child.isin(valid_keys)).sum())
        if orphans:
            out.append(
                QualityFinding(
                    table=table,
                    field=cols[fk],
                    problem=f"{orphans} registros con {fk} inexistente en {parent_table}",
                    quality_dimension="integridad referencial",
                    severity="alta",
                    suggested_rule=f"Validar que {fk} exista en {parent_table}",
                    affected_count=orphans,
                )
            )
    return out


def _check_classification(table: str, df: pd.DataFrame) -> list[QualityFinding]:
    """Marca campos sensibles que aún no tienen clasificación en un catálogo (riesgo §24)."""
    sensitive = [c for c in df.columns if any(h in c.lower() for h in SENSITIVE_HINTS)]
    if not sensitive:
        return []
    return [
        QualityFinding(
            table=table,
            field=", ".join(sensitive),
            problem="Campos con posibles datos personales sin clasificación formal en el catálogo",
            quality_dimension="clasificacion",
            severity="alta",
            suggested_rule="Clasificar como dato personal/sensible y asignar Data Owner",
            affected_count=len(sensitive),
        )
    ]


# --------------------------------------------------------------------------- scoring


def _score(findings: list[QualityFinding]) -> tuple[int, str]:
    by_dim: dict[str, int] = {}
    for f in findings:
        dim = f.quality_dimension
        if dim == "completitud":
            key = "completitud_critico" if f.severity == "alta" else "completitud"
            penalty = PENALTY[key]
            cap_dim = "completitud"
        else:
            penalty = PENALTY.get(dim, 8)
            cap_dim = dim
        by_dim[cap_dim] = by_dim.get(cap_dim, 0) + penalty

    total = 0
    for dim, value in by_dim.items():
        total += min(value, DIMENSION_CAP.get(dim, value))

    score = max(0, 100 - total)
    if score >= 80:
        risk = "bajo"
    elif score >= 65:
        risk = "medio"
    else:
        risk = "alto"
    return score, risk


def _main_issues(findings: list[QualityFinding], limit: int = 5) -> list[str]:
    order = {"alta": 0, "media": 1, "baja": 2}
    ranked = sorted(findings, key=lambda f: order.get(f.severity, 3))
    return [f"{f.field}: {f.problem}" for f in ranked[:limit]]
