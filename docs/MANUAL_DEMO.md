# Manual de Demostración (Profesional) — DataGov Agent

Guía detallada para **demostrar y explicar** DataGov Agent en una entrevista técnica:
qué hace cada módulo, **qué parte del código** lo implementa, qué verás y cómo contarlo.
Para instalar/levantar, ver [MANUAL_DESPLIEGUE.md](MANUAL_DESPLIEGUE.md).

---

## 0. Mapa mental: módulo → qué hace → código

| Módulo (pantalla) | Qué resuelve | Código principal |
| ----------------- | ------------ | ---------------- |
| 📥 Carga | Ingesta de CSV/Excel a memoria | [services/data_loader.py](../app/services/data_loader.py) · [api/routes_data.py](../app/api/routes_data.py) · [api/store.py](../app/api/store.py) |
| 🔎 Perfilamiento | Perfil técnico (nulos, tipos, PII) | [services/profiler.py](../app/services/profiler.py) |
| ✅ Calidad | 8 dimensiones, hallazgos y score | [services/quality_rules.py](../app/services/quality_rules.py) · [services/entities.py](../app/services/entities.py) · [agents/quality_agent.py](../app/agents/quality_agent.py) |
| 🧩 MDM | Duplicados + golden record | [services/mdm.py](../app/services/mdm.py) |
| 🗂️ Catálogo | Glosario, clasificación, owners | [agents/metadata_agent.py](../app/agents/metadata_agent.py) · [services/data_dictionary.py](../app/services/data_dictionary.py) |
| 💬 RAG | Preguntas sobre políticas, con fuentes | [agents/rag_agent.py](../app/agents/rag_agent.py) · [services/vector_store.py](../app/services/vector_store.py) · [services/embeddings.py](../app/services/embeddings.py) |
| 🧠 Recomendaciones | Acciones priorizadas | [agents/recommendation_agent.py](../app/agents/recommendation_agent.py) |
| 📊 Reporte | Documento ejecutivo | [agents/report_agent.py](../app/agents/report_agent.py) · [services/report_generator.py](../app/services/report_generator.py) |
| 🔀 Orquestación | Decide y encadena agentes | [graph/workflow.py](../app/graph/workflow.py) · [agents/supervisor.py](../app/agents/supervisor.py) |
| 🤖 LLM | Narrativa/RAG con Ollama + fallback | [services/llm.py](../app/services/llm.py) |

**Idea central que debes transmitir:** el análisis pesado es **Python determinista** (Pandas), por eso
es reproducible y testeable; el **LLM solo añade lenguaje** (narrativa, RAG, recomendaciones) y si no
está disponible, el sistema **degrada** a una salida determinista.

---

## 1. Antes de empezar (checklist)

- [ ] API: `http://localhost:8001/docs` muestra "DataGov Agent API".
- [ ] UI: `http://localhost:8501` con **API conectada**, **Ollama ✅**, **Milvus ✅**.
- [ ] Modelos: `ollama list` muestra tu LLM (`qwen3:8b` o `llama3.1:8b`) y `nomic-embed-text`.
- [ ] Calentamiento: haz 1 pasada (la primera respuesta del LLM y la 1ª búsqueda RAG son lentas).

---

## 2. Qué datos usa la demo (importante, para no confundirse)

Hay **dos tipos de datos** y van a **módulos distintos**:

### 2.1 Tablas (para Carga/Perfilado/Calidad/MDM/Reporte)
Sube **estas 5** desde `datagov_agent_dataset/data/raw/`:
```
clientes.csv   productos.csv   proveedores.csv   sucursales.csv   ventas.csv
```
> No subas `diccionario_datos.csv` ni `reglas_calidad.csv`: son **metadatos** (el sistema usa el
> diccionario internamente para el catálogo, no como tabla a analizar).

### 2.2 Documentos de gobierno (para el RAG)
El botón **"Indexar documentos de gobierno (paquete)"** indexa los **8 `.md`** de
`datagov_agent_dataset/data/documents/` — porque `DOCUMENTS_DIR` del `.env` apunta ahí
(ver [config.py](../app/config.py) y [routes_rag.py](../app/api/routes_rag.py) → `ingest_default`).

> **Tu duda aclarada:** se indexan los documentos del **paquete `datagov_agent_dataset`** (8 docs),
> **no** los que se generaron antes en `data/documents/` (esos quedaron sin uso). Por eso el mensaje
> dice "8 documentos".

---

## 3. Módulo por módulo (qué hace · demo · código · cómo explicarlo)

### 📥 3.1 Carga (Ingesta)

- **Qué hace:** lee CSV/Excel y los guarda en una sesión en memoria para que el resto de módulos
  trabajen sobre los mismos datos.
