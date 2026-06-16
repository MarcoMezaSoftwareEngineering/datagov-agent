# Prompts del sistema

Los prompts viven en [`app/agents/prompts.py`](../app/agents/prompts.py). Resumen:

## Supervisor Agent
Decide la ruta (`dataset_analysis`, `document_ingestion`, `rag_question`, `mdm_analysis`,
`report_generation`, `recommendation_request`) y responde **solo JSON**:
```json
{ "route": "...", "reason": "..." }
```
Antes de invocar al LLM, el supervisor aplica heurísticas deterministas (extensión de archivo,
palabras clave en la pregunta) para ser robusto sin LLM.

## Data Quality Agent
Especialista en calidad de datos. Recibe el perfil técnico y los hallazgos deterministas y redacta
una narrativa breve y profesional. **No inventa datos**; usa solo las métricas entregadas.

## RAG Policy Agent
Responde **únicamente** con base en el contexto recuperado. Si no hay sustento, responde:
> "No se encontró sustento suficiente en los documentos cargados."

Devuelve JSON con `answer`, `rationale`, `confidence`. La respuesta incluye las **fuentes** internas.

## Recommendation Agent
Consultor junior de gobierno de datos. Genera recomendaciones con prioridad, riesgo, acción,
responsable, impacto esperado y esfuerzo estimado. **No inventa métricas.**

## Metadata Agent
Genera definiciones de negocio y clasificación de campos. Usa las reglas de calidad provistas.

## Report Agent
Redacta el resumen ejecutivo (5-8 frases) para la alta dirección con estado general, riesgos y
prioridades.

## Principio común
Todos los agentes LLM tienen un **fallback determinista**: si Ollama no está disponible, producen
una salida estructurada a partir de los hallazgos, de modo que el sistema siempre responde.
