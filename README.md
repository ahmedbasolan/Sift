# Sift

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue)](https://python.org)
[![Next.js 14](https://img.shields.io/badge/Next.js-14-black)](https://nextjs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green)](https://fastapi.tiangolo.com)
[![CI](https://github.com/ahmedbasolan/Sift/actions/workflows/ci.yml/badge.svg)](https://github.com/ahmedbasolan/Sift/actions/workflows/ci.yml)
[![Code Quality](https://img.shields.io/badge/Code_Quality-Ruff%2BMypy-orange)](https://github.com/ahmedbasolan/Sift)

AI-powered due diligence copilot. Upload financial documents, get source-backed risk assessments, growth opportunities, and executive summaries in seconds.

## What It Does

Upload any financial document — 10-K filings, pitch decks, annual reports, investor presentations — and Sift instantly:

- Generates an **executive summary** with company overview and recommendation
- Identifies **risks** across 5 categories (market, financial, regulatory, operational, competitive) with severity scoring and evidence
- Extracts **financial metrics** (revenue, margins, burn rate, runway, etc.)
- Answers **follow-up questions** with source citations and page references
- Exports **Markdown/HTML reports** for sharing

## Demo Files

Ready-to-use sample documents in `sample_data/`. **All of them are fictional**: written for this demo, with invented companies, people and figures. None is a real company's filing or pitch deck, and each file says so at the top.

| File | Type | What It Shows |
|------|------|---------------|
| `shutterbloom_10k_2024.md` | Listed company 10-K summary | Revenue growth, first profitable quarter, ad concentration |
| `quillwork_series_c.md` | Series C pitch deck | Fast growth — traction, unit economics, 175% ARR growth |
| `hivedesk_dd_brief.md` | Due diligence brief | **Failing company** — lease obligations, governance failures, bankruptcy |
| `zerica_series_a.md` | Series A pitch deck | Early-stage fintech — metrics, market opportunity |
| `quickship_logistics_dd.md` | DD brief | Distressed company — cash crisis, negative unit economics |
| `acme_robotics_sample.md`, `greenenergy_series_a.md`, `meridian_health_10k.md`, `novatech_ai_seed.md` | Mixed | Shorter samples across stages and sectors |

**Upload any of these through the UI to see Sift in action.**

## Features

- **Multi-format ingestion** — PDF, DOCX, PPTX, XLSX, CSV, TXT, MD, HTML
- **Hybrid RAG** — BM25 sparse + dense embeddings with Reciprocal Rank Fusion
- **Source-grounded chat** — Every answer cites its sources
- **Zero-cost stack** — Free tier Groq, ChromaDB, sentence-transformers
- **50MB file limit** — Prevents OOM from oversized uploads

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

### Option 1: Double-click (Windows)

Run `start.bat` — installs deps and starts both servers automatically.

### Option 2: Manual

```bash
# Backend
cd backend
python -m venv .venv
.venv\Scripts\activate      # Windows
source .venv/bin/activate   # Mac/Linux
pip install -r requirements.txt
cp .env.example .env        # Then edit .env to add your GROQ_API_KEY
uvicorn app.main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

### Option 3: Docker

```bash
# Set your Groq API key
export GROQ_API_KEY=gsk_...
export NEXT_PUBLIC_API_URL=http://localhost:8000

docker-compose up --build
```

### Get a Groq API Key

1. Go to [console.groq.com](https://console.groq.com)
2. Sign up (free)
3. Create an API key
4. Paste into `backend/.env` as `GROQ_API_KEY=gsk_...`

### Without a key

Upload and search work without one: chat answers with the passages that best match the question, with their citations, and says no answer was generated. Analysis needs the LLM, so it returns an error saying what to set and saves nothing. A rejected key or an exhausted Groq rate limit is reported the same way rather than stored as a result. `/health` reports `"groq": "no_key"`.

### End-to-end check

```bash
python scripts/smoke_samples.py
```

Uploads and analyzes every file in `sample_data/` through the API, in a throwaway database, and exits non-zero if any fails. It calls Groq (about 3 calls per document), so it needs the key and is not part of CI.

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
