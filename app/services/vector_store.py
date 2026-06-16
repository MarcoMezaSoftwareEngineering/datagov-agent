"""Vector store: Milvus (vía Docker) + InMemoryVectorStore para tests sin Docker."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from app.config import settings
from app.services.embeddings import EmbeddingBackend, get_embeddings
from app.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class RetrievedChunk:
    """Fragmento recuperado del vector store."""

    text: str
    source: str = ""
    score: float = 0.0
    metadata: dict = field(default_factory=dict)


class BaseVectorStore:
    """Interfaz común de los vector stores."""

    def add_documents(self, texts: list[str], metadatas: list[dict] | None = None) -> int:
        raise NotImplementedError

    def similarity_search(self, query: str, k: int | None = None) -> list[RetrievedChunk]:
        raise NotImplementedError

    def count(self) -> int:
        raise NotImplementedError

    def reset(self) -> None:
        raise NotImplementedError


# --------------------------------------------------------------------------- in-memory


class InMemoryVectorStore(BaseVectorStore):
    """Vector store en memoria (cosine) — usado por los tests y como modo degradado."""

    def __init__(self, embeddings: EmbeddingBackend | None = None) -> None:
        self.embeddings = embeddings or get_embeddings()
        self._vectors: list[np.ndarray] = []
        self._texts: list[str] = []
        self._metadatas: list[dict] = []

    def add_documents(self, texts: list[str], metadatas: list[dict] | None = None) -> int:
        metadatas = metadatas or [{} for _ in texts]
        vecs = self.embeddings.embed_documents(texts)
        for text, vec, meta in zip(texts, vecs, metadatas, strict=False):
            self._texts.append(text)
            self._vectors.append(_unit(np.asarray(vec, dtype=np.float32)))
            self._metadatas.append(meta or {})
        return len(texts)

    def similarity_search(self, query: str, k: int | None = None) -> list[RetrievedChunk]:
        k = k or settings.rag_top_k
        if not self._vectors:
            return []
        q = _unit(np.asarray(self.embeddings.embed_query(query), dtype=np.float32))
        sims = np.array([float(np.dot(q, v)) for v in self._vectors])
        top = np.argsort(-sims)[:k]
        return [
            RetrievedChunk(
                text=self._texts[i],
                source=str(self._metadatas[i].get("source", "")),
                score=float(sims[i]),
                metadata=self._metadatas[i],
            )
            for i in top
        ]

    def count(self) -> int:
        return len(self._texts)

    def reset(self) -> None:
        self._vectors.clear()
        self._texts.clear()
        self._metadatas.clear()


# --------------------------------------------------------------------------- milvus


class MilvusVectorStore(BaseVectorStore):
    """Vector store respaldado por Milvus standalone (Docker)."""

    def __init__(
        self,
        embeddings: EmbeddingBackend | None = None,
        uri: str | None = None,
        collection: str | None = None,
    ) -> None:
        from pymilvus import MilvusClient

        self.embeddings = embeddings or get_embeddings()
        self.uri = uri or settings.milvus_uri
        self.collection = collection or settings.milvus_collection
        self.client = MilvusClient(uri=self.uri)
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        if not self.client.has_collection(self.collection):
            self.client.create_collection(
                collection_name=self.collection,
                dimension=self.embeddings.dim,
                metric_type="COSINE",
                auto_id=True,
                enable_dynamic_field=True,
            )
            logger.info(
                "Colección Milvus creada: %s (dim=%d)", self.collection, self.embeddings.dim
            )

    def add_documents(self, texts: list[str], metadatas: list[dict] | None = None) -> int:
        metadatas = metadatas or [{} for _ in texts]
        vecs = self.embeddings.embed_documents(texts)
        rows = []
        for text, vec, meta in zip(texts, vecs, metadatas, strict=False):
            row = {"vector": vec, "text": text, "source": str(meta.get("source", ""))}
            row.update({k: v for k, v in (meta or {}).items() if k != "source"})
            rows.append(row)
        self.client.insert(collection_name=self.collection, data=rows)
        return len(rows)

    def similarity_search(self, query: str, k: int | None = None) -> list[RetrievedChunk]:
        k = k or settings.rag_top_k
        q = self.embeddings.embed_query(query)
        results = self.client.search(
            collection_name=self.collection,
            data=[q],
            limit=k,
            output_fields=["text", "source"],
            search_params={"metric_type": "COSINE"},
        )
        chunks: list[RetrievedChunk] = []
        for hit in results[0]:
            entity = hit.get("entity", {})
            chunks.append(
                RetrievedChunk(
                    text=entity.get("text", ""),
                    source=entity.get("source", ""),
                    score=float(hit.get("distance", 0.0)),
                    metadata=entity,
                )
            )
        return chunks

    def count(self) -> int:
        try:
            stats = self.client.get_collection_stats(self.collection)
            return int(stats.get("row_count", 0))
        except Exception:
            return 0

    def reset(self) -> None:
        if self.client.has_collection(self.collection):
            self.client.drop_collection(self.collection)
        self._ensure_collection()


# --------------------------------------------------------------------------- factory


def milvus_available(uri: str | None = None) -> bool:
    """Comprueba si Milvus está accesible."""
    try:
        from pymilvus import MilvusClient

        client = MilvusClient(uri=uri or settings.milvus_uri)
        client.list_collections()
        return True
    except Exception:
        return False


def get_vector_store(
    embeddings: EmbeddingBackend | None = None, backend: str = "milvus"
) -> BaseVectorStore:
    """Devuelve el vector store configurado.

    backend='milvus' (por defecto, requiere Docker) o 'memory' (tests/modo degradado).
    Si se pide Milvus y no está disponible, lanza un error claro y accionable.
    """
    embeddings = embeddings or get_embeddings()
    if backend == "memory":
        return InMemoryVectorStore(embeddings)
    if not milvus_available():
        raise RuntimeError(
            "Milvus no está disponible en "
            f"{settings.milvus_uri}. Levántalo con 'docker compose up -d' antes de usar el RAG."
        )
    return MilvusVectorStore(embeddings)


def _unit(vec: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(vec)
    return vec / norm if norm > 0 else vec
