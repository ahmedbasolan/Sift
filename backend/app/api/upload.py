import re
import shutil
import tempfile
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import DocumentRecord, get_db
from app.embeddings import add_chunks_to_collection
from app.ingest import chunk_pages, detect_doc_type, parse_document
from app.models import DocumentType, UploadResponse
from app.search import get_bm25_index

router = APIRouter()

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


def _sanitize_filename(filename: str) -> str:
    """Remove path traversal and dangerous characters from filename."""
    filename = re.sub(r"[^\w\s\-\.]", "_", filename)
    filename = re.sub(r"_{2,}", "_", filename)
    return filename.strip("_") or "unknown"


@router.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    doc_id = str(uuid.uuid4())
    filename = _sanitize_filename(file.filename or "unknown")
    doc_type = detect_doc_type(filename)

    if doc_type == DocumentType.UNKNOWN:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {filename}")

    tmp_dir = Path(tempfile.mkdtemp())
    tmp_file = tmp_dir / filename

    try:
        content = await file.read()
        file_size = len(content)

        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large: {file_size / (1024 * 1024):.1f} MB (max 50 MB)",
            )

        with open(tmp_file, "wb") as f:
            f.write(content)
        pages, page_count = parse_document(str(tmp_file), filename)
        chunks = chunk_pages(pages, settings.CHUNK_SIZE, settings.CHUNK_OVERLAP)

        chunk_count = add_chunks_to_collection(chunks, doc_id, filename)

        bm25 = get_bm25_index()
        bm25_chunks = [
            {
                "text": c["text"],
                "page_num": c["page_num"],
                "document_id": doc_id,
                "filename": filename,
                "chunk_id": c["id"],
            }
            for c in chunks
        ]
        bm25.replace_document(doc_id, bm25_chunks)

        record = DocumentRecord(
            id=doc_id,
            filename=filename,
            doc_type=doc_type.value,
            file_size=file_size,
            page_count=page_count,
            chunk_count=chunk_count,
            status="ready",
        )
        db.add(record)
        await db.commit()

        return UploadResponse(
            id=doc_id,
            filename=filename,
            status="ready",
            chunks=chunk_count,
            message=f"Successfully processed {filename}: {page_count} pages, {chunk_count} chunks",
        )
    except HTTPException:
        raise
    except Exception as e:
        record = DocumentRecord(
            id=doc_id,
            filename=filename,
            doc_type=doc_type.value,
            file_size=0,
            status=f"error: {str(e)[:200]}",
        )
        db.add(record)
        await db.commit()
        raise HTTPException(
            status_code=500, detail=f"Failed to process {filename}: {str(e)}"
        ) from e
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


@router.get("/documents")
async def list_documents(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select

    result = await db.execute(select(DocumentRecord).order_by(DocumentRecord.uploaded_at.desc()))
    docs = result.scalars().all()
    return [
        {
            "id": d.id,
            "filename": d.filename,
            "doc_type": d.doc_type,
            "file_size": d.file_size,
            "page_count": d.page_count,
            "chunk_count": d.chunk_count,
            "status": d.status,
            "uploaded_at": d.uploaded_at.isoformat() if d.uploaded_at else None,
        }
        for d in docs
    ]


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import delete, select

    from app.database import AnalysisRecord
    from app.embeddings import delete_document_chunks
    from app.search import get_bm25_index

    result = await db.execute(select(DocumentRecord).where(DocumentRecord.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    delete_document_chunks(doc_id)
    get_bm25_index().remove_document(doc_id)
    await db.execute(delete(AnalysisRecord).where(AnalysisRecord.document_id == doc_id))
    await db.execute(delete(DocumentRecord).where(DocumentRecord.id == doc_id))
    await db.commit()

    return {"message": f"Deleted {doc.filename}"}
