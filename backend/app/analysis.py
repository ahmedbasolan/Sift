import json
import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import (
    AnalysisResult, ExecutiveSummary, FinancialMetrics,
    RiskFinding, RiskCategory, RiskLevel, Citation, Document,
)
from app.database import DocumentRecord, AnalysisRecord
from app.search import hybrid_search
from app.llm import generate_summary, extract_financial_metrics, assess_risks
from app.config import settings


async def run_analysis(document_id: str, db: AsyncSession) -> AnalysisResult:
    from sqlalchemy import select
    result = await db.execute(select(DocumentRecord).where(DocumentRecord.id == document_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise ValueError(f"Document {document_id} not found")

    all_chunks = hybrid_search("*", top_k=50)
    doc_chunks = [c for c in all_chunks if c.get("metadata", {}).get("document_id") == document_id]

    if not doc_chunks:
        all_chunks = hybrid_search("financial report analysis", top_k=50)
        doc_chunks = [c for c in all_chunks if c.get("metadata", {}).get("document_id") == document_id]

    context = "\n\n".join(
        f"[Source: {c['metadata'].get('filename', 'unknown')}, Page {c['metadata'].get('page_num', '?')}]\n{c['text']}"
        for c in doc_chunks[:15]
    )

    if not context.strip():
        context = "No document content available for analysis."

    summary_text = await generate_summary(context)
    metrics_text = await extract_financial_metrics(context)
    risks_text = await assess_risks(context)

    executive_summary = _parse_summary(summary_text)
    financial_metrics = _parse_metrics(metrics_text)
    risks = _parse_risks(risks_text)

    analysis_id = str(uuid.uuid4())
    analysis = AnalysisResult(
        id=analysis_id,
        document_id=document_id,
        created_at=datetime.utcnow(),
        executive_summary=executive_summary,
        financial_metrics=financial_metrics,
        risks=risks,
        sections=[],
        metadata={"chunk_count": len(doc_chunks), "context_length": len(context)},
    )

    record = AnalysisRecord(
        id=analysis_id,
        document_id=document_id,
        summary=summary_text,
        financial_metrics=financial_metrics.model_dump(),
        risks=[r.model_dump() for r in risks],
        sections=[],
    )
    db.add(record)
    await db.commit()

    return analysis


def _parse_summary(text: str) -> ExecutiveSummary:
    return ExecutiveSummary(
        company_overview=_extract_section(text, "overview") or text[:200],
        financial_health=_extract_section(text, "financial health") or "Analysis pending",
        key_strengths=_extract_list(text, "strengths"),
        key_risks=_extract_list(text, "risks"),
        growth_opportunities=_extract_list(text, "opportunities"),
        recommendation=_extract_section(text, "recommendation") or "Further analysis recommended",
        confidence_score=0.5,
    )


def _parse_metrics(text: str) -> FinancialMetrics:
    try:
        data = json.loads(text)
        return FinancialMetrics(**{k: v for k, v in data.items() if k in FinancialMetrics.model_fields})
    except (json.JSONDecodeError, TypeError):
        return FinancialMetrics()


def _parse_risks(text: str) -> list[RiskFinding]:
    try:
        data = json.loads(text)
        if not isinstance(data, list):
            return []
        risks = []
        for item in data:
            try:
                risks.append(RiskFinding(
                    category=RiskCategory(item.get("category", "operational")),
                    title=item.get("title", "Unknown risk"),
                    description=item.get("description", ""),
                    severity=RiskLevel(item.get("severity", "medium")),
                    evidence=[
                        Citation(text=e.get("text", ""), source="document", trust_level=e.get("trust_level", "inference"))
                        for e in item.get("evidence", [])
                    ],
                    recommendation=item.get("recommendation", ""),
                ))
            except (ValueError, KeyError):
                continue
        return risks
    except (json.JSONDecodeError, TypeError):
        return []


def _extract_section(text: str, keyword: str) -> str:
    lower = text.lower()
    idx = lower.find(keyword.lower())
    if idx == -1:
        return ""
    start = text.rfind("\n", 0, idx)
    start = max(0, start)
    end = text.find("\n", idx + len(keyword))
    if end == -1:
        end = min(len(text), idx + 500)
    return text[start:end].strip()


def _extract_list(text: str, keyword: str) -> list[str]:
    section = _extract_section(text, keyword)
    if not section:
        return []
    items = []
    for line in section.split("\n"):
        line = line.strip()
        if line.startswith(("-", "•", "*")) or (len(line) > 3 and line[0].isdigit()):
            item = line.lstrip("-•*0123456789. ").strip()
            if item:
                items.append(item)
    return items[:5]
