"""MDM Agent: detección de duplicados y golden record (Módulo 4)."""

from __future__ import annotations

import pandas as pd

from app.schemas.data_schema import MdmResult
from app.services.mdm import detect_duplicates, detect_entity_from_table


def run_mdm(table_name: str, df: pd.DataFrame, entity: str | None = None) -> MdmResult:
    """Ejecuta MDM para una tabla, infiriendo la entidad por el nombre si no se indica."""
    entity = entity or detect_entity_from_table(table_name) or table_name.rstrip("s")
    return detect_duplicates(entity, df)
