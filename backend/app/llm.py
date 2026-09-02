import asyncio
import json
import httpx
from app.config import settings


async def call_groq(
    messages: list[dict],
    temperature: float = 0.1,
    max_tokens: int = 4096,
    response_format: dict | None = None,
) -> str:
    if not settings.GROQ_API_KEY:
        return _mock_response(messages)

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
                if resp.status_code == 429:
                    wait = min(2 ** attempt * 3, 30)
                    await asyncio.sleep(wait)
                    continue
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"]
            except (KeyError, IndexError, ValueError) as e:
                import sys
                print(f"[Sift] Groq response parse error: {e}", file=sys.stderr)
                return _mock_response(messages)

    return _mock_response(messages)


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


def _mock_response(messages: list[dict]) -> str:
    user_msg = messages[-1]["content"] if messages else ""
    system_msg = messages[0]["content"] if len(messages) > 0 else ""
    combined = (system_msg + " " + user_msg).lower()

    if "financial metric" in combined or "extract" in combined:
        return json.dumps({
            "revenue": None, "revenue_growth": None,
            "gross_margin": None, "operating_margin": None,
            "net_income": None, "ebitda": None,
            "cash_position": None, "debt_level": None,
            "burn_rate": None, "runway_months": None,
            "arr": None, "mrr": None, "custom": {},
        })
    if "risk" in combined and "anomal" not in combined:
        return json.dumps([])
    if "executive summary" in combined or "senior financial analyst" in combined:
        return (
            "Company Overview: Analysis unavailable in offline mode.\n\n"
            "Financial Health: Add a GROQ_API_KEY to .env for real analysis.\n\n"
            "Key Strengths:\n- Offline mode placeholder\n\n"
            "Key Risks:\n- Offline mode placeholder\n\n"
            "Growth Opportunities:\n- Offline mode placeholder\n\n"
            "Recommendation: Add a GROQ_API_KEY to enable full analysis.\n\n"
            "Confidence Score: 0.0"
        )
    return "Response unavailable in offline mode. Add a GROQ_API_KEY to .env for real analysis."
