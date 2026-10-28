import asyncio

import httpx

from app.config import settings


class LLMUnavailable(RuntimeError):
    """The LLM gave no usable answer: no key, a rejected key, a rate limit, or an
    unreadable reply. The message says which, in words a user can act on."""


async def call_groq(
    messages: list[dict],
    temperature: float = 0.1,
    max_tokens: int = 4096,
    response_format: dict | None = None,
) -> str:
    if not settings.GROQ_API_KEY:
        raise LLMUnavailable(
            "No GROQ_API_KEY is set. Add one to backend/.env "
            "(free at console.groq.com) and restart the backend."
        )

    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.GROQ_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if response_format:
        payload["response_format"] = response_format

    max_retries = 5
    async with httpx.AsyncClient(timeout=60.0) as client:
        for attempt in range(max_retries):
            try:
                resp = await client.post(
                    f"{settings.GROQ_BASE_URL}/chat/completions",
                    headers=headers,
                    json=payload,
                )
            except httpx.TransportError as e:
                raise LLMUnavailable(f"Could not reach Groq: {e}") from e
            if resp.status_code == 429:
                wait = min(2**attempt * 3, 30)
                await asyncio.sleep(wait)
                continue
            if resp.status_code in (401, 403):
                raise LLMUnavailable(
                    "Groq rejected the GROQ_API_KEY. Check the key in backend/.env."
                )
            if resp.status_code >= 400:
                raise LLMUnavailable(f"Groq returned HTTP {resp.status_code}. Try again shortly.")
            try:
                content = resp.json()["choices"][0]["message"]["content"]
            except (KeyError, IndexError, TypeError, ValueError) as e:
                raise LLMUnavailable("Groq returned a reply Sift could not read.") from e
            if not isinstance(content, str) or not content.strip():
                raise LLMUnavailable("Groq returned a reply Sift could not read: it had no text.")
            return content

    raise LLMUnavailable(
        "Groq's rate limit is still exceeded after several retries. "
        "Wait a minute, or check your daily token quota at console.groq.com."
    )


async def generate_analysis(
    context: str,
    question: str,
    system_prompt: str,
) -> str:
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
    ]
    return await call_groq(messages)


async def generate_summary(context: str) -> str:
    prompt = """You are a senior financial analyst. Generate a concise executive summary
from the provided document context. Include:
1. Company overview (1-2 sentences)
2. Financial health assessment
3. Top 3 key strengths
4. Top 3 key risks
5. Growth opportunities
6. Final recommendation
7. Confidence score (0.0-1.0)

Be factual and cite evidence. If information is missing, state it clearly."""
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": f"Document context:\n{context}"},
    ]
    return await call_groq(messages)


async def extract_financial_metrics(context: str) -> str:
    prompt = """Extract financial metrics from the document. Return ONLY valid JSON with these fields:
{
    "revenue": "string or null",
    "revenue_growth": "string or null",
    "gross_margin": "string or null",
    "operating_margin": "string or null",
    "net_income": "string or null",
    "ebitda": "string or null",
    "cash_position": "string or null",
    "debt_level": "string or null",
    "burn_rate": "string or null",
    "runway_months": "string or null",
    "arr": "string or null",
    "mrr": "string or null",
    "custom": {}
}
Only include values that are explicitly stated. Use null for missing fields.
Return ONLY the JSON object, no other text."""
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": f"Document context:\n{context}"},
    ]
    return await call_groq(messages)


async def assess_risks(context: str) -> str:
    prompt = """Analyze the document for risks. Return ONLY a valid JSON array:
[
    {
        "category": "market|financial|regulatory|operational|competitive",
        "title": "short title",
        "description": "detailed description",
        "severity": "low|medium|high|critical",
        "evidence": [{"text": "quoted text", "trust_level": "verified|inference|assumption"}],
        "recommendation": "action item"
    }
]
Be specific and cite actual evidence. If no risks found, return [].
Return ONLY the JSON array, no other text."""
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": f"Document context:\n{context}"},
    ]
    return await call_groq(messages)


async def answer_question(context: str, question: str) -> str:
    prompt = """Answer the user's question using ONLY the provided context.
Cite your sources by referencing the document and page number.
If the context doesn't contain enough information, say so.
Be concise and factual."""
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
    ]
    return await call_groq(messages)
