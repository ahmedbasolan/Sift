from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import settings


class Base(DeclarativeBase):
    pass


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class DocumentRecord(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True)
    filename = Column(String, nullable=False)
    doc_type = Column(String, default="unknown")
    file_size = Column(Integer, default=0)
    page_count = Column(Integer, nullable=True)
    chunk_count = Column(Integer, default=0)
    status = Column(String, default="processing")
    uploaded_at = Column(DateTime, default=_utcnow)
    doc_metadata = Column("metadata", JSON, default=dict)


class AnalysisRecord(Base):
    __tablename__ = "analyses"

    id = Column(String, primary_key=True)
    document_id = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, default=_utcnow)
    summary = Column(Text, default="")
    financial_metrics = Column(JSON, default=dict)
    risks = Column(JSON, default=list)
    sections = Column(JSON, default=list)
    analysis_metadata = Column("metadata", JSON, default=dict)


engine = create_async_engine(settings.DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    async with async_session() as session:
        yield session
