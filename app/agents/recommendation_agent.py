"""Recommendation Agent: recomendaciones ejecutivas accionables (Módulo 7)."""

from __future__ import annotations

from app.agents.prompts import RECOMMENDATION_SYSTEM
from app.schemas.data_schema import MdmResult
from app.schemas.quality_schema import QualityReport, Recommendation
from app.services.llm import get_llm
from app.utils.text_cleaning import extract_json


def run_recommendations(
    quality_reports: list[QualityReport],
    mdm_results: list[MdmResult] | None = None,
) -> list[Recommendation]:
    """Genera recomendaciones a partir de hallazgos de calidad y MDM."""
    mdm_results = mdm_results or []
    llm = get_llm()
    if llm.available:
        recs = _llm_recommendations(llm, quality_reports, mdm_results)
        if recs:
            return recs
    return _fallback_recommendations(quality_reports, mdm_results)


def _llm_recommendations(llm, quality_reports, mdm_results) -> list[Recommendation]:
    findings_txt = []
    for qr in quality_reports:
        for f in qr.findings:
            findings_txt.append(
                f"{qr.table}.{f.field}: {f.problem} [{f.quality_dimension}, {f.severity}]"
            )
    for mr in mdm_results:
        if mr.duplicates_detected:
            findings_txt.append(f"{mr.entity}: {mr.duplicates_detected} posibles duplicados (MDM)")
    user = "Hallazgos detectados:\n" + "\n".join(findings_txt[:60])
    raw = llm.complete(RECOMMENDATION_SYSTEM, user, json_mode=True)
    data = extract_json(raw) if raw else None
    if not isinstance(data, dict):
        return []
    out = []
    for item in data.get("recommendations", []):
        out.append(
            Recommendation(
                priority=str(item.get("priority", "media")),
                title=str(item.get("title", "")),
                risk=str(item.get("risk", "")),
                suggested_action=str(item.get("suggested_action", "")),
                responsible=str(item.get("responsible", "")),
                expected_impact=str(item.get("expected_impact", "")),
                estimated_effort=str(item.get("estimated_effort", "")),
            )
        )
    return out


def _fallback_recommendations(
    quality_reports: list[QualityReport], mdm_results: list[MdmResult]
) -> list[Recommendation]:
    recs: list[Recommendation] = []
    # Tabla con peor score = mayor prioridad
    for qr in sorted(quality_reports, key=lambda r: r.quality_score):
        high = [f for f in qr.findings if f.severity == "alta"]
        if not high:
            continue
        dims = sorted({f.quality_dimension for f in high})
        recs.append(
            Recommendation(
                priority="alta" if qr.quality_score < 65 else "media",
                title=f"Mejorar calidad de la tabla {qr.table}",
                risk=f"Score {qr.quality_score}/100 (riesgo {qr.risk_level}); dimensiones afectadas: {', '.join(dims)}.",
                suggested_action="Implementar reglas de validación: "
                + "; ".join(sorted({f.suggested_rule for f in high})[:4]),
                responsible="Data Owner de " + qr.table,
                expected_impact="Reducción de errores y mayor confianza en los reportes.",
                estimated_effort="medio",
            )
        )

    for mr in mdm_results:
        if mr.duplicates_detected:
            recs.append(
                Recommendation(
                    priority="alta",
                    title=f"Consolidar duplicados de {mr.entity}",
                    risk=f"{mr.duplicates_detected} posibles duplicados degradan la visión única de {mr.entity}.",
                    suggested_action="Aplicar golden record sugerido y reglas de matching (clave exacta + similaridad).",
                    responsible="Data Steward de " + mr.entity,
                    expected_impact="Visión única de la entidad maestra y menor duplicidad.",
                    estimated_effort="medio",
                )
            )

    if not recs:
        recs.append(
            Recommendation(
                priority="baja",
                title="Mantener monitoreo de calidad",
                risk="No se detectaron hallazgos críticos.",
                suggested_action="Programar perfilamiento periódico y definir umbrales de calidad.",
                responsible="Gobierno de Datos",
                expected_impact="Sostenibilidad de la calidad de datos.",
                estimated_effort="bajo",
            )
        )
    return recs
