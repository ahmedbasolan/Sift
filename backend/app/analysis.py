import json
import re
import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import (
    AnalysisResult, ExecutiveSummary, FinancialMetrics,
    RiskFinding, RiskCategory, RiskLevel, Citation,
)
from app.database import DocumentRecord, AnalysisRecord
from app.search import hybrid_search
from app.llm import generate_summary, extract_financial_metrics, assess_risks


async def run_analysis(document_id: str, db: AsyncSession) -> AnalysisResult:
    from sqlalchemy import select
    result = await db.execute(select(DocumentRecord).where(DocumentRecord.id == document_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise ValueError(f"Document {document_id} not found")

    # Search specifically for this document's chunks
    doc_chunks = hybrid_search(
        "financial report analysis document " + doc.filename,
        top_k=50,
        where={"document_id": document_id},
    )

    # Fallback: broader search filtered by document_id
    if not doc_chunks:
        doc_chunks = hybrid_search(
            "revenue growth risk financial summary",
            top_k=50,
            where={"document_id": document_id},
        )

    context = "\n\n".join(
        f"[Source: {c.get('metadata', {}).get('filename', 'unknown')}, Page {c.get('metadata', {}).get('page_num', '?')}]\n{c['text']}"
        for c in doc_chunks[:15]
    )

    if not context.strip():
        context = f"Document: {doc.filename}. No extractable text content available for analysis."

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
    company_name = None
    name_match = re.search(r'(?:Executive Summary|Summary)\s*[-–]\s*(.+?)(?:\n|\*\*)', text)
    if name_match:
        company_name = name_match.group(1).strip().strip('*').strip()

    return ExecutiveSummary(
        company_name=company_name,
        company_overview=_extract_table_section(text, "Company Overview") or _extract_section(text, "overview") or text[:300],
        financial_health=_extract_table_section(text, "Financial Health") or _extract_section(text, "financial health") or "Analysis pending",
        key_strengths=_extract_bullet_list(text, "Strengths"),
        key_risks=_extract_bullet_list(text, "Risks"),
        growth_opportunities=_extract_bullet_list(text, "Opportunities"),
        recommendation=_extract_table_section(text, "Recommendation") or _extract_section(text, "recommendation") or "Further analysis recommended",
        confidence_score=_extract_confidence(text),
    )


def _extract_table_section(text: str, label: str) -> str:
    pattern = rf'\|\s*\*\*[^|]*?{re.escape(label)}[^|]*?\*\*\s*\|(.+?)\|'
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if match:
        cell = match.group(1).strip()
        cell = re.sub(r'<br\s*/?>', '\n', cell)
        cell = re.sub(r'\*\*(.+?)\*\*', r'\1', cell)
        cell = re.sub(r'\*(.+?)\*', r'\1', cell)
        return cell.strip()
    return ""


def _extract_bullet_list(text: str, label: str) -> list[str]:
    section = _extract_table_section(text, label)
    if not section:
        section = _extract_section(text, label.lower())
    if not section:
        return []
    items = []
    for line in section.split("\n"):
        line = line.strip()
        line = re.sub(r'^\d+\.\s*', '', line)
        line = re.sub(r'^[-•*]\s*', '', line)
        line = re.sub(r'\*\*(.+?)\*\*', r'\1', line)
        line = re.sub(r'<br\s*/?>', '\n', line)
        line = line.strip()
        if len(line) > 10:
            items.append(line)
    return items[:5]


def _extract_confidence(text: str) -> float:
    cleaned = re.sub(r'\*\*', '', text)
    match = re.search(r'confidence\s*(?:score)?[:\s]*(\d+\.?\d*)', cleaned, re.IGNORECASE)
    if match:
        val = float(match.group(1))
        return val if val <= 1.0 else val / 100.0
    return 0.5


def _parse_metrics(text: str) -> FinancialMetrics:
    try:
        # Try to extract JSON from response (may be wrapped in markdown code block)
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
            cleaned = cleaned.rsplit("```", 1)[0]
        data = json.loads(cleaned)
        if isinstance(data, dict):
            return FinancialMetrics(**{k: v for k, v in data.items() if k in FinancialMetrics.model_fields})
    except (json.JSONDecodeError, TypeError, ValueError):
        pass
    return FinancialMetrics()


def _parse_risks(text: str) -> list[RiskFinding]:
    try:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
            cleaned = cleaned.rsplit("```", 1)[0]
        data = json.loads(cleaned)
        if not isinstance(data, list):
            return []
        risks = []
        for item in data:
            if not isinstance(item, dict):
                continue
            try:
                cat_str = item.get("category", "operational")
                if cat_str not in [c.value for c in RiskCategory]:
                    cat_str = "operational"
                sev_str = item.get("severity", "medium")
                if sev_str not in [s.value for s in RiskLevel]:
                    sev_str = "medium"
                risks.append(RiskFinding(
                    category=RiskCategory(cat_str),
                    title=item.get("title", "Unknown risk"),
                    description=item.get("description", ""),
                    severity=RiskLevel(sev_str),
                    evidence=[
                        Citation(text=e.get("text", ""), source="document", trust_level=e.get("trust_level", "inference"))
                        for e in item.get("evidence", []) if isinstance(e, dict)
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
