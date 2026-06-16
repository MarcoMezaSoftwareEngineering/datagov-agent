"""Data Profiler Agent: envuelve el servicio de perfilado (Módulo 2)."""

from __future__ import annotations

import pandas as pd

from app.schemas.data_schema import TableProfile
from app.services.profiler import profile_dataframe


def run_profiler(table_name: str, df: pd.DataFrame) -> TableProfile:
    """Genera el perfil técnico de una tabla."""
    return profile_dataframe(table_name, df)
