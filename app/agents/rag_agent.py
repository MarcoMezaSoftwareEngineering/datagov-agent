"""RAG Policy Agent: chunking, ingestión, recuperación y respuesta con fuentes (Módulo 6)."""

from __future__ import annotations

import re

from app.agents.prompts import RAG_SYSTEM
from app.config import settings
from app.schemas.quality_schema import RagAnswer
from app.services.llm import get_llm
from app.services.vector_store import BaseVectorStore, RetrievedChunk
from app.utils.text_cleaning import extract_json

NO_SUPPORT = "No se encontró sustento suficiente en los documentos cargados."


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
    chunks = store.similarity_search(question, k=top_k or settings.rag_top_k)
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


def _unique_sources(chunks: list[RetrievedChunk]) -> list[str]:
    seen, out = set(), []
    for c in chunks:
        if c.source and c.source not in seen:
            seen.add(c.source)
            out.append(c.source)
    return out


def _format_context(chunks: list[RetrievedChunk]) -> str:
    return "\n\n".join(f"[Fuente: {c.source}]\n{c.text}" for c in chunks)
