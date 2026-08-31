from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db, AnalysisRecord
from app.report import generate_markdown_report, generate_html_report
from app.models import AnalysisResult, ExecutiveSummary, FinancialMetrics, RiskFinding, Citation

router = APIRouter()


@router.get("/report/{analysis_id}")
async def get_report(analysis_id: str, format: str = "markdown", db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    result = await db.execute(select(AnalysisRecord).where(AnalysisRecord.id == analysis_id))
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Analysis not found")

    # Parse summary from stored text
    summary_text = record.summary or ""
    executive_summary = ExecutiveSummary(
        company_overview=summary_text[:200] if summary_text else "",
        financial_health="",
        key_strengths=[],
        key_risks=[],
        growth_opportunities=[],
        recommendation="",
        confidence_score=0.5,
    )

    # Parse risks from stored JSON
    risks = []
    if record.risks and isinstance(record.risks, list):
        for r in record.risks:
            if isinstance(r, dict):
                try:
                    risks.append(RiskFinding(**r))
                except Exception:
                    pass

    analysis = AnalysisResult(
        id=record.id,
        document_id=record.document_id,
        created_at=record.created_at,
        executive_summary=executive_summary,
        financial_metrics=FinancialMetrics(**record.financial_metrics) if record.financial_metrics else FinancialMetrics(),
        risks=risks,
        sections=record.sections or [],
        metadata={},
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


from app.config import settings
