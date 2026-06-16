"""Report Agent: ensambla el reporte ejecutivo final (Módulo 8)."""

from __future__ import annotations

from app.agents.prompts import REPORT_SYSTEM
from app.schemas.data_schema import MdmResult, TableProfile
from app.schemas.quality_schema import CatalogEntry, QualityReport, Recommendation
from app.schemas.report_schema import ExecutiveReport
from app.services.llm import get_llm

DEFAULT_ROADMAP = [
    "Formalizar el catálogo de datos y asignar Data Owners/Stewards.",
    "Implementar reglas de calidad automatizadas en la ingesta.",
    "Consolidar entidades maestras (MDM) con golden records.",
    "Establecer un tablero de score de calidad por dominio.",
    "Definir política de clasificación y controles para datos personales.",
    "Planificar la modernización del data warehouse (capa cloud simulada).",
]


def build_report(
    *,
    profiles: list[TableProfile],
    quality_reports: list[QualityReport],
    mdm_results: list[MdmResult] | None = None,
    catalog: list[CatalogEntry] | None = None,
    recommendations: list[Recommendation] | None = None,
) -> ExecutiveReport:
    """Construye el ExecutiveReport agregando los resultados de todos los agentes."""
    mdm_results = mdm_results or []
    catalog = catalog or []
    recommendations = recommendations or []

    overall = (
        round(sum(q.quality_score for q in quality_reports) / len(quality_reports))
        if quality_reports
        else 100
    )
    risks = _risks(quality_reports, mdm_results, profiles)
    kpis = _kpis(profiles, quality_reports, mdm_results, catalog)

    report = ExecutiveReport(
        datasets=[p.table for p in profiles],
        profiles=profiles,
        quality_reports=quality_reports,
        mdm_results=mdm_results,
        catalog=catalog,
        recommendations=recommendations,
        risks=risks,
        roadmap=DEFAULT_ROADMAP,
        overall_score=overall,
        kpis=kpis,
    )
    report.executive_summary = _summary(report)
    return report


def _risks(quality_reports, mdm_results, profiles) -> list[str]:
    risks = []
    for qr in quality_reports:
        if qr.risk_level == "alto":
            risks.append(f"Tabla {qr.table} con riesgo alto de calidad (score {qr.quality_score}).")
    for mr in mdm_results:
        if mr.duplicates_detected:
            risks.append(
                f"{mr.duplicates_detected} posibles duplicados en {mr.entity} (riesgo de visión única)."
            )
    for p in profiles:
        if p.possible_sensitive_fields:
            risks.append(
                f"Datos personales sin clasificación formal en {p.table}: "
                f"{', '.join(p.possible_sensitive_fields)}."
            )
    return risks


def _kpis(profiles, quality_reports, mdm_results, catalog) -> dict:
    total_findings = sum(len(q.findings) for q in quality_reports)
    total_rules = len(
        {f.suggested_rule for q in quality_reports for f in q.findings if f.suggested_rule}
    )
    total_dupes = sum(m.duplicates_detected for m in mdm_results)
    sensitive = sum(len(p.possible_sensitive_fields) for p in profiles)
    return {
        "datasets_analizados": len(profiles),
        "hallazgos_detectados": total_findings,
        "reglas_sugeridas": total_rules,
        "duplicados_detectados": total_dupes,
        "campos_sensibles": sensitive,
        "campos_catalogados": len(catalog),
        "score_promedio": (
            round(sum(q.quality_score for q in quality_reports) / len(quality_reports))
            if quality_reports
            else 100
        ),
    }


def _summary(report: ExecutiveReport) -> str:
    llm = get_llm()
    facts = (
        f"Datasets: {', '.join(report.datasets)}. "
        f"Score global: {report.overall_score}/100. "
        f"Hallazgos: {report.kpis.get('hallazgos_detectados', 0)}. "
        f"Duplicados: {report.kpis.get('duplicados_detectados', 0)}. "
        f"Campos sensibles: {report.kpis.get('campos_sensibles', 0)}. "
        f"Riesgos: {'; '.join(report.risks[:4]) or 'ninguno relevante'}."
    )
    if llm.available:
        out = llm.complete(REPORT_SYSTEM, facts)
        if out:
            return out.strip()
    return (
        f"Se analizaron {len(report.datasets)} datasets con un score global de calidad de "
        f"{report.overall_score}/100. Se detectaron {report.kpis.get('hallazgos_detectados', 0)} "
        f"hallazgos de calidad y {report.kpis.get('duplicados_detectados', 0)} posibles duplicados. "
        f"Existen {report.kpis.get('campos_sensibles', 0)} campos con datos personales que requieren "
        f"clasificación y asignación de responsables. Se recomienda priorizar las tablas con mayor "
        f"riesgo, formalizar el catálogo y aplicar reglas de calidad e iniciativas MDM."
    )
