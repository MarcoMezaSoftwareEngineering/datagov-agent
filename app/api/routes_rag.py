"""Endpoints RAG: ingestión de documentos y preguntas (Milvus)."""

from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from app.agents import rag_agent
from app.api.store import store
from app.config import settings
from app.schemas.quality_schema import RagAnswer
from app.services.data_loader import extract_text
from app.services.vector_store import milvus_available

router = APIRouter(prefix="/rag", tags=["rag"])


class AskRequest(BaseModel):
    question: str
    top_k: int | None = None


class IngestDefaultRequest(BaseModel):
    reset: bool = False


@router.get("/status")
def status() -> dict:
    available = milvus_available()
    count = 0
    if available:
        try:
            count = store.get_vector_store().count()
        except Exception:
            count = 0
    return {
        "milvus_available": available,
        "milvus_uri": settings.milvus_uri,
        "collection": settings.milvus_collection,
        "indexed_chunks": count,
    }


@router.post("/ingest")
async def ingest(files: list[UploadFile] = File(...)) -> dict:
    """Indexa documentos subidos (PDF/TXT/MD/DOCX) en Milvus."""
    vs = _vector_store()
    documents: list[tuple[str, str]] = []
    for f in files:
        content = await f.read()
        try:
            text = extract_text(content, f.filename or "doc.txt")
        except Exception as exc:
            raise HTTPException(
                status_code=400, detail=f"Error extrayendo texto de {f.filename}: {exc}"
            ) from exc
        documents.append((text, f.filename or "doc"))
    n = rag_agent.ingest_documents(vs, documents)
    return {"ingested_files": len(documents), "ingested_chunks": n}


@router.post("/ingest-default")
def ingest_default(req: IngestDefaultRequest) -> dict:
    """Indexa todos los documentos de data/documents/."""
    vs = _vector_store()
    if req.reset:
        vs.reset()
    docs_dir = settings.documents_path
    if not docs_dir.exists():
        raise HTTPException(status_code=404, detail=f"No existe la carpeta {docs_dir}")
    documents = []
    for path in sorted(docs_dir.glob("*")):
        if path.suffix.lower() in (".md", ".txt", ".pdf", ".docx"):
            documents.append((extract_text(path.read_bytes(), path.name), path.name))
    if not documents:
        raise HTTPException(status_code=404, detail="No se encontraron documentos para indexar.")
    n = rag_agent.ingest_documents(vs, documents)
    return {"ingested_files": len(documents), "ingested_chunks": n}


@router.post("/ask", response_model=RagAnswer)
def ask(req: AskRequest) -> RagAnswer:
    vs = _vector_store()
    return rag_agent.answer_question(vs, req.question, top_k=req.top_k)


def _vector_store():
    try:
        return store.get_vector_store()
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc
