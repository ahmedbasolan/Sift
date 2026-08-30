# AI Due Diligence Copilot

An AI-powered platform that analyzes financial documents — company filings, financial statements, investor presentations, and market reports — to accelerate due diligence workflows. Delivers source-backed risk assessments, growth opportunities, and executive summaries in seconds.

## Architecture

```
┌─────────────────────────────────────────────┐
│          Next.js Frontend                    │
│  Upload · Dashboard · Analysis · Chat        │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│          FastAPI Backend                     │
│                                              │
│  Upload → Parse → Chunk → Embed → Store     │
│  Query → Hybrid Search → Groq LLM → Response│
└──────────┬───────────────┬──────────────────┘
           │               │
      ┌────▼────┐    ┌─────▼─────┐
      │ ChromaDB │    │  SQLite   │
      │ (vectors)│    │(metadata) │
      └─────────┘    └───────────┘
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, TypeScript, Tailwind CSS, Recharts |
| Backend | FastAPI, Python 3.12 |
| LLM | Groq (Llama 3.3 70B) — free tier, 14,400 req/day |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| Vector DB | ChromaDB (embedded) |
| Database | SQLite |
| Search | Hybrid RAG (BM25 + Dense + RRF Fusion) |

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- A Groq API key (free at https://console.groq.com)

### Backend

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Add your GROQ_API_KEY to .env

uvicorn app.main:app --reload
# API docs at http://localhost:8000/docs
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# App at http://localhost:3000
```

### Docker

```bash
docker-compose up --build
```

## Features

- **Multi-format ingestion**: PDF, PPTX, DOCX, XLSX, CSV, TXT, Markdown, HTML
- **Hybrid RAG**: Dense embeddings + BM25 with Reciprocal Rank Fusion
- **Financial extraction**: Revenue, margins, EBITDA, burn rate, runway, ARR/MRR
- **Risk engine**: 5 categories (market, financial, regulatory, operational, competitive)
- **Executive summaries**: AI-generated with confidence scores
- **Source citations**: Every claim traced to source with trust labels
- **Grounded chat**: Ask questions over your documents
- **Report export**: Markdown and HTML formats

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/upload` | Upload a document |
| GET | `/documents` | List all documents |
| DELETE | `/documents/{id}` | Delete a document |
| POST | `/analyze/{id}` | Run due diligence analysis |
| GET | `/analyses` | List all analyses |
| GET | `/analyses/{id}` | Get analysis details |
| POST | `/chat` | Ask questions about documents |
| GET | `/report/{id}` | Get report (markdown/html) |
| GET | `/health` | Health check |

## How It Works

1. **Upload** — Drop a PDF, presentation, or spreadsheet
2. **Parse & Chunk** — Document is parsed with section-aware chunking
3. **Embed** — Chunks are embedded using sentence-transformers
4. **Index** — Stored in ChromaDB (dense) + BM25 (sparse)
5. **Analyze** — Hybrid search retrieves relevant context → Groq LLM generates analysis
6. **Report** — Executive summary, financial metrics, risk assessment with citations

## License

MIT
