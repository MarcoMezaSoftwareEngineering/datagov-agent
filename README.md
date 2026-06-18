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

### 2. Datos
La **fuente canónica** es el paquete validado [`datagov_agent_dataset/`](datagov_agent_dataset/)
(clientes 1210, productos 350, proveedores 100, sucursales 10, ventas 5000) con su diccionario de
datos, documentos de gobierno y un **ground truth** de problemas esperados. La config ya apunta ahí.

> El generador `python data/synthetic/generate_synthetic_data.py` sigue disponible como utilidad
> para crear una muestra pequeña adicional.

### 3. (Opcional) Ollama para LLM/embeddings reales
```bash
ollama pull llama3.1:8b
ollama pull nomic-embed-text
```

### 4. (Para RAG) Milvus vía Docker
```bash
docker compose up -d            # Milvus en localhost:19533
```

### 5. Backend + Interfaz
```bash
uvicorn app.main:app --reload --port 8010              # API en http://localhost:8010/docs
streamlit run ui/streamlit_app.py --server.port 8510   # UI en http://localhost:8510
```

> En Windows sin `make`, usa los comandos de arriba. Con `make`: `make data`, `make api`, `make ui`,
> `make milvus-up`, `make test`.

---

## 🧪 Pruebas y validación
```bash
pytest                                # suite unitaria
python scripts/validate_dataset.py    # detecciones vs ground truth del dataset
```
La suite corre **sin Ollama ni Docker** (usa embeddings deterministas + vector store en memoria;
el test de integración de Milvus se omite automáticamente si no está disponible).

El script de validación compara las detecciones del motor de calidad contra
`datagov_agent_dataset/data/expected_outputs/known_issues_expected.json` (**22/22 métricas exactas**:
DNI/correos inválidos, faltantes, precios negativos, fechas futuras, integridad referencial de
clientes/productos/**sucursales**, totales mal calculados, etc.).

---

## 📦 Casos de uso (demo)
- **Perfilamiento**: nulos, duplicados, tipos, identificadores y datos sensibles.
- **Calidad**: 8 dimensiones, score por tabla y reglas sugeridas.
- **MDM**: duplicados por clave exacta + similaridad de nombres, golden record.
- **RAG**: preguntas sobre políticas de gobierno con fuentes y nivel de confianza.
- **Reporte ejecutivo**: resumen, KPIs, riesgos, recomendaciones y roadmap (MD/HTML/JSON/PDF).

**Manuales:** [Despliegue e Implementación](docs/MANUAL_DESPLIEGUE.md) ·
[Demostración y Casos de Uso](docs/MANUAL_DEMO.md) · [Guion corto](docs/demo_script.md).

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
