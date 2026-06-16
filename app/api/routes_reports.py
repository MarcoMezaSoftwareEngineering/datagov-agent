"""Endpoints de reportes: ejecuta el pipeline completo y genera el reporte ejecutivo."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.agents import (
    mdm_agent,
    metadata_agent,
    profiler_agent,
    quality_agent,
    recommendation_agent,
    report_agent,
)
from app.api.store import store
from app.schemas.report_schema import ExecutiveReport
from app.services.mdm import detect_entity_from_table
from app.services.report_generator import save_report, to_markdown

router = APIRouter(prefix="/reports", tags=["reports"])


class GenerateRequest(BaseModel):
    tables: list[str] | None = None  # None = todas las cargadas
    save_files: bool = True


@router.post("/generate", response_model=ExecutiveReport)
def generate(req: GenerateRequest) -> ExecutiveReport:
    """Ejecuta perfilado→calidad→MDM→catálogo→recomendaciones→reporte sobre las tablas cargadas."""
    names = req.tables or store.table_names()
    if not names:
        raise HTTPException(
            status_code=400, detail="No hay tablas cargadas. Sube datasets primero."
        )

    tables = {n: store.get_table(n) for n in names if store.get_table(n) is not None}
    if not tables:
        raise HTTPException(status_code=404, detail="Ninguna de las tablas indicadas está cargada.")

    profiles = [profiler_agent.run_profiler(n, df) for n, df in tables.items()]
    quality_reports = [quality_agent.run_quality(n, df, related=tables) for n, df in tables.items()]

    mdm_results = []
    for n, df in tables.items():
        entity = detect_entity_from_table(n)
        if entity:
            mdm_results.append(mdm_agent.run_mdm(n, df, entity))

    quality_by_table = {q.table: q for q in quality_reports}
    catalog = []
    for prof in profiles:
        catalog += metadata_agent.run_metadata(prof, quality_by_table.get(prof.table))

    recommendations = recommendation_agent.run_recommendations(quality_reports, mdm_results)

    report = report_agent.build_report(
        profiles=profiles,
        quality_reports=quality_reports,
        mdm_results=mdm_results,
        catalog=catalog,
        recommendations=recommendations,
    )
    store.last_report = report
    if req.save_files:
        save_report(report)
    return report


@router.get("/latest", response_model=ExecutiveReport)
def latest() -> ExecutiveReport:
    if store.last_report is None:
        raise HTTPException(status_code=404, detail="Aún no se ha generado ningún reporte.")
    return store.last_report


@router.get("/latest/markdown")
def latest_markdown() -> dict:
    if store.last_report is None:
        raise HTTPException(status_code=404, detail="Aún no se ha generado ningún reporte.")
    return {"markdown": to_markdown(store.last_report)}
