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
| `MILVUS_URI` | `http://localhost:19533` | Conexión a Milvus |
| `API_PORT` | `8010` | Puerto del backend |
| `API_BASE_URL` | `http://localhost:8010` | URL que usa la UI para hablar con la API |
| `RAW_DIR` | `datagov_agent_dataset/data/raw` | **Fuente canónica de datos** |

> **Datos:** la fuente canónica es el paquete `datagov_agent_dataset/`. El script
> `python data/synthetic/generate_synthetic_data.py` es **opcional** (muestra pequeña); no hace falta.
>
> **Puertos dedicados:** DataGov usa un bloque propio (**8010** API · **8510** UI · **19533** Milvus)
> para no chocar con otros proyectos. Ya vienen configurados en `.env.example`. Si aun así algún
> puerto estuviera ocupado, cámbialo en `.env` y al lanzar la UI/Milvus (ver sección 8).

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
uvicorn app.main:app --reload --port 8010

# 4. Interfaz — Terminal 2
.\.venv\Scripts\Activate.ps1
streamlit run ui/streamlit_app.py --server.port 8510
```

URLs:
- API: `http://localhost:8010` · Swagger: `http://localhost:8010/docs` · Salud: `/health`
- UI: `http://localhost:8510`

> La UI lee `API_BASE_URL` desde `.env`; con el bloque dedicado ya viene
> `API_BASE_URL=http://localhost:8010` (así la UI apunta al backend correcto).

**Apagar al terminar:**
```powershell
# Ctrl+C en las terminales de uvicorn y streamlit
docker compose down                 # detiene Milvus (conserva ./volumes)
```

---

## 8. Puertos y conflictos (IMPORTANTE)

DataGov Agent usa un **bloque de puertos dedicado** para no chocar con otros proyectos:

| Servicio | Puerto |
| -------- | ------ |
| API (FastAPI) | **8010** |
| UI (Streamlit) | **8510** |
| Milvus (gRPC) | **19533** |
| Milvus health · MinIO API/consola | 9093 · 9010 / 9011 |

Si al abrir la UI ves **otra aplicación** (por ejemplo, el Streamlit de otro proyecto) o
*"API no disponible"*, es que **otro proceso ya ocupa ese puerto**. Diagnóstico:

```powershell
netstat -ano | Select-String ":8510\s"                        # ¿quién usa el puerto de la UI?
Get-CimInstance Win32_Process -Filter "name='python.exe'" |
  Select-Object ProcessId, CommandLine                         # ver de qué proyecto es
```

**Solución (recomendada): usa el bloque dedicado o un puerto libre; no toques el otro proyecto.**
```powershell
uvicorn app.main:app --reload --port 8010
streamlit run ui/streamlit_app.py --server.port 8510
```

> Para liberar un puerto ocupado por otro servidor de desarrollo:
> `Stop-Process -Id <PID> -Force` (reversible: se reinicia relanzando ese proyecto).

---

## 9. Verificación rápida del sistema

```powershell
curl http://localhost:8010/health          # ollama_available / milvus_available
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
| UI muestra **otra app** (otro Streamlit) | Otro proyecto ocupa el puerto de la UI | Usa la UI en **8510** o cierra el otro servidor (sección 8) |
| UI: "API no disponible" | El backend no está arriba | Levanta `uvicorn app.main:app --reload --port 8010` |
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
ollama pull nomic-embed-text
```

**Arranque diario:**
```powershell
docker compose up -d
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8010              # Terminal 1
streamlit run ui/streamlit_app.py --server.port 8510   # Terminal 2
```
