"""Almacén de sesión a nivel de proceso para datasets, reportes y vector store.

Mantiene en memoria los DataFrames subidos para que distintos endpoints
(perfilado, calidad, MDM, reporte) operen sobre los mismos datos.
"""

from __future__ import annotations

import threading

import pandas as pd

from app.schemas.report_schema import ExecutiveReport
from app.services.vector_store import BaseVectorStore


class SessionStore:
    """Estado compartido en memoria (no es una BD; suficiente para la demo local)."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.tables: dict[str, pd.DataFrame] = {}
        self.last_report: ExecutiveReport | None = None
        self._vector_store: BaseVectorStore | None = None

    def add_table(self, name: str, df: pd.DataFrame) -> None:
        with self._lock:
            self.tables[name] = df

    def get_table(self, name: str) -> pd.DataFrame | None:
        return self.tables.get(name)

    def table_names(self) -> list[str]:
        return list(self.tables.keys())

    def clear_tables(self) -> None:
        with self._lock:
            self.tables.clear()

    def get_vector_store(self) -> BaseVectorStore:
        """Devuelve el vector store (Milvus). Lanza error claro si no está disponible."""
        if self._vector_store is None:
            from app.services.vector_store import get_vector_store

            self._vector_store = get_vector_store(backend="milvus")
        return self._vector_store


store = SessionStore()
