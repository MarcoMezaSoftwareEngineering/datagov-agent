# Manual de Demostración y Casos de Uso — DataGov Agent

Cómo exponer y demostrar DataGov Agent en una entrevista técnica.
Para levantar el sistema, ver primero [MANUAL_DESPLIEGUE.md](MANUAL_DESPLIEGUE.md).
Guion corto alternativo en [demo_script.md](demo_script.md).

---

## 1. El pitch (30 segundos)

> "DataGov Agent es un sistema **local y agéntico** de IA generativa para **gobierno, calidad, MDM y
> catalogación de datos**. Simula cómo una consultora acelera el diagnóstico inicial de datos: carga
> datasets, detecta problemas de calidad, identifica datos personales, propone reglas, encuentra
> duplicados, responde políticas internas con RAG y genera un reporte ejecutivo. Todo corre en mi PC,
> sin servicios de pago, con Python, LangChain, LangGraph, Milvus y Ollama."

**Diferenciadores clave** (menciónalos):
1. No es un chatbot: es un pipeline de **7 agentes** orquestados con LangGraph.
2. El análisis es **determinista** (Pandas) → reproducible y testeable; el LLM solo añade lenguaje.
3. Está **validado contra un ground truth**: 22/22 métricas exactas.
4. **Degrada con elegancia**: funciona aunque se caiga Ollama o Milvus.

---

## 2. Preparación previa (5 min antes)

1. Levanta Milvus, API y UI (ver manual de despliegue).
2. Verifica `http://localhost:8000/health` → Ollama ✅ y Milvus ✅.
3. **Haz una pasada completa de calentamiento**: la primera respuesta del LLM y la primera búsqueda
   RAG son las más lentas; déjalas "calientes".
4. Ten abiertas: la UI (`8501`), Swagger (`8000/docs`) y una terminal para los comandos de validación.

---

## 3. Casos de uso (qué demuestra cada uno)

Datos a usar: los 5 CSV de [../datagov_agent_dataset/data/raw/](../datagov_agent_dataset/data/raw/)
(clientes, productos, proveedores, sucursales, ventas).

### UC1 — Ingesta y perfilado de datos
- **Objetivo:** convertir archivos crudos en un perfil técnico.
- **Cómo:** UI → **📥 Carga** (sube los 5 CSV) → **🔎 Perfilamiento** → `clientes`.
- **Qué mostrar:** filas/columnas, filas duplicadas, **campos sensibles** detectados (dni, correo,
  teléfono, dirección), gráfico de **nulos por campo**, perfil por columna.
- **Frase:** "Detecta automáticamente identificadores y datos personales sin que yo se lo diga."

### UC2 — Calidad de datos (8 dimensiones + score)
- **Objetivo:** detectar problemas y puntuar la calidad.
- **Cómo:** UI → **✅ Calidad** → `ventas` (y luego `clientes`).
- **Qué mostrar:** **score** y nivel de riesgo, narrativa, tabla de hallazgos con dimensión,
  severidad y **regla sugerida**. En `ventas`: integridad referencial rota (cliente/producto/sucursal
  inexistente) y **total mal calculado**.
- **Frase:** "Cubre 8 dimensiones: completitud, unicidad, validez, consistencia, integridad,
  conformidad, exactitud y oportunidad."

### UC3 — MDM y golden record
- **Objetivo:** encontrar registros maestros duplicados y proponer el registro consolidado.
- **Cómo:** UI → **🧩 MDM** → `clientes`.
- **Qué mostrar:** grupos de duplicados por **clave exacta (DNI)** y por **similaridad de nombres**,
  con el **golden record** sugerido (IDs reales `CLI…`).
- **Frase:** "Combina coincidencia exacta y fuzzy matching con rapidfuzz; el golden record toma el
  valor más completo de cada campo."

### UC4 — Catálogo y metadatos
- **Objetivo:** glosario de negocio, clasificación y responsables.
- **Cómo:** aparece en el **reporte ejecutivo** (UC6); se nutre de `diccionario_datos.csv`.
- **Qué mostrar:** definiciones de negocio, clasificación (dato personal/maestro/financiero),
  Data Owner y Data Steward sugeridos por campo.
- **Frase:** "El catálogo usa el diccionario de datos real cuando existe, con fallback heurístico."

### UC5 — RAG sobre políticas de gobierno
- **Objetivo:** responder preguntas con base en los documentos internos, **sin alucinar**.
- **Cómo:** UI → **💬 Chat RAG** → botón **"Indexar documentos…"** (los indexa en Milvus con
  embeddings reales) → preguntar.
- **Preguntas** (de [../datagov_agent_dataset/data/documents/preguntas_demo_rag.md](../datagov_agent_dataset/data/documents/preguntas_demo_rag.md)):
  - ¿Qué campos se consideran datos personales?
  - ¿Quién aprueba cambios masivos en datos maestros?
  - ¿Qué reglas aplican al campo DNI?
  - ¿Qué es un golden record?
- **Qué mostrar:** respuesta **con fuentes** y nivel de confianza; y que responde
  *"No se encontró sustento suficiente…"* cuando no hay base.
- **Frase:** "RAG estricto: cita la fuente, da confianza y se niega a inventar."

