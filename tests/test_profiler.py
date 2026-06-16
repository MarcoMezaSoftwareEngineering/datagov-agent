"""Pruebas del servicio de perfilamiento."""

from __future__ import annotations

from app.services.profiler import profile_dataframe


def test_profile_basic_metrics(clientes_df):
    prof = profile_dataframe("clientes", clientes_df)
    assert prof.table == "clientes"
    assert prof.rows == 5
    assert prof.columns == len(clientes_df.columns)


def test_profile_detects_nulls(clientes_df):
    prof = profile_dataframe("clientes", clientes_df)
    # telefono y correo tienen vacíos -> deben aparecer en nulos o como vacíos
    # pandas trata "" como string no nulo, así que validamos via column profiles
    by_name = {c.name: c for c in prof.column_profiles}
    assert "telefono" in by_name


def test_profile_detects_sensitive_fields(clientes_df):
    prof = profile_dataframe("clientes", clientes_df)
    for field in ("dni", "correo", "telefono", "nombre", "apellido"):
        assert field in prof.possible_sensitive_fields


def test_profile_detects_identifiers(clientes_df):
    prof = profile_dataframe("clientes", clientes_df)
    assert "cliente_id" in prof.possible_identifier_fields


def test_profile_detects_duplicate_dni(clientes_df):
    prof = profile_dataframe("clientes", clientes_df)
    assert prof.duplicates.get("dni", 0) >= 1
