from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import analyze, chat, report, upload
from app.auth import create_api_key_middleware
from app.config import settings
from app.database import init_db
from app.search import rebuild_bm25_from_collection


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    # BM25 lives in memory only; restore it from the persisted Chroma chunks
    # so the sparse half of hybrid search works on every boot, not just the first.
    try:
        restored = rebuild_bm25_from_collection()
        if restored:
            print(f"[Sift] Restored {restored} chunks into the BM25 index")
    except Exception as e:
        print(f"[Sift] BM25 restore skipped: {e}")
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if settings.API_KEY:
    app.middleware("http")(create_api_key_middleware(settings.API_KEY))

app.include_router(upload.router, tags=["documents"])
app.include_router(analyze.router, tags=["analysis"])
app.include_router(chat.router, tags=["chat"])
app.include_router(report.router, tags=["reports"])


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }
