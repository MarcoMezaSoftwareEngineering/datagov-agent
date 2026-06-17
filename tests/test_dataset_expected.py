"""Valida que las detecciones coincidan con el ground truth del paquete de datos.

Se auto-omite si el paquete `datagov_agent_dataset` no está presente, de modo que
la suite sigue corriendo en entornos sin el dataset.
"""

from __future__ import annotations

import pytest

from app.config import settings
from app.services.dataset_validation import hard_failures, run_validation

pytestmark = pytest.mark.skipif(
    not settings.expected_outputs_path.exists()
    or not (settings.raw_path / "clientes.csv").exists(),
    reason="Paquete datagov_agent_dataset no disponible",
)


@pytest.fixture(scope="module")
def checks():
    return run_validation()


def test_all_hard_checks_pass(checks):
    fails = hard_failures(checks)
    assert not fails, "Fallos: " + "; ".join(f"{c.table}.{c.metric}" for c in fails)


def test_sucursal_referential_integrity_detected(checks):
    sucursal = [c for c in checks if c.metric == "invalid_sucursal_reference_records"]
    assert sucursal and sucursal[0].ok
    assert sucursal[0].detected == sucursal[0].expected


def test_no_false_positive_fk_uniqueness():
    """ventas.cliente_id/producto_id/sucursal_id NO deben marcarse como duplicados (son FKs)."""

    from app.services.dataset_validation import load_tables
    from app.services.quality_rules import evaluate_quality

    tables = load_tables()
    rep = evaluate_quality("ventas", tables["ventas"], related=tables)
    uniqueness_fields = {f.field for f in rep.findings if f.quality_dimension == "unicidad"}
    assert "cliente_id" not in uniqueness_fields
    assert "producto_id" not in uniqueness_fields
    assert "sucursal_id" not in uniqueness_fields
