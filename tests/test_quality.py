"""Pruebas del motor de reglas de calidad."""

from __future__ import annotations

from app.services.quality_rules import evaluate_quality


def _dims(report):
    return {f.quality_dimension for f in report.findings}


def test_quality_detects_duplicate_identifier(clientes_df):
    report = evaluate_quality("clientes", clientes_df)
    assert "unicidad" in _dims(report)
    dni_findings = [
        f for f in report.findings if f.field == "dni" and f.quality_dimension == "unicidad"
    ]
    assert dni_findings and dni_findings[0].affected_count >= 1


def test_quality_detects_invalid_dni_and_email(clientes_df):
    report = evaluate_quality("clientes", clientes_df)
    assert "validez" in _dims(report)
    fields = {f.field for f in report.findings if f.quality_dimension == "validez"}
    assert "dni" in fields
    assert "correo" in fields


def test_quality_detects_country_inconsistency(clientes_df):
    report = evaluate_quality("clientes", clientes_df)
    assert "conformidad" in _dims(report)


def test_quality_score_and_risk(clientes_df):
    report = evaluate_quality("clientes", clientes_df)
    assert 0 <= report.quality_score <= 100
    assert report.risk_level in {"alto", "medio", "bajo"}
    # Con tantos errores, el score no debe ser perfecto
    assert report.quality_score < 100


def test_quality_referential_integrity(ventas_df, clientes_parent_df):
    report = evaluate_quality("ventas", ventas_df, related=clientes_parent_df)
    assert "integridad referencial" in _dims(report)
    fk = [f for f in report.findings if f.quality_dimension == "integridad referencial"]
    assert fk and fk[0].affected_count >= 1  # C999 huérfano


def test_quality_total_miscalculation(ventas_df, clientes_parent_df):
    report = evaluate_quality("ventas", ventas_df, related=clientes_parent_df)
    assert any(f.field == "total" and "exactitud" == f.quality_dimension for f in report.findings)


def test_quality_future_date_and_zero_quantity(ventas_df):
    report = evaluate_quality("ventas", ventas_df)
    problems = " ".join(f.problem for f in report.findings)
    assert "futuro" in problems
    assert "cantidad cero" in problems
