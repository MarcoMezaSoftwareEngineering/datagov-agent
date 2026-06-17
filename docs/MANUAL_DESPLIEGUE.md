# Manual de Despliegue e Implementación — DataGov Agent

Guía para instalar, configurar y ejecutar DataGov Agent en una PC local (Windows 11).
Para la demostración, ver [MANUAL_DEMO.md](MANUAL_DEMO.md).

> **Estructura de este manual**
> - **Parte A — Instalación desde cero** (primera vez): secciones 1–6.
> - **Parte B — Ejecución diaria** (ya instalado): sección 7.
> - **Puertos, verificación y troubleshooting**: secciones 8–11.

---

## 0. Conceptos previos (léelo)

- **`.venv`** = entorno virtual de Python (las librerías). **Obligatorio**. Se crea una sola vez.
- **`.env`** = archivo de configuración (modelo LLM, URL/puerto de Milvus, puerto de la API…).
  **Opcional**: sin él se usan los defaults de `app/config.py`. Son cosas **distintas**.

### Modos de ejecución
| Modo | Requiere | Qué obtienes |
| ---- | -------- | ------------ |
| **Completo** | Ollama + modelos + Milvus (Docker) | Narrativa con IA + RAG semántico real |
| **Degradado** | Solo Python/venv | Perfilado, calidad, MDM, score, reporte (sin IA) |

El sistema **degrada con elegancia**: sin Ollama usa narrativa determinista; sin Milvus el RAG de la
API queda deshabilitado pero el resto funciona y los tests corren igual.

---

# PARTE A — Instalación desde cero (primera vez)

## 1. Requisitos

| Componente | Versión | Nota |
| ---------- | ------- | ---- |
| Python | 3.11 | Usar `py -3.11` (no 3.14) |
| Docker Desktop | reciente | Solo para Milvus (RAG) |
| Ollama | instalado | Solo para LLM/embeddings reales |
| Git | cualquiera | Control de versiones |

## 2. Crear el entorno e instalar dependencias

```powershell
# (si aplica) git clone https://github.com/MarcoMezaSoftwareEngineering/datagov-agent.git
# cd datagov-agent

py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 3. Crear el `.env`

```powershell
Copy-Item .env.example .env
```

Variables clave:

| Variable | Default | Para qué |
| -------- | ------- | -------- |
| `LLM_MODEL` | `llama3.1:8b` | Modelo de chat (Ollama) |
| `EMBED_MODEL` | `nomic-embed-text` | Embeddings (RAG) |
| `EMBED_DIM` | `768` | Dim del modelo de embeddings |
| `MILVUS_URI` | `http://localhost:19530` | Conexión a Milvus |
| `API_PORT` | `8000` | Puerto del backend |
| `API_BASE_URL` | `http://localhost:8000` | URL que usa la UI para hablar con la API |
| `RAW_DIR` | `datagov_agent_dataset/data/raw` | **Fuente canónica de datos** |

> **Datos:** la fuente canónica es el paquete `datagov_agent_dataset/`. El script
> `python data/synthetic/generate_synthetic_data.py` es **opcional** (muestra pequeña); no hace falta.
>
> **Si el puerto 8000 está ocupado por otro proyecto** (ver sección 8), cambia en `.env`:
> `API_PORT=8001` y `API_BASE_URL=http://localhost:8001`.

## 4. Modelos de Ollama

```powershell
ollama list                       # ver qué tienes

ollama pull nomic-embed-text      # embeddings (RAG) — IMPRESCINDIBLE, ~270 MB

# LLM: opción A (sin descargas, usa lo que ya tienes):
(Get-Content .env) -replace 'LLM_MODEL=.*','LLM_MODEL=qwen3:8b' | Set-Content .env
# LLM: opción B (default, salida más limpia, ~5 GB):
# ollama pull llama3.1:8b
```

> Ollama suele arrancar solo como servicio. `EMBED_DIM` debe coincidir con el modelo (`nomic-embed-text` = 768).

## 5. Milvus (Docker)

```powershell
docker compose up -d
docker ps --filter name=datagov-milvus     # esperar "healthy"
```

## 6. Verificación de la instalación

```powershell
pytest                              # 25 tests verdes (Milvus se omite si no está)
python scripts/validate_dataset.py  # 22/22 métricas exactas vs ground truth
```

---

# PARTE B — Ejecución diaria (ya instalado)

Cuando ya hiciste la Parte A, **arrancar el sistema** es solo esto:

