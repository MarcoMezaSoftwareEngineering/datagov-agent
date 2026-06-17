"""Configuración central del proyecto basada en variables de entorno (.env)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Raíz del repositorio (…/DataGov_agent)
ROOT_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    """Configuración tipada cargada desde el entorno / archivo .env."""

    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ----- Ollama / LLM -----
    ollama_base_url: str = "http://localhost:11434"
    llm_model: str = "llama3.1:8b"
    embed_model: str = "nomic-embed-text"
    llm_temperature: float = 0.1
    llm_timeout: int = 120

    # ----- Milvus -----
    milvus_uri: str = "http://localhost:19530"
    milvus_collection: str = "datagov_docs"
    embed_dim: int = 768

    # ----- RAG -----
    chunk_size: int = 800
    chunk_overlap: int = 120
    rag_top_k: int = 6

    # ----- Rutas -----
    # Fuente canónica: el paquete de datos validado `datagov_agent_dataset/`.
    data_dir: str = "data"
    raw_dir: str = "datagov_agent_dataset/data/raw"
    processed_dir: str = "data/processed"
    synthetic_dir: str = "data/synthetic"
    documents_dir: str = "datagov_agent_dataset/data/documents"
    reports_dir: str = "data/processed/reports"
    data_dictionary: str = "datagov_agent_dataset/data/raw/diccionario_datos.csv"
    expected_outputs: str = "datagov_agent_dataset/data/expected_outputs/known_issues_expected.json"

    # ----- API -----
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_base_url: str = "http://localhost:8000"

    # ---- Helpers de rutas absolutas ----
    def path(self, relative: str) -> Path:
        p = Path(relative)
        return p if p.is_absolute() else (ROOT_DIR / p)

    @property
    def raw_path(self) -> Path:
        return self.path(self.raw_dir)

    @property
    def processed_path(self) -> Path:
        return self.path(self.processed_dir)

    @property
    def synthetic_path(self) -> Path:
        return self.path(self.synthetic_dir)

    @property
    def documents_path(self) -> Path:
        return self.path(self.documents_dir)

    @property
    def reports_path(self) -> Path:
        return self.path(self.reports_dir)

    @property
    def data_dictionary_path(self) -> Path:
        return self.path(self.data_dictionary)

    @property
    def expected_outputs_path(self) -> Path:
        return self.path(self.expected_outputs)

    def ensure_dirs(self) -> None:
        """Crea las carpetas de datos si no existen."""
        for p in (
            self.raw_path,
            self.processed_path,
            self.synthetic_path,
            self.documents_path,
            self.reports_path,
        ):
            p.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    """Devuelve una instancia cacheada de Settings."""
    return Settings()


settings = get_settings()
