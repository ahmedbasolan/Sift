import re

from fastapi import Request
from fastapi.responses import JSONResponse


def create_api_key_middleware(api_key: str):
    async def api_key_middleware(request: Request, call_next):
        if request.url.path in ["/health", "/docs", "/openapi.json"]:
            return await call_next(request)

        header_key = request.headers.get("x-api-key")
        if not header_key or header_key != api_key:
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing or invalid API key. Provide x-api-key header."},
            )
        return await call_next(request)

    return api_key_middleware


def validate_api_key(api_key: str) -> bool:
    if not api_key:
        return False
    if len(api_key) < 16:
        return False
    return re.match(r"^[a-zA-Z0-9_-]+$", api_key) is not None
