# Sift

AI-powered due diligence copilot. Upload financial documents, get source-backed risk assessments, growth opportunities, and executive summaries in seconds.

**Live Demo:** [Replit](https://replit.com/@ahmed/sift) *(update after deploy)*

## What It Does

Upload any financial document — 10-K filings, pitch decks, annual reports, investor presentations — and Sift instantly:

- Generates an **executive summary** with company overview and recommendation
- Identifies **risks** across 5 categories (market, financial, regulatory, operational, competitive) with severity scoring and evidence
- Extracts **financial metrics** (revenue, margins, burn rate, runway, etc.)
- Answers **follow-up questions** with source citations and page references
- Exports **Markdown/HTML reports** for sharing

## Features

- **Multi-format ingestion** — PDF, DOCX, PPTX, XLSX, CSV, TXT, MD, HTML
- **Hybrid RAG** — BM25 sparse + dense embeddings with Reciprocal Rank Fusion
- **Source-grounded chat** — Every answer cites its sources
- **Zero-cost stack** — Free tier Groq, ChromaDB, sentence-transformers
- **Docker ready** — One command to deploy

## Tech Stack

| Layer | Technology |
|-------|-----------|
| LLM | Groq (openai/gpt-oss-120b) |
| Embeddings | sentence-transformers `all-MiniLM-L6-v2` |
| Vector DB | ChromaDB (embedded) |
| Database | SQLite + SQLAlchemy async |
| Backend | FastAPI + Python 3.12 |
| Frontend | Next.js 14 + TypeScript + Tailwind CSS |
| Search | Hybrid RAG (BM25 + dense + RRF) |
| Charts | Recharts |

## Architecture

```
┌──────────────┐     ┌──────────────┐     ┌─────────────┐
│   Frontend    │────▶│    Backend    │────▶│  Groq API    │
│   Next.js     │     │   FastAPI     │     │  (LLM)       │
│   :3000       │     │   :8000       │     └─────────────┘
└──────────────┘     └──────┬───────┘
                           │
                    ┌──────┴───────┐
                    │              │
              ┌─────▼─────┐ ┌─────▼─────┐
              │ ChromaDB   │ │  SQLite    │
              │ (vectors)  │ │ (metadata) │
              └───────────┘ └───────────┘
```

## Quick Start

### Local

```bash
# Backend
cd backend
python -m venv .venv
.venv\Scripts\activate      # Windows
source .venv/bin/activate   # Mac/Linux
pip install -r requirements.txt
cp .env.example .env        # Add your GROQ_API_KEY
uvicorn app.main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

### Replit

1. Import this repo → [replit.com](https://replit.com)
2. Add `GROQ_API_KEY` to Replit Secrets
3. Click Run

### Docker

```bash
docker-compose up --build
```

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/upload` | Upload document |
| `GET` | `/documents` | List documents |
| `DELETE` | `/documents/{id}` | Delete document |
| `POST` | `/analyze/{id}` | Run analysis |
| `GET` | `/analyses` | List analyses |
| `GET` | `/analyses/{id}` | Get analysis |
| `POST` | `/chat` | Ask questions |
| `GET` | `/report/{id}` | Export report |

## How It Works

1. **Upload** — Document text is extracted, chunked, and embedded
2. **Index** — Chunks stored in ChromaDB (vectors) + SQLite (metadata)
3. **Analyze** — Hybrid search retrieves relevant chunks → LLM generates summary, risks, metrics
4. **Chat** — Follow-up questions use the same RAG pipeline with citation tracking

## License

MIT
