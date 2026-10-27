"""What Sift does when the LLM can't answer: no key, a rejected key, or a rate limit.

It used to substitute placeholder text ("Offline mode placeholder", confidence 0.0)
and save that as the document's analysis, so a run without a key, or one that hit
Groq's rate limit, produced a stored result that looked like a real one.
"""

import httpx
import pytest
from app.config import settings
from app.database import DocumentRecord
from app.llm import LLMUnavailable, call_groq

CHUNK = {
    "text": "Acme Robotics revenue grew 205% to $12.4M in FY2025.",
    "metadata": {"document_id": "doc-acme", "filename": "acme.md", "page_num": 1},
    "rrf_score": 0.9,
}


@pytest.fixture
async def ready_doc(db_session):
    db_session.add(DocumentRecord(id="doc-acme", filename="acme.md", status="ready"))
    await db_session.commit()
    return "doc-acme"


@pytest.fixture
def no_key(monkeypatch):
    monkeypatch.setattr(settings, "GROQ_API_KEY", "")


def test_analysis_without_a_key_is_refused_and_nothing_is_saved(
    client, ready_doc, no_key, monkeypatch
):
    monkeypatch.setattr("app.analysis.hybrid_search", lambda *a, **k: [CHUNK])

    response = client.post(f"/analyze/{ready_doc}")

    assert response.status_code == 503
    assert "GROQ_API_KEY" in response.json()["detail"]
    assert client.get("/analyses").json() == []


def test_chat_without_a_key_returns_the_matching_passages(client, no_key, monkeypatch):
    monkeypatch.setattr("app.api.chat.hybrid_search", lambda *a, **k: [CHUNK])

    data = client.post("/chat", json={"message": "How fast did revenue grow?"}).json()

    assert data["route"] == "retrieval_only"
    assert "GROQ_API_KEY" in data["answer"]
    assert "205%" in data["answer"]
    assert data["citations"][0]["source"] == "acme.md"


def test_streamed_chat_without_a_key_streams_the_passages(client, no_key, monkeypatch):
    """Streaming also never worked: the stream builder was an `async def`, so
    StreamingResponse was handed a coroutine instead of a stream."""
    monkeypatch.setattr("app.api.chat.hybrid_search", lambda *a, **k: [CHUNK])

    response = client.post("/chat", json={"message": "Revenue growth?", "stream": True})

    assert response.status_code == 200
    assert '"route": "retrieval_only"' in response.text
    assert "205%" in response.text
    assert response.text.rstrip().endswith("data: [DONE]")


def _groq_replies(monkeypatch, status: int, body: dict | None = None):
    async def post(self, url, **kwargs):
        return httpx.Response(status, json=body, request=httpx.Request("POST", url))

    async def no_wait(_seconds):
        return None

    monkeypatch.setattr(settings, "GROQ_API_KEY", "gsk_test")
    monkeypatch.setattr(httpx.AsyncClient, "post", post)
    monkeypatch.setattr("app.llm.asyncio.sleep", no_wait)


async def test_rate_limit_is_reported_not_answered_with_placeholder(monkeypatch):
    _groq_replies(monkeypatch, 429)
    with pytest.raises(LLMUnavailable, match="rate limit"):
        await call_groq([{"role": "user", "content": "hi"}])


async def test_rejected_key_is_reported(monkeypatch):
    _groq_replies(monkeypatch, 401)
    with pytest.raises(LLMUnavailable, match="rejected"):
        await call_groq([{"role": "user", "content": "hi"}])


async def test_a_reply_with_no_text_is_reported(monkeypatch):
    _groq_replies(monkeypatch, 200, {"choices": [{"message": {"content": None}}]})
    with pytest.raises(LLMUnavailable, match="could not read"):
        await call_groq([{"role": "user", "content": "hi"}])
