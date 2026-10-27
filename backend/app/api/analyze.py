from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.analysis import run_analysis
from app.database import DocumentRecord, get_db
from app.llm import LLMUnavailable

router = APIRouter()


@router.post("/analyze/{document_id}")
async def analyze_document(document_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DocumentRecord).where(DocumentRecord.id == document_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if doc.status != "ready":
        raise HTTPException(status_code=400, detail=f"Document not ready: {doc.status}")

    try:
        analysis = await run_analysis(document_id, db)
        return analysis.model_dump()
    except LLMUnavailable as e:
        # Nothing is saved: an analysis without the LLM would be placeholder text.
        raise HTTPException(status_code=503, detail=f"Analysis needs the LLM. {e}") from e
    except Exception as e:
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}") from e


@router.get("/analyses")
async def list_analyses(db: AsyncSession = Depends(get_db)):
    from app.database import AnalysisRecord

    result = await db.execute(select(AnalysisRecord).order_by(AnalysisRecord.created_at.desc()))
    records = result.scalars().all()
    return [
        {
            "id": r.id,
            "document_id": r.document_id,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "summary_preview": (r.summary or "")[:200],
        }
        for r in records
    ]


@router.get("/analyses/{analysis_id}")
async def get_analysis(analysis_id: str, db: AsyncSession = Depends(get_db)):
    from app.database import AnalysisRecord

    result = await db.execute(select(AnalysisRecord).where(AnalysisRecord.id == analysis_id))
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return {
        "id": record.id,
        "document_id": record.document_id,
        "created_at": record.created_at.isoformat() if record.created_at else None,
        "summary": record.summary,
        "financial_metrics": record.financial_metrics,
        "risks": record.risks,
        "sections": record.sections,
    }
