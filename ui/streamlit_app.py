"""Interfaz Streamlit de DataGov Agent.

Consume el backend FastAPI. Levanta primero la API:
    uvicorn app.main:app --reload
y luego:
    streamlit run ui/streamlit_app.py
"""

from __future__ import annotations

import os

import pandas as pd
import plotly.express as px
import requests
import streamlit as st
from dotenv import load_dotenv

# Carga .env si existe, para que API_BASE_URL (p. ej. puerto alternativo) se respete.
load_dotenv()

API = os.getenv("API_BASE_URL", "http://localhost:8010")
TIMEOUT = 180

st.set_page_config(page_title="DataGov Agent", page_icon="🧭", layout="wide")


# --------------------------------------------------------------------------- helpers


def api_get(path: str):
    try:
        r = requests.get(f"{API}{path}", timeout=TIMEOUT)
        return r.json() if r.ok else {"_error": r.text, "_status": r.status_code}
    except requests.RequestException as exc:
        return {"_error": str(exc)}


def api_post(path: str, json=None, files=None):
    try:
        r = requests.post(f"{API}{path}", json=json, files=files, timeout=TIMEOUT)
        return r.json() if r.ok else {"_error": r.text, "_status": r.status_code}
    except requests.RequestException as exc:
        return {"_error": str(exc)}


def show_error(resp) -> bool:
    if isinstance(resp, dict) and "_error" in resp:
        st.error(f"Error de API: {resp.get('_error')}")
        return True
    return False


def score_color(score: int) -> str:
    return "🟢" if score >= 80 else ("🟡" if score >= 65 else "🔴")


def _fmt_cell(v):
    """Convierte celdas con listas o tipos mixtos a texto (Streamlit/Arrow-safe)."""
    if isinstance(v, list):
        return ", ".join(map(str, v))
    if v is None or (not isinstance(v, str) and pd.isna(v)):
        return ""
    return str(v)


# --------------------------------------------------------------------------- sidebar / health


st.sidebar.title("🧭 DataGov Agent")
st.sidebar.caption("Gobierno, calidad, MDM y catalogación de datos — local")

health = api_get("/health")
if "_error" in health:
    st.sidebar.error(
        f"API no disponible en {API}\n\n"
        "Levanta el backend (puerto dedicado de DataGov):\n"
        "`uvicorn app.main:app --reload --port 8010`\n\n"
        "La UI usa `API_BASE_URL=http://localhost:8010` desde `.env`."
    )
else:
    st.sidebar.success("API conectada")
    st.sidebar.write(f"🤖 Ollama: {'✅' if health.get('ollama_available') else '⚠️ no'}")
    st.sidebar.write(f"🗄️ Milvus: {'✅' if health.get('milvus_available') else '⚠️ no'}")

page = st.sidebar.radio(
    "Navegación",
    ["📥 Carga", "🔎 Perfilamiento", "✅ Calidad", "🧩 MDM", "💬 Chat RAG", "📊 Reporte ejecutivo"],
)


def loaded_tables() -> list[str]:
    data = api_get("/data/tables")
    if "_error" in data:
        return []
    return [t["name"] for t in data.get("tables", [])]


# --------------------------------------------------------------------------- pages


if page == "📥 Carga":
    st.header("📥 Carga de datasets")
    st.write("Sube archivos CSV o Excel (clientes, productos, ventas, proveedores).")
    files = st.file_uploader("Archivos tabulares", type=["csv", "xlsx", "xls"], accept_multiple_files=True)
    if st.button("Cargar", type="primary") and files:
        for f in files:
            resp = api_post("/data/upload", files={"file": (f.name, f.getvalue())})
            if not show_error(resp):
                st.success(f"{resp['file_name']} cargado: {resp['rows']} filas, {resp['columns']} columnas")

    st.divider()
    st.subheader("Tablas en sesión")
    tables = api_get("/data/tables")
    if not show_error(tables):
        rows = tables.get("tables", [])
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True)
        else:
            st.info("Aún no hay tablas cargadas.")


elif page == "🔎 Perfilamiento":
    st.header("🔎 Perfilamiento de datos")
    tables = loaded_tables()
    if not tables:
        st.info("Carga datasets primero en la pestaña 📥 Carga.")
    else:
        table = st.selectbox("Tabla", tables)
        if st.button("Perfilar", type="primary"):
            prof = api_post("/data/profile", json={"table": table})
            if not show_error(prof):
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Filas", prof["rows"])
                c2.metric("Columnas", prof["columns"])
                c3.metric("Filas duplicadas", prof["duplicate_rows"])
                c4.metric("Campos sensibles", len(prof["possible_sensitive_fields"]))

                if prof["possible_sensitive_fields"]:
                    st.warning("Posibles datos personales: " + ", ".join(prof["possible_sensitive_fields"]))

                if prof["nulls"]:
                    st.subheader("Nulos por campo")
                    nulls_df = pd.DataFrame(
                        {"campo": list(prof["nulls"].keys()), "nulos": list(prof["nulls"].values())}
                    )
                    st.plotly_chart(px.bar(nulls_df, x="campo", y="nulos", color="nulos"), use_container_width=True)

                st.subheader("Perfil por columna")
                cp_df = pd.DataFrame(prof["column_profiles"])
                # sample_values/min/max contienen valores de tipos mixtos (str y números);
                # se convierten a texto para que Streamlit/Arrow puedan renderizarlos.
                for c in ("sample_values", "min", "max"):
                    if c in cp_df.columns:
                        cp_df[c] = cp_df[c].apply(_fmt_cell)
                st.dataframe(cp_df, use_container_width=True)