```powershell
# 1. Milvus (si no está arriba)
docker compose up -d

# 2. (Opcional) confirmar que Ollama corre — normalmente ya está como servicio

# 3. Backend — Terminal 1
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8001      # usa 8000 si está libre

# 4. Interfaz — Terminal 2
.\.venv\Scripts\Activate.ps1
streamlit run ui/streamlit_app.py
```

URLs:
- API: `http://localhost:8001` · Swagger: `http://localhost:8001/docs` · Salud: `/health`
- UI: `http://localhost:8501`

> La UI lee `API_BASE_URL` desde `.env`. Si corres la API en 8001, asegúrate de tener
> `API_BASE_URL=http://localhost:8001` en `.env` (así la UI apunta al backend correcto).

**Apagar al terminar:**
```powershell
# Ctrl+C en las terminales de uvicorn y streamlit
docker compose down                 # detiene Milvus (conserva ./volumes)
```

---

## 8. Puertos y conflictos (IMPORTANTE)

DataGov Agent usa: **8000** (API), **8501** (UI), **19530** (Milvus).

Si al abrir la UI ves *"API no disponible"* o un **error 404 con HTML de Django** (`core.urls`,
`api/v1/...`), significa que **otro proyecto ya ocupa el puerto 8000** (típico: un Django/Docker/WSL).
Tu FastAPI no llegó a tomar el puerto y la UI está hablando con la app equivocada.

**Diagnóstico:**
```powershell
Get-NetTCPConnection -LocalPort 8000 -State Listen | ForEach-Object {
  (Get-Process -Id $_.OwningProcess).ProcessName }
```

**Solución (recomendada): usa otro puerto, no toques el otro proyecto.**
```powershell
# en .env:
#   API_PORT=8001
#   API_BASE_URL=http://localhost:8001
uvicorn app.main:app --reload --port 8001
streamlit run ui/streamlit_app.py
```

> Alternativa rápida sin tocar `.env` (solo esa terminal):
> `$env:API_BASE_URL="http://localhost:8001"` antes de `streamlit run …`.

---

## 9. Verificación rápida del sistema

```powershell
curl http://localhost:8001/health          # ollama_available / milvus_available
pytest
python scripts/validate_dataset.py
```
La barra lateral de la UI también muestra el estado de Ollama y Milvus (✅/⚠️).

---

## 10. Atajos con `make` (opcional)

```
make install  make validate  make test  make api  make ui  make milvus-up  make milvus-down
```
En Windows sin `make`, usa los comandos equivalentes de las secciones anteriores.

---

## 11. Solución de problemas

| Síntoma | Causa | Solución |
| ------- | ----- | -------- |
| UI: "API no disponible" + **HTML 404 de Django** | El 8000 lo ocupa otro proyecto | Corre la API en `--port 8001` y pon `API_BASE_URL=http://localhost:8001` en `.env` (sección 8) |
| UI: "API no disponible" (sin HTML) | El backend no está arriba | Levanta `uvicorn app.main:app --reload --port 8001` |
| `/health` → `milvus_available: false` o RAG 503 | Milvus no corre | `docker compose up -d` y espera "healthy" |
| Error al ingestar documentos / embeddings | Falta `nomic-embed-text` | `ollama pull nomic-embed-text` |
| Narrativa vacía o genérica | LLM no disponible / modelo no descargado | Pulla el modelo o ajusta `LLM_MODEL` en `.env` |
| `model 'llama3.1:8b' not found` | Default no descargado | `ollama pull llama3.1:8b` o `LLM_MODEL=qwen3:8b` |
| Búsqueda RAG vacía tras indexar | Dim de embeddings ≠ colección | Re-indexa con "reset" (la UI lo hace) |
| `pytest` no encuentra `app` | Ejecutado fuera de la raíz | Corre `pytest` desde la carpeta del proyecto |

---

## 12. Cheat sheet

**Instalación (una vez):**
```powershell
py -3.11 -m venv .venv ; .\.venv\Scripts\Activate.ps1 ; pip install -r requirements.txt
Copy-Item .env.example .env
(Get-Content .env) -replace 'LLM_MODEL=.*','LLM_MODEL=qwen3:8b' | Set-Content .env
(Get-Content .env) -replace 'API_PORT=.*','API_PORT=8001' | Set-Content .env
(Get-Content .env) -replace 'API_BASE_URL=.*','API_BASE_URL=http://localhost:8001' | Set-Content .env
ollama pull nomic-embed-text
```

**Arranque diario:**
```powershell
docker compose up -d
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8001     # Terminal 1
streamlit run ui/streamlit_app.py             # Terminal 2
```
