# Documento de Arquitectura de Datos (Simulada)

## 1. Visión general
La arquitectura de datos simulada describe cómo fluyen los datos desde las fuentes hasta el
consumo analítico, incluyendo gobierno, calidad y catalogación.

## 2. Capas
1. **Ingesta (Raw)**: archivos CSV/Excel y documentos (PDF/TXT/MD) cargados localmente.
2. **Procesamiento (Curated)**: perfilamiento, reglas de calidad, MDM y catalogación.
3. **Conocimiento (Knowledge)**: documentos de gobierno indexados en una base vectorial (Milvus)
   para RAG.
4. **Servicio (Serving)**: API (FastAPI) y UI (Streamlit) que exponen diagnósticos y reportes.

## 3. Componentes técnicos
- **Pandas** para análisis de datos.
- **LangChain** para carga documental, RAG y prompts.
- **LangGraph** para orquestar agentes especializados.
- **Milvus** como base vectorial local (vía Docker).
- **Ollama** para ejecutar modelos LLM locales (Llama 3.1 8B) y embeddings (nomic-embed-text).
- **FastAPI** como backend y **Streamlit** como frontend.

## 4. Flujo agéntico
El supervisor decide la ruta según la entrada: análisis de dataset, ingestión de documentos o
pregunta RAG. La rama de dataset ejecuta: perfilado → calidad → MDM → catálogo → recomendaciones →
reporte ejecutivo.

## 5. Modernización futura (cloud simulada)
La arquitectura está diseñada para migrar a un esquema cloud: almacenamiento en S3, catálogo en
Glue, data warehouse en Redshift y consultas con Athena. La capa de gobierno y calidad se mantiene
como control transversal.
