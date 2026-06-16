"""Embeddings: Ollama (nomic-embed-text) con fallback determinista para tests/sin-Ollama."""

from __future__ import annotations

import hashlib

import numpy as np

from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)


class EmbeddingBackend:
    """Interfaz común de embeddings."""

    dim: int

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]


class HashingEmbeddings(EmbeddingBackend):
    """Embedding determinista (bag-of-hashed-tokens) — no requiere modelos.

    Útil para tests y para que el RAG funcione aunque Ollama no esté disponible.
    No es semántico, pero permite recuperar por solapamiento de términos.
    """

    def __init__(self, dim: int | None = None) -> None:
        self.dim = dim or settings.embed_dim

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(t) for t in texts]

    def _embed(self, text: str) -> list[float]:
        vec = np.zeros(self.dim, dtype=np.float32)
        for token in (text or "").lower().split():
            h = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16)
            vec[h % self.dim] += 1.0
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec /= norm
        return vec.tolist()


class OllamaEmbeddingBackend(EmbeddingBackend):
    """Embeddings vía Ollama usando langchain-ollama."""

    def __init__(self) -> None:
        from langchain_ollama import OllamaEmbeddings

        self._client = OllamaEmbeddings(
            model=settings.embed_model, base_url=settings.ollama_base_url
        )
        self.dim = settings.embed_dim

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._client.embed_documents(texts)

    def embed_query(self, text: str) -> list[float]:
        return self._client.embed_query(text)


def ollama_available() -> bool:
    """Verifica rápidamente si el servidor Ollama responde."""
    try:
        import requests

        resp = requests.get(f"{settings.ollama_base_url}/api/tags", timeout=3)
        return resp.status_code == 200
    except Exception:
        return False


def get_embeddings(prefer_ollama: bool = True) -> EmbeddingBackend:
    """Devuelve el backend de embeddings disponible (Ollama o fallback determinista)."""
    if prefer_ollama and ollama_available():
        try:
            logger.info("Usando embeddings de Ollama: %s", settings.embed_model)
            return OllamaEmbeddingBackend()
        except Exception as exc:  # pragma: no cover - defensivo
            logger.warning(
                "Fallo al inicializar OllamaEmbeddings (%s); usando HashingEmbeddings", exc
            )
    logger.info("Usando HashingEmbeddings (determinista, sin Ollama)")
    return HashingEmbeddings()
