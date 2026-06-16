"""Endpoints de datos: carga, perfilado, calidad y MDM."""

from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from app.agents import mdm_agent, profiler_agent, quality_agent
from app.api.store import store
from app.schemas.data_schema import FileMetadata, MdmResult, TableProfile
from app.schemas.quality_schema import QualityReport
from app.services.data_loader import load_dataframe_from_bytes
from app.services.mdm import detect_entity_from_table

router = APIRouter(prefix="/data", tags=["data"])


class TableRequest(BaseModel):
    table: str


@router.post("/upload", response_model=FileMetadata)
async def upload(file: UploadFile = File(...)) -> FileMetadata:
    """Carga un CSV/Excel y lo guarda en la sesión."""
    content = await file.read()
    try:
        loaded = load_dataframe_from_bytes(content, file.filename or "uploaded.csv")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"No se pudo cargar el archivo: {exc}") from exc
    store.add_table(loaded.name, loaded.df)
    return loaded.metadata


@router.get("/tables")
def list_tables() -> dict:
    """Lista las tablas cargadas en la sesión."""
    return {
        "tables": [
            {"name": name, "rows": int(df.shape[0]), "columns": int(df.shape[1])}
            for name, df in store.tables.items()
        ]
    }


@router.post("/profile", response_model=TableProfile)
def profile(req: TableRequest) -> TableProfile:
    df = _require_table(req.table)
    return profiler_agent.run_profiler(req.table, df)


@router.post("/quality", response_model=QualityReport)
def quality(req: TableRequest) -> QualityReport:
    df = _require_table(req.table)
    return quality_agent.run_quality(req.table, df, related=store.tables)


@router.post("/mdm", response_model=MdmResult)
def mdm(req: TableRequest) -> MdmResult:
    df = _require_table(req.table)
    entity = detect_entity_from_table(req.table)
    return mdm_agent.run_mdm(req.table, df, entity)


def _require_table(name: str):
    df = store.get_table(name)
    if df is None:
        raise HTTPException(
            status_code=404,
            detail=f"Tabla '{name}' no cargada. Tablas disponibles: {store.table_names()}",
        )
    return df
