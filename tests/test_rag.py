"""Pruebas del RAG con InMemoryVectorStore + embeddings deterministas (sin Ollama ni Docker)."""

from __future__ import annotations

import pytest

from app.agents.rag_agent import NO_SUPPORT, answer_question, chunk_text, ingest_documents
from app.services.embeddings import HashingEmbeddings
from app.services.vector_store import InMemoryVectorStore, milvus_available

DOCS = [
    (
        "Se consideran datos personales el nombre, apellido, DNI, correo electronico, "
        "telefono y direccion. Estos campos deben clasificarse como dato personal.",
        "politica_datos_personales.md",
    ),
    (
        "Los cambios sobre datos maestros son aprobados por el Comite de Gobierno de Datos "
        "cuando tienen impacto transversal. El Data Owner aprueba los cambios rutinarios.",
        "procedimiento_cambios_datos_maestros.md",
    ),
    (
        "El DNI debe ser obligatorio, tener exactamente 8 digitos numericos y ser unico por cliente.",
        "manual_calidad_datos.md",
    ),
]


@pytest.fixture
def store():
    vs = InMemoryVectorStore(embeddings=HashingEmbeddings(dim=256))
    ingest_documents(vs, DOCS)
    return vs


def test_chunking_produces_chunks():
    chunks, metas = chunk_text("a" * 2000, "doc.md")
    assert len(chunks) >= 1
    assert all(m["source"] == "doc.md" for m in metas)


def test_ingest_counts(store):
    assert store.count() >= len(DOCS)


def test_rag_answers_with_sources(store):
    ans = answer_question(store, "Que campos se consideran datos personales?")
    assert ans.grounded is True
    assert ans.sources
    assert "personal" in ans.answer.lower() or "dni" in ans.answer.lower()


def test_rag_who_approves_master_data(store):
    ans = answer_question(store, "Quien aprueba cambios sobre datos maestros?")
    assert ans.grounded is True
    assert any("procedimiento" in s for s in ans.sources)


def test_rag_no_support_on_empty_store():
    empty = InMemoryVectorStore(embeddings=HashingEmbeddings(dim=256))
    ans = answer_question(empty, "Pregunta sin documentos")
    assert ans.grounded is False
    assert ans.answer == NO_SUPPORT


@pytest.mark.skipif(
    not milvus_available(), reason="Milvus no disponible (requiere docker compose up)"
)
def test_milvus_integration():
    from app.services.vector_store import MilvusVectorStore

    vs = MilvusVectorStore(embeddings=HashingEmbeddings(dim=256), collection="datagov_test")
    vs.reset()
    ingest_documents(vs, DOCS)
    ans = answer_question(vs, "Que campos se consideran datos personales?")
    assert ans.sources
    vs.reset()
