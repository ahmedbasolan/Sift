from fastapi import APIRouter
from app.models import ChatRequest, ChatResponse, Citation
from app.search import hybrid_search
from app.llm import answer_question
from app.config import settings

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    query = req.message.strip()
    if not query:
        return ChatResponse(answer="Please provide a question.", citations=[], route="error")

    where_filter = None
    if req.document_ids:
        if len(req.document_ids) == 1:
            where_filter = {"document_id": req.document_ids[0]}
        # ChromaDB doesn't support $in, so for multiple we search all and filter after

    results = hybrid_search(query, top_k=settings.TOP_K_RESULTS, where=where_filter)

    if req.document_ids and len(req.document_ids) > 1:
        results = [r for r in results if r.get("metadata", {}).get("document_id") in req.document_ids]

    if not results:
        return ChatResponse(
            answer="No relevant documents found. Please upload documents first.",
            citations=[],
            route="rag",
        )

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
            trust_level="verified" if r.get("score", 0) > 0.7 else "inference",
        )
        for r in results[:5]
    ]

    return ChatResponse(answer=answer, citations=citations, route="rag")