- **Demo:** pestaña **📥 Carga** → **Upload** (los 5 CSV) → **Cargar** → aparece "Tablas en sesión".
- **Qué verás:** 5 tablas con sus filas/columnas (clientes 1210, productos 350, proveedores 100,
  sucursales 10, ventas 5000).
- **Cómo funciona (código):**
  - `POST /data/upload` en [routes_data.py](../app/api/routes_data.py) recibe el archivo.
  - `load_dataframe_from_bytes()` en [data_loader.py](../app/services/data_loader.py) lo lee con
    `utf-8-sig` (elimina el BOM) → DataFrame de Pandas.
  - Se guarda en `SessionStore.add_table()` ([store.py](../app/api/store.py)).
- **Cómo lo explicas:** *"La ingesta normaliza codificación (incluido BOM) y mantiene las tablas en
  una sesión para análisis cruzado entre ellas."*

### 🔎 3.2 Perfilamiento (Data Profiling)

- **Qué hace:** genera el perfil técnico de una tabla: nulos, tipos, valores únicos, min/max/promedio,
  identificadores probables y **posibles datos personales (PII)**.
- **Demo:** **🔎 Perfilamiento** → `clientes` → **Perfilar**.
- **Qué verás:** filas/columnas, filas duplicadas, **7 campos sensibles** (nombre, apellido, dni, ruc,
  correo, teléfono, dirección), **gráfico de nulos por campo** y el detalle por columna.
- **Cómo funciona (código):** `profile_dataframe()` en [profiler.py](../app/services/profiler.py):
  - `_column_profile()` calcula métricas por columna.
  - `_sensitive_reason()` detecta PII por nombre (`SENSITIVE_NAME_HINTS`) y por patrón (regex de email).
  - `_looks_like_identifier()` detecta identificadores por nombre y cardinalidad.
- **Cómo lo explicas:** *"Detecta automáticamente identificadores y datos personales combinando
  heurísticas de nombre y de contenido; esto alimenta la clasificación del catálogo."*

### ✅ 3.3 Calidad de datos (Data Quality)

- **Qué hace:** evalúa **8 dimensiones** (completitud, unicidad, validez, consistencia, integridad
  referencial, conformidad, exactitud, oportunidad), lista hallazgos con **regla sugerida** y calcula
  un **score** (0-100) y nivel de riesgo.
- **Demo:** **✅ Calidad** → `ventas` (FK rota + total mal calculado) → luego `clientes` (DNI duplicado,
  correo inválido, país inconsistente).
- **Qué verás:** score, riesgo, narrativa (IA) y tabla de hallazgos con dimensión, severidad y regla.
- **Cómo funciona (código):** `evaluate_quality()` en [quality_rules.py](../app/services/quality_rules.py)
  orquesta los chequeos:
  - `_check_completeness` (vacíos), `_check_uniqueness` (solo PK + dni/ruc/sku vía
    [entities.py](../app/services/entities.py) → **no marca FKs**), `_check_validity` (regex de email,
    DNI=8, RUC=11, negativos, fechas futuras, cantidad 0), `_check_consistency` (país/categoría),
    `_check_total_calculation` (total = cantidad × precio), `_check_referential_integrity`
    (FK_RELATIONS, incl. `sucursal_id`), `_check_classification` (PII sin clasificar).
  - `_score()` aplica penalizaciones por dimensión (`PENALTY`/`DIMENSION_CAP`).
  - La **narrativa** la añade el LLM en `run_quality()` de
    [quality_agent.py](../app/agents/quality_agent.py) (con fallback determinista).
- **Cómo lo explicas:** *"El score es explicable: cada hallazgo descuenta puntos según su dimensión y
  severidad; las claves foráneas se validan por integridad, no como duplicados."*

### 🧩 3.4 MDM (Master Data Management)

- **Qué hace:** encuentra **registros maestros duplicados** (por clave exacta y por similaridad de
  nombres/correo) y propone un **golden record** consolidado.
- **Demo:** **🧩 MDM** → `clientes` → **Detectar duplicados** → expande un grupo.
- **Qué verás:** grupos con miembros (IDs reales `CLI…`), tipo de match, confianza, evidencia y el
  golden record sugerido.
- **Cómo funciona (código):** `detect_duplicates()` en [mdm.py](../app/services/mdm.py):
  - `ENTITY_CONFIG` define clave y campos de nombre por entidad (cliente/producto/proveedor/sucursal).
  - Coincidencia exacta por DNI/RUC/SKU + similaridad con **RapidFuzz** (`token_sort_ratio`,
    umbral `NAME_SIMILARITY_THRESHOLD`).
  - `_golden_record()` elige, por campo, el valor más frecuente/completo.
