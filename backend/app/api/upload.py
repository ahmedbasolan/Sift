import uuid
import shutil
import tempfile
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db, DocumentRecord
from app.models import UploadResponse, DocumentType
from app.ingest import detect_doc_type, parse_document, chunk_pages
from app.embeddings import add_chunks_to_collection
from app.search import get_bm25_index
from app.config import settings

router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    doc_id = str(uuid.uuid4())
    filename = file.filename or "unknown"
    doc_type = detect_doc_type(filename)

    if doc_type == DocumentType.UNKNOWN:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {filename}")

    tmp_dir = Path(tempfile.mkdtemp())
    tmp_file = tmp_dir / filename

    try:
        with open(tmp_file, "wb") as f:
            content = await file.read()
            f.write(content)

        file_size = len(content)
        pages, page_count = parse_document(str(tmp_file), filename)
        chunks = chunk_pages(pages, settings.CHUNK_SIZE, settings.CHUNK_OVERLAP)

        chunk_count = add_chunks_to_collection(chunks, doc_id, filename)

        bm25 = get_bm25_index()
        bm25_chunks = [
            {"text": c["text"], "page_num": c["page_num"], "document_id": doc_id, "filename": filename}
            for c in chunks
        ]
        bm25.add(bm25_chunks)

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
            id=doc_id, filename=filename, doc_type=doc_type.value,
            file_size=0, status=f"error: {str(e)[:200]}",
        )
        db.add(record)
        await db.commit()
        raise HTTPException(status_code=500, detail=f"Failed to process {filename}: {str(e)}")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


@router.get("/documents")
async def list_documents(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    result = await db.execute(select(DocumentRecord).order_by(DocumentRecord.uploaded_at.desc()))
    docs = result.scalars().all()
    return [
        {
            "id": d.id, "filename": d.filename, "doc_type": d.doc_type,
            "file_size": d.file_size, "page_count": d.page_count,
            "chunk_count": d.chunk_count, "status": d.status,
            "uploaded_at": d.uploaded_at.isoformat() if d.uploaded_at else None,
        }
        for d in docs
    ]


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select, delete
    from app.embeddings import delete_document_chunks

    result = await db.execute(select(DocumentRecord).where(DocumentRecord.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    delete_document_chunks(doc_id)
    await db.execute(delete(DocumentRecord).where(DocumentRecord.id == doc_id))
    await db.commit()

    return {"message": f"Deleted {doc.filename}"}
