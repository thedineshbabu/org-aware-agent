"""
Document ingestion API — POST /api/v1/ingest
Accepts file uploads (PDF, DOCX, TXT, MD) and stores chunks in document_chunks.
FTS column is auto-maintained by the database trigger.
"""
from __future__ import annotations

import io
import uuid
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.models import UserContext
from app.db.engine import get_db

logger = structlog.get_logger(__name__)
router = APIRouter(tags=["ingest"])

CHUNK_SIZE = 800      # characters per chunk
CHUNK_OVERLAP = 100  # character overlap between chunks


# ── Text extraction ───────────────────────────────────────────────────────────

def _extract_text_pdf(data: bytes) -> str:
    import pdfplumber
    text_parts = []
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text_parts.append(t)
    return "\n\n".join(text_parts)


def _extract_text_docx(data: bytes) -> str:
    from docx import Document
    doc = Document(io.BytesIO(data))
    return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())


def _extract_text_plain(data: bytes) -> str:
    return data.decode("utf-8", errors="replace")


def _extract_text(filename: str, data: bytes) -> str:
    ext = filename.rsplit(".", 1)[-1].lower()
    if ext == "pdf":
        return _extract_text_pdf(data)
    if ext == "docx":
        return _extract_text_docx(data)
    return _extract_text_plain(data)


# ── Chunking ──────────────────────────────────────────────────────────────────

def _chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += size - overlap
    return chunks


# ── Response model ────────────────────────────────────────────────────────────

class IngestResponse(BaseModel):
    doc_name: str
    chunks_inserted: int
    message: str


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.post("/ingest", response_model=IngestResponse)
async def ingest_document(
    current_user: Annotated[UserContext, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    file: UploadFile = File(...),
    doc_name: str = Form(""),
    section: str = Form(""),
    acl_roles: str = Form("employee"),
) -> IngestResponse:
    """
    Upload a document (PDF, DOCX, TXT, MD) and store it as searchable chunks.

    - **file**: The document to ingest
    - **doc_name**: Display name (defaults to filename)
    - **section**: Section or category label
    - **acl_roles**: Comma-separated roles that can access this document (default: employee)
    """
    allowed_extensions = {"pdf", "docx", "txt", "md"}
    filename = file.filename or "upload"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '.{ext}'. Allowed: {', '.join(sorted(allowed_extensions))}",
        )

    data = await file.read()
    if len(data) > 20 * 1024 * 1024:  # 20 MB limit
        raise HTTPException(status_code=400, detail="File exceeds 20 MB limit.")

    resolved_doc_name = doc_name.strip() or filename
    resolved_section = section.strip()
    roles = [r.strip() for r in acl_roles.split(",") if r.strip()] or ["employee"]

    try:
        raw_text = _extract_text(filename, data)
    except Exception as exc:
        logger.error("ingest_extract_failed", filename=filename, error=str(exc))
        raise HTTPException(status_code=422, detail=f"Failed to parse file: {exc}")

    if not raw_text.strip():
        raise HTTPException(status_code=422, detail="No text could be extracted from the file.")

    chunks = _chunk_text(raw_text)

    insert_sql = text("""
        INSERT INTO document_chunks
            (id, doc_name, section, url, chunk_text, acl_roles, acl_users)
        VALUES
            (:id, :doc_name, :section, :url, :chunk_text, :acl_roles, :acl_users)
    """)

    for chunk in chunks:
        await db.execute(insert_sql, {
            "id": str(uuid.uuid4()),
            "doc_name": resolved_doc_name,
            "section": resolved_section,
            "url": f"upload://{filename}",
            "chunk_text": chunk,
            "acl_roles": roles,
            "acl_users": [],
        })

    await db.commit()

    logger.info(
        "ingest_complete",
        doc_name=resolved_doc_name,
        chunks=len(chunks),
        uploaded_by=current_user.user_id,
    )

    return IngestResponse(
        doc_name=resolved_doc_name,
        chunks_inserted=len(chunks),
        message=f"Successfully ingested '{resolved_doc_name}' as {len(chunks)} searchable chunks.",
    )