elif page == "✅ Calidad":
    st.header("✅ Calidad de datos")
    tables = loaded_tables()
    if not tables:
        st.info("Carga datasets primero en la pestaña 📥 Carga.")
    else:
        table = st.selectbox("Tabla", tables)
        if st.button("Evaluar calidad", type="primary"):
            rep = api_post("/data/quality", json={"table": table})
            if not show_error(rep):
                c1, c2, c3 = st.columns(3)
                c1.metric("Score de calidad", f"{rep['quality_score']}/100")
                c2.metric("Nivel de riesgo", rep["risk_level"].upper())
                c3.metric("Hallazgos", len(rep["findings"]))
                st.write(f"{score_color(rep['quality_score'])} **Narrativa:** {rep.get('narrative', '')}")

                if rep["findings"]:
                    st.subheader("Hallazgos")
                    st.dataframe(
                        pd.DataFrame(rep["findings"])[
                            ["field", "problem", "quality_dimension", "severity", "suggested_rule", "affected_count"]
                        ],
                        use_container_width=True,
                    )
                else:
                    st.success("Sin hallazgos relevantes.")


elif page == "🧩 MDM":
    st.header("🧩 Master Data Management — posibles duplicados")
    tables = loaded_tables()
    if not tables:
        st.info("Carga datasets primero en la pestaña 📥 Carga.")
    else:
        table = st.selectbox("Tabla (entidad maestra)", tables)
        if st.button("Detectar duplicados", type="primary"):
            res = api_post("/data/mdm", json={"table": table})
            if not show_error(res):
                st.metric("Duplicados detectados", res.get("duplicates_detected", 0))
                groups = res.get("duplicate_groups", [])
                if not groups:
                    st.success("No se detectaron duplicados.")
                for i, g in enumerate(groups, 1):
                    with st.expander(f"Grupo {i} — {g['match_type']} (confianza {g['confidence']})"):
                        st.write("**Miembros:**", ", ".join(g["member_ids"]))
                        st.write("**Evidencia:**", "; ".join(g.get("evidence", [])))
                        st.write("**Golden record sugerido:**")
                        st.json(g["golden_record"]["values"])


elif page == "💬 Chat RAG":
    st.header("💬 Consulta de políticas de gobierno (RAG)")
    rag_status = api_get("/rag/status")
    if not show_error(rag_status):
        st.caption(
            f"Milvus: {'✅' if rag_status.get('milvus_available') else '⚠️ no disponible'} · "
            f"Chunks indexados: {rag_status.get('indexed_chunks', 0)}"
        )
    st.caption("Se indexan los documentos de gobierno del paquete (carpeta DOCUMENTS_DIR del .env).")
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Indexar documentos de gobierno (paquete)"):
            res = api_post("/rag/ingest-default", json={"reset": True})
            if not show_error(res):
                st.success(
                    f"Indexados {res['ingested_chunks']} chunks de {res['ingested_files']} documentos."
                )
    with col2:
        docs = st.file_uploader("…o sube documentos", type=["pdf", "txt", "md", "docx"], accept_multiple_files=True)
        if st.button("Indexar subidos") and docs:
            files = [("files", (d.name, d.getvalue())) for d in docs]
            res = api_post("/rag/ingest", files=files)
            if not show_error(res):
                st.success(f"Indexados {res['ingested_chunks']} chunks.")

    st.divider()
    question = st.text_input("Pregunta", placeholder="¿Qué campos deben considerarse datos personales?")
    if st.button("Preguntar", type="primary") and question:
        ans = api_post("/rag/ask", json={"question": question})
        if not show_error(ans):
            st.markdown(f"### Respuesta\n{ans['answer']}")
            if ans.get("rationale"):
                st.markdown(f"**Fundamento:** {ans['rationale']}")
            st.caption(f"Confianza: {ans['confidence']} · Sustentada: {'sí' if ans['grounded'] else 'no'}")
            if ans.get("sources"):
                st.markdown("**Fuentes:** " + ", ".join(ans["sources"]))


elif page == "📊 Reporte ejecutivo":
    st.header("📊 Reporte ejecutivo de gobierno de datos")
    tables = loaded_tables()
    if not tables:
        st.info("Carga datasets primero en la pestaña 📥 Carga.")
    else:
        st.write("Tablas a incluir:", ", ".join(tables))
        if st.button("Generar reporte", type="primary"):
            with st.spinner("Ejecutando agentes (perfilado → calidad → MDM → catálogo → recomendaciones)…"):
                rep = api_post("/reports/generate", json={"tables": tables, "save_files": True})
            if not show_error(rep):
                st.metric("Score global de calidad", f"{rep['overall_score']}/100")
                st.subheader("Resumen ejecutivo")
                st.write(rep["executive_summary"])

                st.subheader("KPIs")
                st.json(rep["kpis"])

                st.subheader("Score por tabla")
                qdf = pd.DataFrame(
                    [{"tabla": q["table"], "score": q["quality_score"], "riesgo": q["risk_level"]}
                     for q in rep["quality_reports"]]
                )
                st.plotly_chart(px.bar(qdf, x="tabla", y="score", color="riesgo", range_y=[0, 100]),
                                use_container_width=True)

                st.subheader("Recomendaciones")
                for r in rep["recommendations"]:
                    st.markdown(f"**[{r['priority'].upper()}] {r['title']}**")
                    st.caption(f"Riesgo: {r['risk']}")
                    st.write(f"Acción: {r['suggested_action']} · Responsable: {r['responsible']}")

                md = api_get("/reports/latest/markdown")
                if not show_error(md):
                    st.download_button("⬇️ Descargar reporte (Markdown)", md["markdown"],
                                       file_name="reporte_ejecutivo.md")
