# Manual de Demostración y Casos de Uso — DataGov Agent

Cómo demostrar DataGov Agent paso a paso (entrevista o portafolio).
Para levantar el sistema, ver [MANUAL_DESPLIEGUE.md](MANUAL_DESPLIEGUE.md).

---

## 1. Antes de empezar (checklist)

- [ ] Backend arriba: `http://localhost:8001/docs` muestra "DataGov Agent API".
- [ ] UI arriba: `http://localhost:8501`, barra lateral con **API conectada**, **Ollama ✅**, **Milvus ✅**.
- [ ] Modelos: `qwen3:8b` (o `llama3.1:8b`) y `nomic-embed-text` descargados (`ollama list`).
- [ ] Haz una pasada de calentamiento (la primera respuesta del LLM y la primera búsqueda RAG son lentas).

> Si la UI dice "API no disponible", revisa el puerto: la API debe correr en el mismo que `API_BASE_URL`
> del `.env` (en esta máquina, **8001**, porque el 8000 lo ocupa otro proyecto).

---

## 2. Qué archivos cargar

Desde `datagov_agent_dataset/data/raw/` sube **estas 5 tablas**:

```
clientes.csv   productos.csv   proveedores.csv   sucursales.csv   ventas.csv
```

> **No** subas `diccionario_datos.csv` ni `reglas_calidad.csv`: son metadatos, no tablas
> (el sistema ya usa el diccionario internamente para el catálogo).
>
> Carga las **5 antes** de Calidad/MDM para que funcione la **integridad referencial entre tablas**
> (p. ej. detectar que una venta apunta a una sucursal inexistente).

---

## 3. Recorrido clic por clic (la demo)

### 3.1 📥 Carga
1. **Upload** → selecciona los 5 CSV a la vez → **Cargar**.
2. "Tablas en sesión" debe listar las 5 con filas/columnas.

### 3.2 🔎 Perfilamiento
1. Elige `clientes` → **Perfilar**.
2. Observa: filas/columnas, **filas duplicadas**, **campos sensibles** (dni, correo, teléfono,
   dirección) y el **gráfico de nulos por campo**.

