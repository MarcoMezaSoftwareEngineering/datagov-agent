"""Generación del reporte ejecutivo en Markdown / HTML / JSON / Excel / PDF (Módulo 8)."""

from __future__ import annotations

from pathlib import Path

from app.config import settings
from app.schemas.report_schema import ExecutiveReport
from app.utils.logging import get_logger

logger = get_logger(__name__)


def to_markdown(report: ExecutiveReport) -> str:
    """Renderiza el reporte ejecutivo a Markdown (§8 estructura)."""
    lines: list[str] = []
    a = lines.append

    a(f"# {report.title}")
    a("")
    a(f"_Generado: {report.generated_at:%Y-%m-%d %H:%M}_")
    a("")
    a(f"**Score global de calidad:** {report.overall_score}/100")
    a("")

    a("## 1. Resumen ejecutivo")
    a(report.executive_summary or "_Sin resumen disponible._")
    a("")

    a("## 2. Datasets analizados")
    for ds in report.datasets:
        a(f"- {ds}")
    if not report.datasets:
        a("_Sin datasets._")
    a("")

    a("## 3. Principales hallazgos")
    for qr in report.quality_reports:
        a(f"### {qr.table}")
        if not qr.findings:
            a("- Sin hallazgos relevantes.")
        for f in qr.findings:
            a(
                f"- **[{f.severity.upper()}] {f.field}** — {f.problem} "
                f"(_{f.quality_dimension}_) → {f.suggested_rule}"
            )
        a("")

    a("## 4. Score de calidad por tabla")
    a("")
    a("| Tabla | Score | Riesgo | Filas |")
    a("| ----- | ----- | ------ | ----- |")
    for qr in report.quality_reports:
        a(f"| {qr.table} | {qr.quality_score} | {qr.risk_level} | {qr.rows} |")
    a("")

    a("## 5. Campos críticos / sensibles")
    for prof in report.profiles:
        if prof.possible_sensitive_fields:
            a(f"- **{prof.table}**: {', '.join(prof.possible_sensitive_fields)}")
    a("")

    a("## 6. Reglas de calidad sugeridas")
    seen = set()
    for qr in report.quality_reports:
        for f in qr.findings:
            rule = f"{qr.table}.{f.field}: {f.suggested_rule}"
            if f.suggested_rule and rule not in seen:
                seen.add(rule)
                a(f"- {rule}")
    a("")

    a("## 7. Hallazgos MDM (posibles duplicados)")
    for mr in report.mdm_results:
        a(
            f"### {mr.entity} — {mr.duplicates_detected} duplicados en {len(mr.duplicate_groups)} grupos"
        )
        for g in mr.duplicate_groups[:10]:
            ids = ", ".join(g.member_ids)
            a(f"- [{g.match_type}, conf={g.confidence}] {ids}")
        a("")

    a("## 8. Riesgos")
    for r in report.risks:
        a(f"- {r}")
    if not report.risks:
        a("_Sin riesgos detectados._")
    a("")

    a("## 9. Recomendaciones")
    for rec in report.recommendations:
        a(f"- **[{rec.priority.upper()}] {rec.title}**")
        a(f"  - Riesgo: {rec.risk}")
        a(f"  - Acción: {rec.suggested_action}")
        a(f"  - Responsable: {rec.responsible}")
        a(f"  - Impacto: {rec.expected_impact} | Esfuerzo: {rec.estimated_effort}")
    if not report.recommendations:
        a("_Sin recomendaciones._")
    a("")

    a("## 10. Roadmap de mejora")
    for i, step in enumerate(report.roadmap, 1):
        a(f"{i}. {step}")
    a("")

    if report.kpis:
        a("## KPIs")
        a("")
        a("| KPI | Valor |")
        a("| --- | ----- |")
        for key, value in report.kpis.items():
            a(f"| {key} | {value} |")
        a("")

    return "\n".join(lines)


def to_html(report: ExecutiveReport) -> str:
    """Convierte el reporte a HTML (a partir del Markdown)."""
    import markdown as md

    body = md.markdown(to_markdown(report), extensions=["tables", "fenced_code"])
    return _HTML_TEMPLATE.format(title=report.title, body=body)


def to_json(report: ExecutiveReport) -> str:
    return report.model_dump_json(indent=2)


def save_report(report: ExecutiveReport, basename: str = "executive_report") -> dict[str, str]:
    """Guarda el reporte en md/html/json dentro de REPORTS_DIR. Devuelve las rutas."""
    settings.reports_path.mkdir(parents=True, exist_ok=True)
    paths: dict[str, str] = {}

    md_path = settings.reports_path / f"{basename}.md"
    md_path.write_text(to_markdown(report), encoding="utf-8")
    paths["markdown"] = str(md_path)

    html_path = settings.reports_path / f"{basename}.html"
    html_path.write_text(to_html(report), encoding="utf-8")
    paths["html"] = str(html_path)

    json_path = settings.reports_path / f"{basename}.json"
    json_path.write_text(to_json(report), encoding="utf-8")
    paths["json"] = str(json_path)

    pdf_path = settings.reports_path / f"{basename}.pdf"
    if _save_pdf(report, pdf_path):
        paths["pdf"] = str(pdf_path)

    logger.info("Reporte guardado en: %s", ", ".join(paths.values()))
    return paths


def _save_pdf(report: ExecutiveReport, path: Path) -> bool:
    """Genera PDF con xhtml2pdf (puro Python, Windows-friendly). Devuelve True si tuvo éxito."""
    try:
        from xhtml2pdf import pisa

        html = to_html(report)
        with open(path, "wb") as fh:
            result = pisa.CreatePDF(html, dest=fh)
        return not result.err
    except Exception as exc:  # pragma: no cover - dependiente de entorno
        logger.warning("No se pudo generar PDF (%s)", exc)
        return False


_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>
  body {{ font-family: Arial, Helvetica, sans-serif; margin: 40px; color: #1a1a1a; }}
  h1 {{ color: #0b3d91; }}
  h2 {{ color: #0b3d91; border-bottom: 2px solid #e0e0e0; padding-bottom: 4px; }}
  table {{ border-collapse: collapse; width: 100%; margin: 12px 0; }}
  th, td {{ border: 1px solid #ccc; padding: 6px 10px; text-align: left; }}
  th {{ background: #f0f4ff; }}
  code {{ background: #f5f5f5; padding: 1px 4px; }}
</style>
</head>
<body>
{body}
</body>
</html>
"""
