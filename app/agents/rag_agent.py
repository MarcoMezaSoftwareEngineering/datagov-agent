"""RAG Policy Agent: chunking, ingestión, recuperación y respuesta con fuentes (Módulo 6)."""

from __future__ import annotations

import re

from app.agents.prompts import RAG_SYSTEM
from app.config import settings
from app.schemas.quality_schema import RagAnswer
from app.services.llm import get_llm
from app.services.vector_store import BaseVectorStore, RetrievedChunk
from app.utils.text_cleaning import extract_json, strip_accents

NO_SUPPORT = "No se encontró sustento suficiente en los documentos cargados."

# Referencias exactas tipo "artículo 16", "art. 16", "articulo 16" (la búsqueda
# vectorial no las discrimina bien; se refuerzan con recuperación léxica).
_ARTICLE_RE = re.compile(r"art(?:iculo)?s?\.?\s*(\d+)", re.IGNORECASE)


def chunk_text(text: str, source: str) -> tuple[list[str], list[dict]]:
    """Divide el texto en fragmentos con metadata de fuente."""
    chunks = _split(text)
    metadatas = [{"source": source, "chunk_id": i} for i in range(len(chunks))]
    return chunks, metadatas


def _split(text: str) -> list[str]:
    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        return [c for c in splitter.split_text(text) if c.strip()]
    except Exception:
        return _naive_split(text, settings.chunk_size, settings.chunk_overlap)


def _naive_split(text: str, size: int, overlap: int) -> list[str]:
    text = re.sub(r"\s+\n", "\n", text)
    chunks, start = [], 0
    while start < len(text):
        end = min(len(text), start + size)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += max(1, size - overlap)
    return chunks


def ingest_documents(store: BaseVectorStore, documents: list[tuple[str, str]]) -> int:
    """Indexa documentos (text, source) en el vector store. Devuelve nº de chunks."""
    total = 0
    for text, source in documents:
        chunks, metas = chunk_text(text, source)
        if chunks:
            store.add_documents(chunks, metas)
            total += len(chunks)
    return total


def answer_question(store: BaseVectorStore, question: str, top_k: int | None = None) -> RagAnswer:
    """Responde una pregunta usando RAG estricto (no inventa; cita fuentes)."""
    k = top_k or settings.rag_top_k
    chunks = store.similarity_search(question, k=k)
    # Búsqueda híbrida: refuerza con fragmentos que mencionan literalmente una
    # referencia exacta de la pregunta (p. ej. "artículo 16"), que el vector no recupera.
    chunks = _augment_with_keywords(store, question, chunks, k)
    if not chunks:
        return RagAnswer(question=question, answer=NO_SUPPORT, grounded=False, confidence="baja")

    sources = _unique_sources(chunks)
    context = _format_context(chunks)

    llm = get_llm()
    if llm.available:
        user = f"Pregunta: {question}\n\nContexto recuperado:\n{context}"
        raw = llm.complete(RAG_SYSTEM, user, json_mode=True)
        data = extract_json(raw) if raw else None
        if isinstance(data, dict) and data.get("answer"):
            answer = str(data["answer"]).strip()
            grounded = NO_SUPPORT.lower()[:30] not in answer.lower()
            return RagAnswer(
                question=question,
                answer=answer,
                rationale=str(data.get("rationale", "")),
                sources=sources if grounded else [],
                confidence=str(data.get("confidence", "media")),
                grounded=grounded,
            )

    # Fallback extractivo sin LLM
    return _extractive_answer(question, chunks, sources)


def _extractive_answer(
    question: str, chunks: list[RetrievedChunk], sources: list[str]
) -> RagAnswer:
    best = chunks[0]
    sentences = re.split(r"(?<=[.!?])\s+", best.text)
    q_terms = set(re.findall(r"\w+", question.lower()))
    ranked = sorted(
        sentences,
        key=lambda s: len(q_terms & set(re.findall(r"\w+", s.lower()))),
        reverse=True,
    )
    snippet = " ".join(ranked[:2]).strip() or best.text[:300]
    confidence = "media" if best.score > 0.15 else "baja"
    return RagAnswer(
        question=question,
        answer=snippet,
        rationale="Respuesta extraída directamente de los documentos recuperados (modo sin LLM).",
        sources=sources,
        confidence=confidence,
        grounded=True,
    )


def _augment_with_keywords(
    store: BaseVectorStore, question: str, chunks: list[RetrievedChunk], k: int
) -> list[RetrievedChunk]:
    """Antepone fragmentos que mencionan literalmente la referencia exacta de la pregunta."""
    numbers = set(_ARTICLE_RE.findall(strip_accents(question).lower()))
    if not numbers:
        return chunks

    # Variantes de "artículo N" como aparece en el texto (con/sin acento y mayúsculas),
    # sin la 'A' inicial para tolerar mayúscula/minúscula.
    contains: list[str] = []
    for n in numbers:
        for stem in ("rtículo", "rticulo", "RTÍCULO", "RTICULO", "rt. ", "rt "):
            contains.append(f"{stem} {n}" if not stem.endswith(" ") else f"{stem}{n}")

    try:
        kw_hits = store.keyword_search(contains, limit=k)
    except Exception:
        kw_hits = []

    # Precisión: conservar solo los que realmente referencian el número exacto (límite de palabra).
    precise = []
    for c in kw_hits:
        norm = strip_accents(c.text).lower()
        if any(re.search(rf"art(?:iculo)?s?\.?\s*{n}\b", norm) for n in numbers):
            precise.append(c)

    if not precise:
        return chunks

    # Fusiona: primero los aciertos léxicos, luego los vectoriales, sin duplicar.
    merged: list[RetrievedChunk] = []
    seen_texts: set[str] = set()
    for c in precise + chunks:
        key = c.text[:200]
        if key not in seen_texts:
            seen_texts.add(key)
            merged.append(c)
    return merged[: k + len(precise)]


def _unique_sources(chunks: list[RetrievedChunk]) -> list[str]:
    seen, out = set(), []
    for c in chunks:
        if c.source and c.source not in seen:
            seen.add(c.source)
            out.append(c.source)
    return out


def _format_context(chunks: list[RetrievedChunk]) -> str:
    return "\n\n".join(f"[Fuente: {c.source}]\n{c.text}" for c in chunks)
