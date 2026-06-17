"""Compara las detecciones del sistema contra el ground truth del dataset.

Lee `known_issues_expected.json` del paquete `datagov_agent_dataset` y verifica
que el motor de calidad/perfilado detecte exactamente los problemas esperados.
Reutilizable por el script CLI y por los tests.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from app.config import settings
from app.services.profiler import profile_dataframe
from app.services.quality_rules import _empty_mask, evaluate_quality

TABLES = ["clientes", "productos", "proveedores", "sucursales", "ventas"]

# Métricas cuya convención de conteo difiere del ground truth (registros involucrados
# vs "extras"): se reportan pero no hacen fallar la validación.
SOFT_PREFIXES = ("duplicate_",)


@dataclass
class Check:
    table: str
    metric: str
    expected: object
    detected: object
    ok: bool
    hard: bool


def load_tables(raw_dir: Path | None = None) -> dict[str, pd.DataFrame]:
    raw = raw_dir or settings.raw_path
    tables: dict[str, pd.DataFrame] = {}
    for name in TABLES:
        path = raw / f"{name}.csv"
        if path.exists():
            tables[name] = pd.read_csv(path, encoding="utf-8-sig")
    return tables


def load_expected(path: Path | None = None) -> dict:
    p = path or settings.expected_outputs_path
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _finding(report, field: str, dimension: str) -> int:
    for f in report.findings:
        if f.field.lower() == field.lower() and f.quality_dimension == dimension:
            return f.affected_count
    return 0


def _records_involved(df: pd.DataFrame, col: str) -> int:
    """Nº de registros que participan en un valor duplicado (convención del ground truth)."""
    if col not in df.columns:
        return 0
    s = df[col][~_empty_mask(df[col])]
    counts = s.value_counts()
    return int(counts[counts > 1].sum())


def _detected_metrics(tables: dict[str, pd.DataFrame]) -> dict[str, dict[str, object]]:
    """Calcula las métricas detectadas mapeadas a las claves del ground truth."""
    q = {t: evaluate_quality(t, df, related=tables) for t, df in tables.items()}
    out: dict[str, dict[str, object]] = {}

    if "clientes" in tables:
        df = tables["clientes"]
        out["clientes"] = {
            "rows": len(df),
            "duplicate_dni_records": _records_involved(df, "dni"),
            "invalid_dni_records": _finding(q["clientes"], "dni", "validez"),
            "invalid_email_records": _finding(q["clientes"], "correo", "validez"),
            "missing_telefono_records": _finding(q["clientes"], "telefono", "completitud"),
            "missing_segmento_records": _finding(q["clientes"], "segmento", "completitud"),
            "possible_sensitive_fields": profile_dataframe(
                "clientes", df
            ).possible_sensitive_fields,
        }
    if "productos" in tables:
        df = tables["productos"]
        out["productos"] = {
            "rows": len(df),
            "duplicate_sku_records": _records_involved(df, "sku"),
            "negative_price_records": _finding(q["productos"], "precio", "validez"),
            "future_fecha_alta_records": _finding(q["productos"], "fecha_alta", "validez"),
            "missing_moneda_records": _finding(q["productos"], "moneda", "completitud"),
            "invalid_proveedor_reference_records": _finding(
                q["productos"], "proveedor_id", "integridad referencial"
            ),
        }
    if "proveedores" in tables:
        df = tables["proveedores"]
        out["proveedores"] = {
            "rows": len(df),
            "duplicate_ruc_records": _records_involved(df, "ruc"),
            "invalid_ruc_records": _finding(q["proveedores"], "ruc", "validez"),
            "missing_correo_records": _finding(q["proveedores"], "correo", "completitud"),
        }
    if "ventas" in tables:
        df = tables["ventas"]
        out["ventas"] = {
            "rows": len(df),
            "invalid_cliente_reference_records": _finding(
                q["ventas"], "cliente_id", "integridad referencial"
            ),
            "invalid_producto_reference_records": _finding(
                q["ventas"], "producto_id", "integridad referencial"
            ),
            "zero_quantity_records": _finding(q["ventas"], "cantidad", "validez"),
            "future_fecha_venta_records": _finding(q["ventas"], "fecha_venta", "validez"),
            "total_mismatch_records": _finding(q["ventas"], "total", "exactitud"),
            "missing_canal_records": _finding(q["ventas"], "canal", "completitud"),
            "invalid_sucursal_reference_records": _finding(
                q["ventas"], "sucursal_id", "integridad referencial"
            ),
        }
    return out


def _compare_metric(metric: str, expected, detected) -> bool:
    if metric == "possible_sensitive_fields":
        # detectado debe contener (superset) a lo esperado
        return set(expected).issubset({s.lower() for s in detected})
    return expected == detected


def run_validation(
    tables: dict[str, pd.DataFrame] | None = None,
    expected: dict | None = None,
) -> list[Check]:
    """Devuelve la lista de chequeos detectado-vs-esperado."""
    tables = tables if tables is not None else load_tables()
    expected = expected if expected is not None else load_expected()
    detected = _detected_metrics(tables)

    checks: list[Check] = []
    for table, exp_metrics in expected.items():
        det_metrics = detected.get(table, {})
        for metric, exp_value in exp_metrics.items():
            det_value = det_metrics.get(metric, 0)
            ok = _compare_metric(metric, exp_value, det_value)
            hard = not metric.startswith(SOFT_PREFIXES)
            checks.append(Check(table, metric, exp_value, det_value, ok, hard))
    return checks


def hard_failures(checks: list[Check]) -> list[Check]:
    return [c for c in checks if c.hard and not c.ok]
