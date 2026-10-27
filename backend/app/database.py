from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Integer, String, Text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.config import settings


class Base(DeclarativeBase):
    pass


def _utcnow() -> datetime:
    return datetime.now(UTC)


# Typed with Mapped[] so mypy sees str/int/datetime, not Column objects. The
# explicit nullable=True keeps the schema exactly as it was: those columns
# were nullable in the database, and always filled by their defaults.
class DocumentRecord(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    filename: Mapped[str] = mapped_column(String, nullable=False)
    doc_type: Mapped[str] = mapped_column(String, nullable=True, default="unknown")
    file_size: Mapped[int] = mapped_column(Integer, nullable=True, default=0)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    chunk_count: Mapped[int] = mapped_column(Integer, nullable=True, default=0)
    status: Mapped[str] = mapped_column(String, nullable=True, default="processing")
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, nullable=True, default=_utcnow)
    doc_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSON, nullable=True, default=dict
    )


class AnalysisRecord(Base):
    __tablename__ = "analyses"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    document_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=True, default=_utcnow)
    summary: Mapped[str] = mapped_column(Text, nullable=True, default="")
    financial_metrics: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=True, default=dict)
    risks: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=True, default=list)
    sections: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=True, default=list)
    analysis_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSON, nullable=True, default=dict
    )


engine = create_async_engine(settings.DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    async with async_session() as session:
        yield session