- **Cómo lo explicas:** *"Combino matching exacto y difuso; el golden record toma el valor más completo
  de cada campo, que es la base para consolidar una vista única del cliente."*

### 🗂️ 3.5 Catálogo y metadatos (Metadata & Catalog)

- **Qué hace:** genera entradas de catálogo (definición de negocio, clasificación, criticidad,
  **Data Owner / Data Steward**, reglas) por campo.
- **Demo:** se incluye dentro del **Reporte ejecutivo** (sección catálogo).
- **Cómo funciona (código):** `run_metadata()` en
  [metadata_agent.py](../app/agents/metadata_agent.py):
  - Usa `get_data_dictionary()` ([data_dictionary.py](../app/services/data_dictionary.py)) para leer
    `diccionario_datos.csv` y tomar definiciones/owners **reales**; si no existe, cae a heurísticas
    (`BUSINESS_DEFINITIONS`, `OWNERSHIP`).
- **Cómo lo explicas:** *"El catálogo se nutre del diccionario de datos corporativo cuando existe, con
  un fallback heurístico para arrancar sin él."*

### 💬 3.6 RAG (Consulta de políticas) — ver detalle en sección 4

- **Qué hace:** responde preguntas **solo** con base en los documentos de gobierno, citando fuentes y
  sin inventar.
- **Demo:** **💬 Chat RAG** → **"Indexar documentos de gobierno (paquete)"** → preguntar.
- **Cómo funciona (código):** [rag_agent.py](../app/agents/rag_agent.py) +
  [vector_store.py](../app/services/vector_store.py) + [embeddings.py](../app/services/embeddings.py).

### 🧠 3.7 Recomendaciones

- **Qué hace:** convierte hallazgos en **acciones priorizadas** (prioridad, riesgo, acción, responsable,
  impacto, esfuerzo).
- **Cómo funciona (código):** `run_recommendations()` en
  [recommendation_agent.py](../app/agents/recommendation_agent.py) (LLM con prompt
  `RECOMMENDATION_SYSTEM` + fallback determinista por severidad).

### 📊 3.8 Reporte ejecutivo

- **Qué hace:** consolida todo en un documento con resumen, KPIs, riesgos, recomendaciones y roadmap;
  exporta a Markdown/HTML/JSON/PDF.
- **Demo:** **📊 Reporte ejecutivo** → **Generar reporte** → descarga Markdown.
- **Cómo funciona (código):** `build_report()` en [report_agent.py](../app/agents/report_agent.py)
  (resumen ejecutivo con LLM + KPIs) y `save_report()` en
  [report_generator.py](../app/services/report_generator.py) (render y PDF con `xhtml2pdf`).

---

## 4. RAG en detalle (lo que más preguntan)

### 4.1 ¿Qué se indexa exactamente?
Los **8 documentos de gobierno** del paquete (`datagov_agent_dataset/data/documents/`):
política de gobierno, política de datos personales, manual de calidad, procedimiento MDM, glosario,
arquitectura, roadmap y la lista de preguntas demo.

### 4.2 ¿Cómo funciona el pipeline? (código)
1. **Chunking:** `chunk_text()` ([rag_agent.py](../app/agents/rag_agent.py)) parte cada documento en
   fragmentos (`RecursiveCharacterTextSplitter`).
2. **Embeddings:** `get_embeddings()` ([embeddings.py](../app/services/embeddings.py)) usa
   `nomic-embed-text` (768 dims) vía Ollama; sin Ollama cae a un embedding determinista.
3. **Almacenamiento:** `MilvusVectorStore.add_documents()`
   ([vector_store.py](../app/services/vector_store.py)) inserta en Milvus y hace **flush** (para que
   sea buscable de inmediato).
4. **Recuperación + respuesta:** `answer_question()` busca los top-k fragmentos y arma la respuesta con
   el prompt **estricto** `RAG_SYSTEM` ([prompts.py](../app/agents/prompts.py)): si el contexto no
   alcanza, responde literalmente *"No se encontró sustento suficiente en los documentos cargados."*

### 4.3 ¿Qué preguntas hacer? (tienen respuesta en los docs)
Usa las de `preguntas_demo_rag.md` (están diseñadas para estos documentos):

| Pregunta | Documento que la responde |
| -------- | ------------------------- |
| ¿Qué es un dato crítico? | política de gobierno / glosario |
| ¿Qué campos se consideran datos personales? | política de datos personales |
| ¿Quién aprueba cambios masivos en datos maestros? | política de gobierno / procedimiento MDM |
| ¿Qué dimensiones de calidad se deben evaluar? | manual de calidad |
| ¿Qué es un golden record? | procedimiento MDM |
| ¿Qué reglas aplican al campo DNI? | política de datos personales |
| ¿Qué acciones prioriza el roadmap de 90 días? | roadmap de gobierno |
| ¿Qué sistemas origen existen en la arquitectura demo? | arquitectura de datos |

