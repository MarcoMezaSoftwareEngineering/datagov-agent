"""Punto de entrada FastAPI de DataGov Agent."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api import routes_data, routes_rag, routes_reports
from app.config import settings
from app.services.embeddings import ollama_available
from app.services.vector_store import milvus_available
from app.utils.logging import configure_logging

configure_logging()

app = FastAPI(
    title="DataGov Agent API",
    description="Asistente agéntico local para gobierno, calidad, MDM y catalogación de datos.",
    version=__version__,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_data.router)
app.include_router(routes_rag.router)
app.include_router(routes_reports.router)


@app.on_event("startup")
def _startup() -> None:
    settings.ensure_dirs()


@app.get("/", tags=["health"])
def root() -> dict:
    return {
        "name": "DataGov Agent",
        "version": __version__,
        "docs": "/docs",
        "status": "ok",
    }


@app.get("/health", tags=["health"])
def health() -> dict:
    """Estado de las dependencias locales (Ollama, Milvus)."""
    return {
        "status": "ok",
        "ollama_available": ollama_available(),
        "ollama_model": settings.llm_model,
        "milvus_available": milvus_available(),
        "milvus_uri": settings.milvus_uri,
    }
