"""Pruebas del agente MDM (duplicados y golden record)."""

from __future__ import annotations

import pandas as pd

from app.services.mdm import detect_duplicates, detect_entity_from_table


def test_detect_entity_from_table():
    assert detect_entity_from_table("clientes") == "cliente"
    assert detect_entity_from_table("productos") == "producto"
    assert detect_entity_from_table("proveedores") == "proveedor"
    assert detect_entity_from_table("ventas") is None


def test_mdm_exact_key_duplicates(clientes_df):
    result = detect_duplicates("cliente", clientes_df)
    assert result.entity == "cliente"
    # C001 y C002 comparten DNI 12345678
    assert result.duplicates_detected >= 1
    groups = [g for g in result.duplicate_groups if g.match_type == "exact_key"]
    assert groups
    assert "C001" in groups[0].member_ids and "C002" in groups[0].member_ids


def test_mdm_fuzzy_name_duplicates():
    df = pd.DataFrame(
        {
            "cliente_id": ["C010", "C011", "C012"],
            "nombre": ["Juan", "Juán", "Carlos"],
            "apellido": ["Perez", "Perez", "Ramirez"],
            "dni": ["", "", ""],
            "correo": ["juan.perez@email.com", "juan.perez@email.com", "carlos@email.com"],
        }
    )
    result = detect_duplicates("cliente", df)
    fuzzy = [g for g in result.duplicate_groups if g.match_type == "fuzzy_name"]
    assert fuzzy
    assert set(fuzzy[0].member_ids) >= {"C010", "C011"}


def test_mdm_golden_record(clientes_df):
    result = detect_duplicates("cliente", clientes_df)
    assert result.duplicate_groups
    golden = result.duplicate_groups[0].golden_record.values
    assert "cliente_id" in golden or "nombre" in golden
