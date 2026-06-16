# 🧭 DataGov Agent

> Sistema **local** de IA generativa y agéntica para **gobierno, calidad, MDM y catalogación de datos**.

DataGov Agent simula cómo una consultora de datos puede acelerar diagnósticos iniciales usando
**agentes especializados**. Carga datasets sintéticos, detecta problemas de calidad, identifica
datos sensibles, propone reglas, detecta duplicados (MDM), consulta políticas internas mediante
**RAG** y genera un **reporte ejecutivo** — todo corriendo en local, sin servicios de pago.

---

## 🎯 Problema
Las organizaciones tienen datos dispersos, baja calidad, sin documentación clara, con campos
duplicados y reglas de negocio no formalizadas. Esto genera reportes inconsistentes, duplicidad de
clientes/productos, falta de trazabilidad y riesgo en el manejo de datos personales.

## 💡 Solución
Agentes especializados (perfilado, calidad, MDM, catálogo, RAG, recomendaciones, reporte) analizan
datasets y documentos de gobierno para generar diagnósticos y recomendaciones accionables.

## 🧱 Stack
Python 3.11 · LangChain · LangGraph · Milvus (Docker) · Ollama (Llama 3.1 8B + nomic-embed-text) ·
FastAPI · Streamlit · Pandas · Pydantic · RapidFuzz · Plotly · Pytest.

> **Diseño robusto:** todo el análisis pesado (perfilado, calidad, MDM, score) es **Python
> determinista**. El LLM solo añade narrativa/RAG/recomendaciones y degrada elegantemente: el
> sistema **corre y se prueba sin Ollama ni Docker** gracias a sus _fallbacks_.

---

## 🏗️ Arquitectura

```text
Usuario → Streamlit UI → FastAPI Backend → LangGraph Supervisor
                                              ├── Data Profiler Agent
                                              ├── Data Quality Agent
                                              ├── MDM Agent
                                              ├── Metadata Agent
                                              ├── RAG Policy Agent
                                              ├── Recommendation Agent
                                              └── Report Agent
                                                    │
                          LangChain (loaders, splitter, retriever, prompts)
                                                    │
                                  Milvus (vector DB) · Ollama (LLM local)
```

Ver detalle en [docs/architecture.md](docs/architecture.md).

---

## 🚀 Instalación local

### 1. Entorno (Python 3.11)
```bash
py -3.11 -m venv .venv
.venv\Scripts\activate            # Windows
pip install -r requirements.txt
```

### 2. Generar datasets sintéticos
```bash
python data/synthetic/generate_synthetic_data.py
```

### 3. (Opcional) Ollama para LLM/embeddings reales
```bash
ollama pull llama3.1:8b
ollama pull nomic-embed-text
```

### 4. (Para RAG) Milvus vía Docker
```bash
docker compose up -d            # Milvus en localhost:19530
```

### 5. Backend + Interfaz
```bash
uvicorn app.main:app --reload                 # API en http://localhost:8000/docs
streamlit run ui/streamlit_app.py             # UI en http://localhost:8501
```

> En Windows sin `make`, usa los comandos de arriba. Con `make`: `make data`, `make api`, `make ui`,
> `make milvus-up`, `make test`.

---

## 🧪 Pruebas
```bash
pytest
```
La suite corre **sin Ollama ni Docker** (usa embeddings deterministas + vector store en memoria;
el test de integración de Milvus se omite automáticamente si no está disponible).

---

## 📦 Casos de uso (demo)
- **Perfilamiento**: nulos, duplicados, tipos, identificadores y datos sensibles.
- **Calidad**: 8 dimensiones, score por tabla y reglas sugeridas.
- **MDM**: duplicados por clave exacta + similaridad de nombres, golden record.
- **RAG**: preguntas sobre políticas de gobierno con fuentes y nivel de confianza.
- **Reporte ejecutivo**: resumen, KPIs, riesgos, recomendaciones y roadmap (MD/HTML/JSON/PDF).

Guion completo en [docs/demo_script.md](docs/demo_script.md).

---

## 🗂️ Estructura
```
app/        config, api, agents, graph (LangGraph), services, schemas, utils
ui/         streamlit_app.py
data/       synthetic/ (datasets) · documents/ (10 docs de gobierno) · processed/ (reportes)
notebooks/  generación de datos y pruebas de reglas
tests/      profiler, quality, mdm, rag
docs/       architecture, project_plan, data_dictionary, prompts, demo_script
```

---

## ⚠️ Limitaciones
Proyecto **local**, con **datos sintéticos**, no productivo. No usa nube pagada ni APIs comerciales
como requisito, no hace fine-tuning ni procesa millones de registros. En Windows, Milvus corre vía
Docker (Milvus Lite solo soporta Linux/macOS).

## 🛣️ Roadmap futuro
Integración cloud (AWS S3, Glue, Redshift, Athena, Lake Formation), catálogo empresarial
(Collibra/Purview/DataHub), lineage automatizado, observabilidad de agentes y controles de seguridad
(enmascaramiento, clasificación automática de PII, auditoría). Ver [docs/architecture.md](docs/architecture.md).

---

## 📝 Licencia
MIT — uso educativo y de portafolio.
