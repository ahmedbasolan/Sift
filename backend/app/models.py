from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class DocumentType(StrEnum):
    PDF = "pdf"
    PPTX = "pptx"
    DOCX = "docx"
    XLSX = "xlsx"
    CSV = "csv"
    TXT = "txt"
    MD = "md"
    HTML = "html"
    UNKNOWN = "unknown"


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskCategory(StrEnum):
    MARKET = "market"
    FINANCIAL = "financial"
    REGULATORY = "regulatory"
    OPERATIONAL = "operational"
    COMPETITIVE = "competitive"


class Citation(BaseModel):
    text: str
    source: str
    page: int | None = None
    section: str | None = None
    trust_level: str = "verified"  # verified | inference | assumption


class FinancialMetrics(BaseModel):
    revenue: str | None = None
    revenue_growth: str | None = None
    gross_margin: str | None = None
    operating_margin: str | None = None
    net_income: str | None = None
    ebitda: str | None = None
    cash_position: str | None = None
    debt_level: str | None = None
    burn_rate: str | None = None
    runway_months: str | None = None
    arr: str | None = None
    mrr: str | None = None
    custom: dict[str, str] = Field(default_factory=dict)


class RiskFinding(BaseModel):
    category: RiskCategory
    title: str
    description: str
    severity: RiskLevel
    evidence: list[Citation]
    recommendation: str


class ExecutiveSummary(BaseModel):
    company_name: str | None = None
    company_overview: str
    financial_health: str
    key_strengths: list[str]
    key_risks: list[str]
    growth_opportunities: list[str]
    recommendation: str
    confidence_score: float


class AnalysisResult(BaseModel):
    id: str
    document_id: str
    created_at: datetime
    executive_summary: ExecutiveSummary
    financial_metrics: FinancialMetrics
    risks: list[RiskFinding]
    sections: list[dict]
    metadata: dict = Field(default_factory=dict)


class Document(BaseModel):
    id: str
    filename: str
    doc_type: DocumentType
    file_size: int
    page_count: int | None = None
    chunk_count: int = 0
    uploaded_at: datetime
    status: str = "processing"
    metadata: dict = Field(default_factory=dict)


class ChatMessage(BaseModel):
    role: str
    content: str
    citations: list[Citation] = Field(default_factory=list)


class ChatRequest(BaseModel):
    message: str
    document_ids: list[str] = Field(default_factory=list)
    stream: bool = False


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]
    route: str  # rag | hybrid


class UploadResponse(BaseModel):
    id: str
    filename: str
    status: str
    chunks: int
    message: str


class HealthResponse(BaseModel):
    status: str
    version: str
    groq: str
    chromadb: str
    sqlite: str
