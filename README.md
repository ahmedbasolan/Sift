# AI Due Diligence Copilot

A Retrieval-Augmented Generation (RAG) platform that analyzes company filings, financial statements, investor presentations, and market reports to deliver source-backed risk assessments, growth opportunities, and executive summaries.

**Live Demo:** [Replit URL](https://replit.com/@ahmed/ai-dd-copilot) (update after deploy)

## Features

- **Multi-format document ingestion** — PDF, DOCX, PPTX, XLSX, CSV, TXT, MD, HTML
- **Hybrid RAG search** — BM25 sparse + dense embeddings with Reciprocal Rank Fusion
- **LLM-powered analysis** — Executive summaries, risk assessments, financial metric extraction
- **Source-grounded chat** — Ask questions about uploaded documents with citation tracking
- **Report export** — Markdown and HTML report generation
- **Zero-cost stack** — Free tier everything (Groq, ChromaDB, sentence-transformers)

## Tech Stack

| Layer | Technology |
|-------|-----------|
| LLM | Groq (openai/gpt-oss-120b) |
| Embeddings | sentence-transformers all-MiniLM-L6-v2 |
| Vector DB | ChromaDB (embedded) |
| Database | SQLite + SQLAlchemy async |
| Backend | FastAPI + Python 3.12 |
| Frontend | Next.js 14 + TypeScript + Tailwind CSS |
| Search | Hybrid RAG (BM25 + dense + RRF) |
| Charts | Recharts |

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Frontend   │────▶│    Backend    │────▶│   Groq API   │
│  Next.js     │     │   FastAPI     │     │  (LLM)       │
│  :3000       │     │   :8000       │     └─────────────┘
└─────────────┘     └──────┬───────┘
                           │
                    ┌──────┴───────┐
                    │              │
              ┌─────▼─────┐ ┌─────▼─────┐
              │ ChromaDB   │ │  SQLite    │
              │ (vectors)  │ │ (metadata) │
              └───────────┘ └───────────┘
```

## Getting Started

### Local Development

```bash
# Backend
cd backend
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Mac/Linux
pip install -r requirements.txt

# Add your Groq API key
cp .env.example .env
# Edit .env with your GROQ_API_KEY

# Start backend
uvicorn app.main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

### Replit

1. Import this repo to Replit
2. Add `GROQ_API_KEY` to Replit Secrets
3. Click Run

### Docker

```bash
docker-compose up --build
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/upload` | Upload document |
| GET | `/documents` | List documents |
| DELETE | `/documents/{id}` | Delete document |
| POST | `/analyze/{id}` | Run analysis |
| GET | `/analyses` | List analyses |
| GET | `/analyses/{id}` | Get analysis detail |
| POST | `/chat` | Ask questions |
| GET | `/report/{id}` | Export report |

## Environment Variables

```bash
GROQ_API_KEY=gsk_xxxxx          # Required: Groq API key
NEXT_PUBLIC_API_URL=http://localhost:8000  # Frontend API URL
```

## How It Works

1. **Upload** — Documents are parsed (text extracted), chunked, and embedded
2. **Index** — Chunks stored in ChromaDB (vectors) + SQLite (metadata)
3. **Analyze** — Hybrid search retrieves relevant chunks, LLM generates summary/risks/metrics
4. **Chat** — Questions go through the same RAG pipeline with source citations

## License

MIT