### UC6 — Recomendaciones y reporte ejecutivo
- **Objetivo:** consolidar todo en un entregable para dirección.
- **Cómo:** UI → **📊 Reporte ejecutivo** → **Generar reporte**.
- **Qué mostrar:** score global, resumen ejecutivo, **KPIs**, gráfico de score por tabla,
  **recomendaciones priorizadas** y descarga en Markdown/HTML/PDF/JSON.
- **Frase:** "Un solo clic ejecuta perfilado → calidad → MDM → catálogo → recomendaciones → reporte,
  orquestado con LangGraph."

### UC7 — Validación contra ground truth (tu carta fuerte)
- **Objetivo:** demostrar rigor: el sistema detecta exactamente lo esperado.
- **Cómo:** terminal → `python scripts/validate_dataset.py`.
- **Qué mostrar:** la tabla "detectado vs esperado" con **22/22 OK** (incluye las 449 referencias a
  sucursal inexistente, 68 totales mal calculados, 22 DNI inválidos, etc.).
- **Frase:** "No es 'parece que funciona': está validado contra un fichero de problemas esperados."

---

## 4. Guion paso a paso (~8 min)

1. **Problema (30s):** "Las empresas tienen datos dispersos, sin reglas y con baja calidad."
2. **Carga (1m):** sube los 5 CSV. Muestra la tabla de sesión.
3. **Perfilado (1.5m):** `clientes` → nulos, duplicados, datos sensibles (UC1).
4. **Calidad (2m):** `ventas` y `clientes` → score, hallazgos, reglas (UC2).
5. **MDM (1.5m):** `clientes` → duplicados + golden record (UC3).
6. **RAG (2m):** indexa y pregunta 2-3 cosas; resalta fuentes y "no inventa" (UC5).
7. **Reporte (1.5m):** genera y descarga; muestra KPIs y recomendaciones (UC4 + UC6).
8. **Validación (1m):** corre el script 22/22 (UC7).
9. **Arquitectura + cierre (1m):** ver sección 6 y roadmap.

> Versión corta imprimible: [demo_script.md](demo_script.md).

---

## 5. Pruebas alternativas por API (perfiles técnicos)

Abre **http://localhost:8000/docs** y ejecuta en vivo:
- `POST /data/upload` (sube un CSV)
- `POST /data/quality` con `{"table":"ventas"}`
- `POST /rag/ingest-default` con `{"reset": true}` (indexa los docs del paquete)
- `POST /rag/ask` con `{"question":"¿Quién aprueba cambios en datos maestros?"}`
- `POST /reports/generate`

Demuestra que la UI y el backend están **desacoplados** (API REST documentada).

---

## 6. Defensa de la arquitectura (FAQ de entrevista)

| Pregunta | Respuesta |
| -------- | --------- |
| ¿Por qué LangGraph y no un script? | Orquestación con estado, ruteo condicional (dataset/documento/pregunta) y agentes especializados reutilizables. |
| ¿Por qué el LLM no hace el análisis? | Determinismo, reproducibilidad y testeo. Contar nulos o validar FKs no debe depender de un modelo probabilístico. El LLM es para lenguaje (narrativa, RAG). |
| ¿Cómo evitas alucinaciones en el RAG? | Prompt estricto + recuperación con fuentes + respuesta "no hay sustento" cuando el contexto no alcanza. |
| ¿Por qué Milvus por Docker y no Milvus Lite? | Milvus Lite no soporta Windows; uso Milvus standalone en Docker y un vector store en memoria intercambiable para los tests. |
| ¿Cómo sabes que la calidad está bien medida? | Ground truth + `validate_dataset.py`: 22/22 métricas exactas. |
| ¿Escala a producción? | Roadmap a la nube: S3, Glue, Redshift, Athena y catálogo empresarial (Collibra/Purview/DataHub), con lineage y seguridad. |
| ¿Qué pasa si no hay GPU/Internet? | Degrada: análisis determinista + narrativa de respaldo; los tests corren sin Ollama ni Docker. |

**Stack resumido:** Python 3.11 · LangChain · LangGraph · Milvus · Ollama · FastAPI · Streamlit ·
Pandas · Pydantic · RapidFuzz · Plotly · Pytest.

---

## 7. Plan B (si algo falla en vivo)

- **Se cae Ollama** → la demo sigue: agentes con narrativa determinista (hallazgos, reglas, score,
  recomendaciones intactos).
- **Se cae Milvus** → omite el RAG por API; corre `pytest` y `validate_dataset.py` igual.
- **Falla red/Docker** → respaldo infalible: `python scripts/validate_dataset.py` (la tabla 22/22
  habla por sí sola) y `pytest` (25 verdes).
- **Lentitud del LLM** → ten una respuesta ya generada (calentamiento previo) o usa un modelo más
  pequeño.

---

## 8. Checklist final antes de exponer

- [ ] `docker ps` muestra Milvus "healthy".
- [ ] `http://localhost:8000/health` → Ollama ✅ y Milvus ✅.
- [ ] UI abre en `8501` y la barra lateral muestra ambos en verde.
- [ ] `pytest` → 25 verdes.
- [ ] `python scripts/validate_dataset.py` → 22/22 OK.
- [ ] Documentos RAG ya indexados (botón "Indexar…") y 1-2 preguntas probadas.
- [ ] Un reporte ejecutivo ya generado (para tenerlo de respaldo).
