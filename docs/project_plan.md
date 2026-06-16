# Plan de Proyecto (resumen)

Este documento resume el plan completo. El plan original detallado está en
[`Plan de Proyecto DataGov Agent.txt`](../Plan%20de%20Proyecto%20DataGov%20Agent.txt).

## Objetivo
Sistema local de IA generativa y agéntica para gobierno, calidad, MDM y catalogación de datos,
ejecutable en una PC (RTX 3080 10GB) sin servicios de pago.

## Módulos (agentes)
1. **Data Ingestion** — carga CSV/Excel/PDF/TXT/MD.
2. **Data Profiling Agent** — perfil técnico (nulos, duplicados, tipos, PII).
3. **Data Quality Agent** — 8 dimensiones, hallazgos, reglas y score.
4. **MDM Agent** — duplicados y golden record.
5. **Metadata & Catalog Agent** — glosario, clasificación, owner/steward.
6. **RAG Policy Agent** — preguntas sobre documentos de gobierno (Milvus).
7. **Recommendation Agent** — recomendaciones ejecutivas.
8. **Report Agent** — reporte ejecutivo final.

## Orquestación (LangGraph)
`START → load_input → classify_input →` ramas **dataset / document / question**. La rama dataset
ejecuta perfilado → calidad → MDM → catálogo → recomendaciones → reporte.

## MVP (cumplido)
Carga CSV · nulos/duplicados · formatos inválidos · campos sensibles · reglas de calidad ·
ingesta de documentos · embeddings en Milvus · preguntas RAG · ≥3 agentes con LangGraph ·
reporte ejecutivo · UI Streamlit · README completo.

## Cronograma (6 semanas)
1. Base + datos sintéticos + perfilado.
2. Calidad + MDM + tests.
3. RAG con Milvus.
4. LangGraph y agentes.
5. API + interfaz.
6. Reportes, documentación y presentación.

## Entregables
Código en GitHub, README, diagrama de arquitectura, dataset sintético, documentos de gobierno,
API, UI, RAG, agentes, reporte ejecutivo, guion de demo y roadmap.
