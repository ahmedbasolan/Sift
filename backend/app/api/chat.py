import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.config import settings
from app.llm import answer_question
from app.models import ChatRequest, Citation
from app.search import hybrid_search

router = APIRouter()


async def _stream_chat_response(results: list[dict], query: str) -> AsyncIterator[str]:
    from app.llm import answer_question

    context = "\n\n".join(
        f"[{r.get('metadata', {}).get('filename', 'doc')}, p.{r.get('metadata', {}).get('page_num', '?')}]\n{r['text']}"
        for r in results
    )

    async def generate():
        try:
            answer = await answer_question(context, query)
            full_text = answer

            data = {
                "type": "content",
                "content": full_text,
                "citations": [],
            }
            yield f"data: {json.dumps(data)}\n\n"

            citations_data = [
                {
                    "text": r["text"][:200],
                    "source": r.get("metadata", {}).get("filename", "unknown"),
                    "page": r.get("metadata", {}).get("page_num"),
                    "trust_level": "verified" if r.get("rrf_score", 0) > 0.5 else "inference",
                }
                for r in results[:5]
            ]

            citation_event = {
                "type": "citations",
                "citations": citations_data,
            }
            yield f"data: {json.dumps(citation_event)}\n\n"

            yield "data: [DONE]\n\n"
        except Exception as e:
            error_event = {"type": "error", "error": str(e)}
            yield f"data: {json.dumps(error_event)}\n\n"

    return generate()


@router.post("/chat")
async def chat_stream(req: ChatRequest):
    query = req.message.strip()
    if not query:
        return {"answer": "Please provide a question.", "citations": [], "route": "error"}

    if len(query) > 5000:
        raise HTTPException(status_code=400, detail="Message too long (max 5000 characters)")

    where_filter = None
    if req.document_ids and len(req.document_ids) == 1:
        where_filter = {"document_id": req.document_ids[0]}

    results = hybrid_search(query, top_k=settings.TOP_K_RESULTS, where=where_filter)

    if req.document_ids and len(req.document_ids) > 1:
        results = [
            r for r in results if r.get("metadata", {}).get("document_id") in req.document_ids
        ]

    if not results:
        return {
            "answer": "No relevant documents found. Please upload documents first.",
            "citations": [],
            "route": "rag",
        }

    context = "\n\n".join(
        f"[{r.get('metadata', {}).get('filename', 'doc')}, p.{r.get('metadata', {}).get('page_num', '?')}]\n{r['text']}"
        for r in results
    )

    citations = [
        Citation(
            text=r["text"][:200],
            source=r.get("metadata", {}).get("filename", "unknown"),
            page=r.get("metadata", {}).get("page_num"),
            trust_level="verified" if r.get("rrf_score", 0) > 0.5 else "inference",
        )
        for r in results[:5]
    ]

    if req.stream:
        return StreamingResponse(
            _stream_chat_response(results, query),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )

    answer = await answer_question(context, query)
    return {"answer": answer, "citations": [c.model_dump() for c in citations], "route": "rag"}


@router.post("/chat/sync")
async def chat_sync(req: ChatRequest):
    query = req.message.strip()
    if not query:
        return {"answer": "Please provide a question.", "citations": [], "route": "error"}

    if len(query) > 5000:
        raise HTTPException(status_code=400, detail="Message too long")

    where_filter = None
    if req.document_ids and len(req.document_ids) == 1:
        where_filter = {"document_id": req.document_ids[0]}

    results = hybrid_search(query, top_k=settings.TOP_K_RESULTS, where=where_filter)

    if req.document_ids and len(req.document_ids) > 1:
        results = [
            r for r in results if r.get("metadata", {}).get("document_id") in req.document_ids
        ]

    if not results:
        return {
            "answer": "No relevant documents found. Please upload documents first.",
            "citations": [],
            "route": "rag",
        }

    context = "\n\n".join(
        f"[{r.get('metadata', {}).get('filename', 'doc')}, p.{r.get('metadata', {}).get('page_num', '?')}]\n{r['text']}"
        for r in results
    )

    answer = await answer_question(context, query)

    citations = [
        Citation(
            text=r["text"][:200],
            source=r.get("metadata", {}).get("filename", "unknown"),
            page=r.get("metadata", {}).get("page_num"),
            trust_level="verified" if r.get("rrf_score", 0) > 0.5 else "inference",
        )
        for r in results[:5]
    ]

    return {"answer": answer, "citations": [c.model_dump() for c in citations], "route": "rag"}
