# Comandos de Inicio — DataGov Agent

Arranque diario en **4 comandos**. Puertos dedicados: **API 8010 · UI 8510 · Milvus 19533**.

> Antes de todo, en cada terminal: situarse en la raíz y activar el entorno.
> ```powershell
> cd F:\PROGRAMACION\DWConsulware\DataGov_agent
> .\.venv\Scripts\Activate.ps1
> ```

---

## Los 4 comandos

### 1) Milvus (base vectorial, para el RAG) — Docker
```powershell
docker compose up -d
```
Queda en `localhost:19533`. (Se levanta una vez; sigue corriendo en segundo plano.)

### 2) Ollama (LLM "llama"/qwen + embeddings)
```powershell
ollama run qwen3:8b
```
Esto carga el modelo en memoria (lo "lanza"). Sal con **Ctrl + D** y el modelo queda caliente.
> Ollama normalmente ya corre como servicio en Windows; este comando solo lo **precalienta**.
> Si falta algún modelo: `ollama pull qwen3:8b` y `ollama pull nomic-embed-text`.
> Verifica lo instalado con: `ollama list`.

### 3) Terminal 1 — Backend (API FastAPI)
```powershell
uvicorn app.main:app --reload --port 8010
```
API en `http://localhost:8010` · Swagger: `http://localhost:8010/docs`

### 4) Terminal 2 — Interfaz (Streamlit)
```powershell
streamlit run ui/streamlit_app.py --server.port 8510
```
Abre **http://localhost:8510** (¡no 8501, ese es otro proyecto!).

---

## Verificación
En la barra lateral de la UI debe verse: **API conectada**, **🤖 Ollama ✅**, **🗄️ Milvus ✅**.
O por consola:
```powershell
curl http://localhost:8010/health
```

## Apagar al terminar
```powershell
# Ctrl + C en las terminales de uvicorn y streamlit
docker compose down        # detiene Milvus (conserva ./volumes)
```

---

### Resumen ultra-rápido (copiar/pegar)
```powershell
# (una vez) cd al proyecto + activar venv en cada terminal
docker compose up -d                                    # 1. Milvus
ollama run qwen3:8b                                      # 2. LLM (Ctrl+D para salir)
uvicorn app.main:app --reload --port 8010               # 3. Terminal 1 (API)
streamlit run ui/streamlit_app.py --server.port 8510    # 4. Terminal 2 (UI)
```
