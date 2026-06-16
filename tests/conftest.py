"""Configuración de pytest: asegura que la raíz del proyecto esté en sys.path."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture
def clientes_df() -> pd.DataFrame:
    """Dataset pequeño de clientes con errores conocidos."""
    return pd.DataFrame(
        {
            "cliente_id": ["C001", "C002", "C003", "C004", "C005"],
            "nombre": ["Juan", "Juan", "Maria", "Pedro", "Ana"],
            "apellido": ["Perez", "Perez", "Lopez", "Gomez", "Diaz"],
            "dni": ["12345678", "12345678", "999", "87654321", "11223344"],  # dup + corto
            "correo": ["juan@email.com", "juan@email.com", "bad#mail", "pedro@email.com", ""],
            "telefono": ["987654321", "", "", "912345678", "999888777"],
            "pais": ["Peru", "Perú", "PE", "Chile", "Peru"],  # inconsistente
            "segmento": ["Retail", "Retail", "", "Pyme", "Premium"],
        }
    )


@pytest.fixture
def ventas_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "venta_id": ["V001", "V002", "V003", "V004"],
            "cliente_id": ["C001", "C002", "C999", "C004"],  # C999 inexistente
            "producto_id": ["P001", "P002", "P003", "P001"],
            "fecha_venta": ["2024-01-10", "2024-02-15", "2024-03-20", "2030-01-01"],  # futura
            "cantidad": [2, 0, 1, 3],  # cantidad 0
            "precio_unitario": [100.0, 50.0, 200.0, 100.0],
            "total": [200.0, 0.0, 999.0, 300.0],  # V003 mal calculado
            "canal": ["Web", "Tienda", "", "Web"],
        }
    )


@pytest.fixture
def clientes_parent_df(clientes_df) -> dict:
    return {"clientes": clientes_df}
