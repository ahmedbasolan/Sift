"""Upload and analyze every demo document in sample_data/ through the real API.

An end-to-end smoke run, not a unit test: it calls Groq, so it needs
GROQ_API_KEY (in backend/.env or the environment) and uses about 3 LLM calls
per document. Each run gets a throwaway database and vector store, so it
neither reads nor changes the data your local app has stored.

  python scripts/smoke_samples.py            # every sample
  python scripts/smoke_samples.py acme_robotics_sample.md

Exits 1 if any document fails to upload or analyze.
"""

import asyncio
import os
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BACKEND = REPO / "backend"
SAMPLES = REPO / "sample_data"

# Before the app is imported: settings are read once, at import.
_scratch = Path(tempfile.mkdtemp(prefix="sift-smoke-"))
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{(_scratch / 'app.db').as_posix()}"
os.environ["CHROMA_PERSIST_DIR"] = str(_scratch / "chroma")
os.chdir(BACKEND)  # so backend/.env is found
sys.path.insert(0, str(BACKEND))
sys.stdout.reconfigure(encoding="utf-8")


async def run(names: list[str]) -> int:
    import httpx
    from app.config import settings
    from app.database import init_db
    from app.main import app

    if not settings.GROQ_API_KEY:
        print("GROQ_API_KEY is not set. Add it to backend/.env (free at console.groq.com).")
        return 2

    await init_db()
    failures = 0
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        for name in names:
            print(f"\n===== {name} =====")
            path = SAMPLES / name
            r = await client.post(
                "/upload", files={"file": (name, path.read_bytes(), "text/markdown")}, timeout=60
            )
            if r.status_code != 200:
                print("  Upload failed:", r.status_code, r.text[:200])
                failures += 1
                continue
            print("  Upload: ok,", r.json().get("chunks", 0), "chunks")

            r = await client.post(f"/analyze/{r.json()['id']}", timeout=300)
            if r.status_code != 200:
                print("  Analyze failed:", r.status_code, r.json().get("detail", r.text)[:300])
                failures += 1
                continue
            data = r.json()
            s = data.get("executive_summary", {})
            fm = data.get("financial_metrics", {})
            filled = sum(1 for k, v in fm.items() if v and k != "custom")
            print("  company_name:", s.get("company_name"))
            print(
                "  strengths / risks / opportunities:",
                *(
                    len(s.get(k, []))
                    for k in ("key_strengths", "key_risks", "growth_opportunities")
                ),
            )
            print("  confidence:", s.get("confidence_score"))
            print(f"  metrics filled: {filled}/12")
            for risk in data.get("risks", [])[:3]:
                print(f"    - [{risk.get('severity', '')}] {risk.get('title', '')}")

    print(f"\n{len(names) - failures}/{len(names)} documents analyzed")
    return 1 if failures else 0


if __name__ == "__main__":
    wanted = sys.argv[1:] or sorted(p.name for p in SAMPLES.glob("*.md"))
    missing = [n for n in wanted if not (SAMPLES / n).is_file()]
    if missing:
        sys.exit(f"Not in sample_data/: {', '.join(missing)}")
    sys.exit(asyncio.run(run(wanted)))
