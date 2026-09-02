from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.config import settings
from app.database import get_db, AnalysisRecord
from app.report import generate_markdown_report, generate_html_report
from app.models import AnalysisResult, ExecutiveSummary, FinancialMetrics, RiskFinding, Citation

router = APIRouter()


@router.get("/report/{analysis_id}")
async def get_report(analysis_id: str, format: str = "markdown", db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AnalysisRecord).where(AnalysisRecord.id == analysis_id))
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Analysis not found")

    summary_text = record.summary or ""
    executive_summary = _reconstruct_summary(summary_text)

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


def _reconstruct_summary(text: str) -> ExecutiveSummary:
    """Parse the stored summary text to reconstruct ExecutiveSummary with all fields."""
    import re

    def _extract_after_label(label: str) -> str:
        pattern = rf'###?\s*{re.escape(label)}\s*\n(.+?)(?=###?\s|\Z)'
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        # Fallback: find label and grab next paragraph
        idx = text.lower().find(label.lower())
        if idx == -1:
            return ""
        end = text.find("\n\n", idx + len(label))
        if end == -1:
            end = min(len(text), idx + 500)
        return text[idx:idx + (end - idx)].strip()

    def _extract_list(label: str) -> list[str]:
        section = _extract_after_label(label)
        if not section:
            return []
        items = []
        for line in section.split("\n"):
            line = line.strip()
            line = re.sub(r'^[-•*]\s*', '', line)
            line = re.sub(r'^\d+\.\s*', '', line)
            line = re.sub(r'\*\*(.+?)\*\*', r'\1', line)
            if len(line) > 10:
                items.append(line)
        return items[:5]

    company_name = None
    name_match = re.search(r'(?:Company|Summary)\s*[-–]\s*(.+?)(?:\n|\*\*)', text)
    if name_match:
        company_name = name_match.group(1).strip().strip('*').strip()

    confidence = 0.5
    cleaned = re.sub(r'\*\*', '', text)
    conf_match = re.search(r'confidence\s*(?:score)?[:\s]*(\d+\.?\d*)', cleaned, re.IGNORECASE)
    if conf_match:
        val = float(conf_match.group(1))
        confidence = val if val <= 1.0 else val / 100.0

    return ExecutiveSummary(
        company_name=company_name,
        company_overview=_extract_after_label("Company Overview"),
        financial_health=_extract_after_label("Financial Health"),
        key_strengths=_extract_list("Strengths"),
        key_risks=_extract_list("Risks"),
        growth_opportunities=_extract_list("Opportunities"),
        recommendation=_extract_after_label("Recommendation"),
        confidence_score=confidence,
    )


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
