from app.database import AnalysisRecord, DocumentRecord
from app.models import (
    Citation,
    ExecutiveSummary,
    FinancialMetrics,
    RiskCategory,
    RiskFinding,
    RiskLevel,
)


def test_risk_level_enum():
    assert RiskLevel.LOW.value == "low"
    assert RiskLevel.CRITICAL.value == "critical"


def test_risk_category_enum():
    assert RiskCategory.MARKET.value == "market"
    assert RiskCategory.FINANCIAL.value == "financial"
    assert RiskCategory.REGULATORY.value == "regulatory"
    assert RiskCategory.OPERATIONAL.value == "operational"
    assert RiskCategory.COMPETITIVE.value == "competitive"


def test_financial_metrics_model():
    m = FinancialMetrics(revenue="1B", gross_margin="75%")
    assert m.revenue == "1B"
    assert m.gross_margin == "75%"
    assert m.net_income is None


def test_citation_model():
    c = Citation(text="test evidence", source="10-K", trust_level="verified")
    assert c.text == "test evidence"
    assert c.trust_level == "verified"
    assert c.page is None


def test_citation_with_page():
    c = Citation(text="test", source="doc", page=5, trust_level="inference")
    assert c.page == 5
    assert c.trust_level == "inference"


def test_executive_summary_model():
    s = ExecutiveSummary(
        company_name="Test Corp",
        company_overview="A test company",
        financial_health="Strong",
        key_strengths=["Strong revenue"],
        key_risks=["Market risk"],
        growth_opportunities=["Expansion"],
        recommendation="Invest",
        confidence_score=0.85,
    )
    assert s.confidence_score == 0.85
    assert len(s.key_strengths) == 1


def test_risk_finding_model():
    citation = Citation(text="test", source="doc", trust_level="verified")
    r = RiskFinding(
        category=RiskCategory.MARKET,
        title="Market risk",
        description="Market is volatile",
        severity=RiskLevel.HIGH,
        evidence=[citation],
        recommendation="Diversify",
    )
    assert r.severity == RiskLevel.HIGH
    assert r.category == RiskCategory.MARKET
    assert len(r.evidence) == 1


def test_risk_finding_defaults():
    citation = Citation(text="test", source="doc")
    r = RiskFinding(
        category=RiskCategory.FINANCIAL,
        title="Test",
        description="Test",
        severity=RiskLevel.MEDIUM,
        evidence=[citation],
        recommendation="Do something",
    )
    assert r.evidence[0].trust_level == "verified"


def test_document_record_creation():
    doc = DocumentRecord(
        id="test-id",
        filename="test.pdf",
        doc_type="pdf",
        file_size=1024,
        page_count=10,
        chunk_count=25,
        status="ready",
    )
    assert doc.id == "test-id"
    assert doc.chunk_count == 25
    assert doc.status == "ready"


def test_analysis_record_schema():
    record = AnalysisRecord(
        id="analysis-1",
        document_id="doc-1",
        summary="Test summary",
        financial_metrics={},
        risks=[],
        sections=[],
    )
    assert record.id == "analysis-1"
    assert record.document_id == "doc-1"


def test_health_response_structure():
    from app.models import HealthResponse

    h = HealthResponse(status="ok", version="0.1.0", groq="ok", chromadb="ok", sqlite="ok")
    assert h.status == "ok"
    assert h.groq == "ok"
    assert h.chromadb == "ok"


def test_upload_response_schema():
    from app.models import UploadResponse

    u = UploadResponse(id="doc-1", filename="test.pdf", status="ready", chunks=25, message="OK")
    assert u.chunks == 25
    assert u.status == "ready"


def test_risk_finding_from_dict():
    data = {
        "category": "financial",
        "title": "Cash flow risk",
        "description": "Negative cash flow",
        "severity": "high",
        "evidence": [{"text": "cash flow negative", "trust_level": "verified"}],
        "recommendation": "Monitor closely",
    }
    citation = Citation(
        text=data["evidence"][0]["text"],
        source="doc",
        trust_level=data["evidence"][0]["trust_level"],
    )
    r = RiskFinding(
        category=RiskCategory(data["category"]),
        title=data["title"],
        description=data["description"],
        severity=RiskLevel(data["severity"]),
        evidence=[citation],
        recommendation=data["recommendation"],
    )
    assert r.title == "Cash flow risk"
    assert r.severity == RiskLevel.HIGH


def test_detect_doc_type():
    from app.ingest import DocumentType, detect_doc_type

    assert detect_doc_type("report.pdf") == DocumentType.PDF
    assert detect_doc_type("presentation.pptx") == DocumentType.PPTX
    assert detect_doc_type("notes.md") == DocumentType.MD
    assert detect_doc_type("data.csv") == DocumentType.CSV
    assert detect_doc_type("unknown.xyz") == DocumentType.UNKNOWN
