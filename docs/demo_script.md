# Guion de Demo — DataGov Agent

Duración sugerida: 8–10 minutos. Pensado para entrevista del perfil **Analista de IA Generativa y
Agéntica Junior**.

## 0. Preparación
```bash
.venv\Scripts\activate
python data/synthetic/generate_synthetic_data.py
docker compose up -d            # Milvus (para el RAG)
ollama serve                    # si se quiere LLM real
uvicorn app.main:app --reload
streamlit run ui/streamlit_app.py
```

## 1. Plantear el problema (30s)
> "Las empresas tienen datos dispersos, sin reglas claras y con baja calidad. DataGov Agent simula
> cómo una consultora acelera el diagnóstico con agentes de IA, 100% local y sin servicios de pago."

## 2. Cargar datasets (1 min)
- Pestaña **📥 Carga** → subir `clientes.csv`, `productos.csv`, `ventas.csv`, `proveedores.csv`.
- Mostrar la tabla de "Tablas en sesión".

## 3. Perfilamiento (1.5 min)
- Pestaña **🔎 Perfilamiento** → tabla `clientes` → **Perfilar**.
- Señalar: filas/columnas, **filas duplicadas**, **campos sensibles** (dni, correo, teléfono…),
  gráfico de **nulos por campo**.

## 4. Calidad de datos (2 min)
- Pestaña **✅ Calidad** → `clientes` → **Evaluar calidad**.
- Mostrar el **score** y el **riesgo**, la **narrativa** y la tabla de **hallazgos** con la
  dimensión, severidad y regla sugerida (DNI duplicado, correo inválido, país inconsistente…).
- Repetir con `ventas` para mostrar **integridad referencial** (cliente inexistente) y **total mal
  calculado**.

## 5. MDM (1.5 min)
- Pestaña **🧩 MDM** → `clientes` → **Detectar duplicados**.
- Mostrar grupos por **clave exacta (DNI)** y por **similaridad de nombres**, con el **golden record**
  sugerido.

## 6. RAG sobre políticas (2 min)
- Pestaña **💬 Chat RAG** → **Indexar documentos de data/documents/**.
- Preguntar:
  - "¿Qué campos deben considerarse datos personales?"
  - "¿Quién aprueba cambios en datos maestros?"
  - "¿Qué reglas deben aplicarse al campo DNI?"
- Resaltar la **respuesta con fuentes** y el **nivel de confianza**, y que **no inventa** (responde
  "No se encontró sustento…" cuando no hay base).

## 7. Reporte ejecutivo (1.5 min)
- Pestaña **📊 Reporte ejecutivo** → **Generar reporte**.
- Mostrar **score global**, **resumen ejecutivo**, **KPIs**, gráfico de score por tabla,
  **recomendaciones** priorizadas y la descarga en **Markdown**.

## 8. Arquitectura (1 min)
> "Backend FastAPI, orquestación con LangGraph (supervisor + 7 agentes), análisis determinista con
> Pandas, RAG con LangChain + Milvus, y LLM local con Ollama. El análisis no depende del LLM, así que
> es reproducible y testeable."

## 9. Cierre — Roadmap (30s)
> "El siguiente paso sería llevar esto a la nube: S3, Glue, Redshift y un catálogo empresarial, con
> lineage y controles de seguridad sobre datos personales."

---

## Preguntas de respaldo para el RAG
- ¿Qué es un dato crítico según la política?
- ¿Qué controles se aplican a datos personales?
- ¿Cuáles son las responsabilidades del Data Steward?
- ¿Qué debe contener el catálogo de datos?

## Preguntas de respaldo sobre los datos
- Analiza la calidad de la tabla clientes.
- ¿Qué campos tienen mayor riesgo?
- Detecta posibles duplicados de clientes.
- Genera reglas de calidad para la tabla ventas.