### 3.3 ✅ Calidad
1. Elige `ventas` → **Evaluar calidad**.
2. Observa **score**, **riesgo**, narrativa y la tabla de hallazgos: **integridad referencial rota**
   (cliente/producto/**sucursal** inexistente) y **total mal calculado**.
3. Repite con `clientes`: DNI duplicado, correo inválido, país inconsistente (Perú/PE).

### 3.4 🧩 MDM
1. Elige `clientes` → **Detectar duplicados**.
2. Expande un grupo: **miembros** (IDs reales `CLI…`), **evidencia** y el **golden record** sugerido.

### 3.5 💬 Chat RAG
1. Pulsa **"Indexar documentos de data/documents/"** y espera "Indexados N chunks".
2. Escribe una pregunta → **Preguntar**. Resalta la **respuesta con fuentes** y el nivel de confianza,
   y que responde *"No se encontró sustento…"* cuando no hay base (no inventa).

Preguntas recomendadas (de `datagov_agent_dataset/data/documents/preguntas_demo_rag.md`):
- ¿Qué campos se consideran datos personales?
- ¿Quién aprueba cambios masivos en datos maestros?
- ¿Qué reglas aplican al campo DNI?
- ¿Qué es un golden record?

### 3.6 📊 Reporte ejecutivo
1. **Generar reporte**.
2. Observa: score global, **KPIs**, gráfico de score por tabla, **recomendaciones priorizadas** y
   **descarga en Markdown**.

### 3.7 Validación (terminal) — tu carta fuerte
```powershell
python scripts/validate_dataset.py
```
Imprime la tabla "detectado vs esperado" con **22/22 OK** (incluye las 449 ventas con sucursal
inexistente, 68 totales mal calculados, 22 DNI inválidos, etc.).

---

## 4. Casos de uso (qué demuestra cada pantalla)

| # | Pantalla | Demuestra |
| - | -------- | --------- |
| UC1 | Perfilamiento | Detecta tipos, identificadores y **datos personales** automáticamente |
| UC2 | Calidad | 8 dimensiones, **score** por tabla y **reglas sugeridas** |
| UC3 | MDM | Duplicados (clave exacta + fuzzy) y **golden record** |
| UC4 | Reporte (catálogo) | Glosario, clasificación, **Data Owner/Steward** (desde el diccionario) |
| UC5 | Chat RAG | Respuestas con **fuentes**, confianza y **sin alucinar** |
| UC6 | Reporte ejecutivo | Consolida todo: KPIs, riesgos, recomendaciones, roadmap |
| UC7 | `validate_dataset.py` | **Validado contra ground truth** (22/22) |

---

## 5. Guion de exposición (~8 min, qué decir)

1. **Problema (30s):** "Las empresas tienen datos dispersos, sin reglas y con baja calidad."
2. **Carga (1m):** sube las 5 tablas.
3. **Perfilado (1.5m):** `clientes` → nulos, duplicados, datos sensibles.
4. **Calidad (2m):** `ventas` y `clientes` → score, hallazgos, reglas.
5. **MDM (1.5m):** `clientes` → duplicados + golden record.
6. **RAG (2m):** indexa y pregunta 2-3 cosas; resalta fuentes y "no inventa".
7. **Reporte (1.5m):** genera y descarga; KPIs y recomendaciones.
8. **Validación (1m):** corre `validate_dataset.py` → 22/22.
9. **Arquitectura + cierre (1m):** ver sección 7 y roadmap.

> Versión muy corta: [demo_script.md](demo_script.md).

---

## 6. Pruebas por API (perfiles técnicos, opcional)

Abre `http://localhost:8001/docs` (Swagger) y ejecuta en vivo:
- `POST /data/upload` (sube un CSV)
- `POST /data/quality` con `{"table":"ventas"}`
- `POST /rag/ingest-default` con `{"reset": true}`
- `POST /rag/ask` con `{"question":"¿Quién aprueba cambios en datos maestros?"}`
- `POST /reports/generate`

Demuestra que UI y backend están **desacoplados** (API REST documentada).

---

## 7. Defensa de la arquitectura (FAQ)

| Pregunta | Respuesta |
| -------- | --------- |
| ¿Por qué LangGraph? | Orquestación con estado y ruteo condicional (dataset/documento/pregunta) entre agentes especializados. |
| ¿Por qué el LLM no hace el análisis? | Determinismo, reproducibilidad y testeo. Contar nulos o validar FKs no debe depender de un modelo probabilístico; el LLM es para lenguaje (narrativa, RAG). |
| ¿Cómo evitas alucinaciones? | Prompt estricto + recuperación con fuentes + "no hay sustento" cuando el contexto no alcanza. |
| ¿Por qué Milvus por Docker? | Milvus Lite no soporta Windows; uso Milvus standalone y un vector store en memoria para los tests. |
| ¿Cómo validas la calidad? | Ground truth + `validate_dataset.py`: 22/22 métricas exactas. |
| ¿Escala a producción? | Roadmap a S3/Glue/Redshift/Athena y catálogo empresarial, con lineage y seguridad. |

**Stack:** Python 3.11 · LangChain · LangGraph · Milvus · Ollama · FastAPI · Streamlit · Pandas ·
Pydantic · RapidFuzz · Plotly · Pytest.

---

## 8. Plan B (si algo falla en vivo)

- **Sin Ollama** → la demo sigue: narrativa determinista (hallazgos, reglas, score, recomendaciones).
- **Sin Milvus** → omite el RAG por API; `pytest` y `validate_dataset.py` corren igual.
- **Falla red/Docker** → respaldo infalible: `python scripts/validate_dataset.py` (22/22) y `pytest`
  (25 verdes). La sesión de tablas es en memoria: si reinicias la API, vuelve a cargar los 5 CSV.

---

## 9. Checklist final antes de exponer

- [ ] API en `8001` responde (`/docs`) y UI en `8501` con todo en verde.
- [ ] `pytest` → 25 verdes · `python scripts/validate_dataset.py` → 22/22.
- [ ] Las 5 tablas cargadas y una pasada por las 6 pantallas hecha.
- [ ] Documentos RAG indexados y 1-2 preguntas probadas.
- [ ] Un reporte ejecutivo generado (de respaldo).
