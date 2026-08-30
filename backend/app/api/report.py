from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db, AnalysisRecord
from app.report import generate_markdown_report, generate_html_report
from app.models import AnalysisResult, ExecutiveSummary, FinancialMetrics
from app.config import settings

router = APIRouter()


@router.get("/report/{analysis_id}")
async def get_report(analysis_id: str, format: str = "markdown", db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    result = await db.execute(select(AnalysisRecord).where(AnalysisRecord.id == analysis_id))
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Analysis not found")

    analysis = AnalysisResult(
        id=record.id,
        document_id=record.document_id,
        created_at=record.created_at,
        executive_summary=ExecutiveSummary(**record.summary) if isinstance(record.summary, dict) else ExecutiveSummary(
            company_overview=record.summary or "",
            financial_health="",
            key_strengths=[], key_risks=[], growth_opportunities=[],
            recommendation="", confidence_score=0.5,
        ),
        financial_metrics=FinancialMetrics(**record.financial_metrics) if record.financial_metrics else FinancialMetrics(),
        risks=[],
        sections=record.sections or [],
        metadata=record.analysis_metadata or {},
    )

    if format == "html":
        return {"content": generate_html_report(analysis), "type": "html"}
    return {"content": generate_markdown_report(analysis), "type": "markdown"}


@router.get("/health")
async def health_check():
    groq_status = "ok" if settings.GROQ_API_KEY else "no_key"
    return {
        "status": "ok",
        "version": settings.APP_VERSION,
        "groq": groq_status,
        "chromadb": "ok",
        "sqlite": "ok",
    }
