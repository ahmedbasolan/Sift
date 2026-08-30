const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

export interface Document {
  id: string;
  filename: string;
  doc_type: string;
  file_size: number;
  page_count: number | null;
  chunk_count: number;
  status: string;
  uploaded_at: string | null;
}

export interface UploadResult {
  id: string;
  filename: string;
  status: string;
  chunks: number;
  message: string;
}

export interface FinancialMetrics {
  revenue: string | null;
  revenue_growth: string | null;
  gross_margin: string | null;
  operating_margin: string | null;
  net_income: string | null;
  ebitda: string | null;
  cash_position: string | null;
  debt_level: string | null;
  burn_rate: string | null;
  runway_months: string | null;
  arr: string | null;
  mrr: string | null;
}

export interface RiskFinding {
  category: string;
  title: string;
  description: string;
  severity: string;
  evidence: { text: string; trust_level: string }[];
  recommendation: string;
}

export interface AnalysisResult {
  id: string;
  document_id: string;
  created_at: string;
  executive_summary: {
    company_overview: string;
    financial_health: string;
    key_strengths: string[];
    key_risks: string[];
    growth_opportunities: string[];
    recommendation: string;
    confidence_score: number;
  };
  financial_metrics: FinancialMetrics;
  risks: RiskFinding[];
  sections: any[];
  metadata: any;
}

export interface ChatResponse {
  answer: string;
  citations: { text: string; source: string; page: number | null; trust_level: string }[];
  route: string;
}

export interface HealthStatus {
  status: string;
  version: string;
  groq: string;
  chromadb: string;
  sqlite: string;
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

export async function healthCheck(): Promise<HealthStatus> {
  return request('/health');
}

export async function uploadDocument(file: File): Promise<UploadResult> {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${API_BASE}/upload`, { method: 'POST', body: formData });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Upload failed');
  }
  return res.json();
}

export async function listDocuments(): Promise<Document[]> {
  return request('/documents');
}

export async function deleteDocument(id: string): Promise<void> {
  await request(`/documents/${id}`, { method: 'DELETE' });
}

export async function analyzeDocument(id: string): Promise<AnalysisResult> {
  return request(`/analyze/${id}`, { method: 'POST' });
}

export async function listAnalyses(): Promise<{ id: string; document_id: string; created_at: string; summary_preview: string }[]> {
  return request('/analyses');
}

export async function getAnalysis(id: string): Promise<any> {
  return request(`/analyses/${id}`);
}

export async function chat(message: string, documentIds: string[] = []): Promise<ChatResponse> {
  return request('/chat', {
    method: 'POST',
    body: JSON.stringify({ message, document_ids: documentIds }),
  });
}

export async function getReport(id: string, format: string = 'markdown'): Promise<{ content: string; type: string }> {
  return request(`/report/${id}?format=${format}`);
}