**Prueba que no alucina:** pregunta algo fuera de los docs (p. ej. *"¿Cuál es la capital de Francia?"*)
y verás la respuesta *"No se encontró sustento…"*.

---

## 5. Orquestación con LangGraph (cómo encaja todo)

El [grafo](../app/graph/workflow.py) implementa: `START → load_input → classify_input →` y según la
entrada ramifica a **dataset** (perfilado → calidad → MDM → catálogo → recomendaciones → reporte),
**documento** (ingesta a Milvus) o **pregunta** (RAG). El **supervisor**
([supervisor.py](../app/agents/supervisor.py)) decide la ruta con heurísticas + LLM.

> Frase: *"No es un script lineal: un supervisor enruta y agentes especializados se encadenan con
> estado compartido."*

---

## 6. Validación contra ground truth (tu remate técnico)

```powershell
python scripts/validate_dataset.py
```
Compara las detecciones contra `known_issues_expected.json` e imprime **22/22 OK** (incluye 449 ventas
con sucursal inexistente, 68 totales mal calculados, 22 DNI inválidos…). Código en
[services/dataset_validation.py](../app/services/dataset_validation.py).

> Frase: *"No es 'parece que funciona': está validado contra un fichero de problemas esperados."*

---

## 7. Guion cronometrado (8-10 min)

| Tiempo | Pantalla | Acción | Frase clave |
| ------ | -------- | ------ | ----------- |
| 0:30 | — | Plantea el problema | "Datos dispersos, sin reglas, baja calidad." |
| 1:00 | 📥 Carga | Sube las 5 tablas | "Sesión en memoria para análisis cruzado." |
| 1:30 | 🔎 Perfilado | `clientes` | "Detecta PII e identificadores solo." |
| 2:00 | ✅ Calidad | `ventas` + `clientes` | "Score explicable, 8 dimensiones." |
| 1:30 | 🧩 MDM | `clientes` | "Matching exacto + difuso, golden record." |
| 2:00 | 💬 RAG | indexar + 2-3 preguntas | "Responde con fuentes, no inventa." |
| 1:30 | 📊 Reporte | Generar | "Un clic orquesta 7 agentes." |
| 1:00 | terminal | `validate_dataset.py` | "Validado contra ground truth: 22/22." |
| 1:00 | — | Arquitectura + roadmap | "Local, sin pago; escala a cloud." |

---

## 8. FAQ / dudas frecuentes

- **¿Qué documentos indexa el RAG?** Los **8 del paquete** `datagov_agent_dataset/data/documents/`
  (config `DOCUMENTS_DIR`). No los antiguos de `data/documents/`.
- **El indicador "Chunks indexados: 0" no cambia tras indexar.** Es la cuenta que se muestra al cargar
  la página; el número real está en el mensaje verde ("Indexados N chunks…"). Se refresca al volver a
  entrar a la pantalla.
- **¿Tengo que cargar los 5 CSV siempre?** Sí, las tablas viven en memoria (sesión). Si reinicias la
  API, vuelve a cargarlas. Cárgalas **antes** de Calidad/MDM para la integridad referencial entre tablas.
- **¿Por qué la primera respuesta del LLM/RAG tarda?** Carga del modelo y de la colección; por eso se
  recomienda calentar antes.
- **¿Funciona sin Ollama o sin Milvus?** Sí, degrada: análisis determinista + narrativa de respaldo;
  los tests corren sin ninguno de los dos.

---

## 9. Plan B (si algo falla en vivo)

- **Sin Ollama** → narrativa determinista (hallazgos/score/recomendaciones intactos).
- **Sin Milvus** → omite el RAG por API; `pytest` y `validate_dataset.py` corren igual.
- **Falla todo** → respaldo infalible: `python scripts/validate_dataset.py` (22/22) y `pytest` (25 verdes).

---

## 10. Checklist final antes de exponer

- [ ] API `8001` (`/docs`) y UI `8501` en verde (Ollama + Milvus).
- [ ] `pytest` → 25 verdes · `python scripts/validate_dataset.py` → 22/22.
- [ ] 5 tablas cargadas; pasada por las 6 pantallas hecha.
- [ ] Documentos RAG indexados y 2-3 preguntas probadas (incluida una "sin sustento").
- [ ] Un reporte ejecutivo generado de respaldo.
