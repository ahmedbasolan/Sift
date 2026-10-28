# Contributing to Sift

Thank you for your interest in contributing! This document outlines how to get started.

## Getting Started

1. **Clone the repo**
   ```bash
   git clone https://github.com/ahmedbasolan/Sift.git
   cd Sift
   ```

2. **Set up the backend**
   ```bash
   cd backend
   pip install -r requirements.txt
   pip install -e ".[dev]"
   cp .env.example .env
   # Add your GROQ_API_KEY to .env
   ```

3. **Set up the frontend**
   ```bash
   cd frontend
   npm install
   ```

4. **Run locally**
   ```bash
   # Option 1: Double-click start.bat (Windows)
   # Option 2: Manual
   cd backend && uvicorn app.main:app --reload --port 8000
   cd frontend && npm run dev
   ```

## Development Workflow

### Running Tests
```bash
cd backend
pytest tests/ -v
```

### Linting & Formatting
```bash
cd backend
ruff check .
ruff format .
```

### Type Checking
```bash
cd backend
pip install mypy
mypy app/ --ignore-missing-imports
```

### Adding a New Feature
1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make your changes
3. Add tests for new functionality
4. Ensure all tests pass: `pytest tests/ -v`
5. Ensure linting passes: `ruff check . && ruff format --check .`
6. Commit and open a Pull Request

## Code Style
- **Python**: Follow PEP 8 with ruff. Line length: 100.
- **TypeScript**: Follow existing patterns. Use `@/lib/api` for API calls.
- **Models**: All Pydantic models are in `backend/app/models.py`.

## Architecture
- **Backend**: FastAPI with async SQLAlchemy + ChromaDB + BM25 hybrid search
- **Frontend**: Next.js 14 + TypeScript + Tailwind CSS
- **LLM**: Groq (gpt-oss-120b)
- **RAG**: Hybrid (BM25 sparse + dense embeddings + Reciprocal Rank Fusion)

## Report Issues
- Use GitHub Issues for bugs and feature requests
- Include reproduction steps and environment details

## License
MIT — See LICENSE file for details.
