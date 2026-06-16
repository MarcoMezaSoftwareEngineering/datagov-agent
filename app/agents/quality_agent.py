"""Data Quality Agent: hallazgos deterministas + narrativa LLM (Módulo 3)."""

from __future__ import annotations

import pandas as pd

from app.agents.prompts import QUALITY_SYSTEM
from app.schemas.quality_schema import QualityReport
from app.services.llm import get_llm
from app.services.quality_rules import evaluate_quality


def run_quality(
    table: str,
    df: pd.DataFrame,
    related: dict[str, pd.DataFrame] | None = None,
) -> QualityReport:
    """Evalúa la calidad y añade una narrativa ejecutiva (si hay LLM)."""
    report = evaluate_quality(table, df, related)
    report.narrative = _narrative(report)
    return report


def _narrative(report: QualityReport) -> str:
    llm = get_llm()
    if llm.available:
        findings_txt = "\n".join(
            f"- {f.field}: {f.problem} [{f.quality_dimension}, {f.severity}]"
            for f in report.findings
        )
        user = (
            f"Tabla: {report.table} ({report.rows} filas)\n"
            f"Score de calidad: {report.quality_score}/100 (riesgo {report.risk_level})\n"
            f"Hallazgos:\n{findings_txt or 'sin hallazgos'}"
        )
        out = llm.complete(QUALITY_SYSTEM, user)
        if out:
            return out.strip()
    return _fallback_narrative(report)


def _fallback_narrative(report: QualityReport) -> str:
    if not report.findings:
        return (
            f"La tabla {report.table} no presenta hallazgos relevantes de calidad "
            f"(score {report.quality_score}/100, riesgo {report.risk_level})."
        )
    top = report.main_issues[:3]
    return (
        f"La tabla {report.table} obtiene un score de calidad de {report.quality_score}/100 "
        f"(riesgo {report.risk_level}). Se detectaron {len(report.findings)} hallazgos; "
        f"los más relevantes: {'; '.join(top)}. Se recomienda priorizar reglas de validación "
        f"y clasificación de campos sensibles."
    )
