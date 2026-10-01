import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings


def _allowed_origin(origin):
    """Return the origin value to echo in Access-Control-Allow-Origin, or None.

    Only exact matches against the configured allow-list are accepted. There is
    intentionally no wildcard support: echoing "*" together with
    Access-Control-Allow-Credentials is invalid per the CORS spec and unsafe.
    """
    if not origin:
        return None
    if origin not in settings.CORS_ORIGINS:
        return None
    return origin


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id

        origin = request.headers.get("origin")
        allowed = _allowed_origin(origin)

        if request.method == "OPTIONS" and allowed:
            response = Response(status_code=200)
            response.headers["X-Request-ID"] = request_id
            response.headers["Access-Control-Allow-Origin"] = allowed
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, PATCH, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Request-ID"
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Vary"] = "Origin"
            return response

        response: Response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        if allowed:
            response.headers["Access-Control-Allow-Origin"] = allowed
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, PATCH, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Request-ID"
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Vary"] = "Origin"
        return response
