"""Small, privacy-conscious HTTP foundation for generated development services.

No request bodies, query strings, client IPs, secrets, or exception details are
logged. X-Request-ID is server-created, not trusted from incoming headers.
"""
import json
import logging
import os
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

_LOGGER = logging.getLogger("aet.request")
if not _LOGGER.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(message)s"))
    _LOGGER.addHandler(_handler)
_LOGGER.propagate = False

_KNOWN_PATHS = frozenset({"/invoke", "/ask", "/health", "/ready"})


def install_foundations(app: FastAPI) -> None:
    """Register a single request middleware without changing public API schemas."""

    @app.middleware("http")
    async def request_foundation(request: Request, call_next):
        request_id = uuid4().hex
        started = perf_counter()
        failed = False
        try:
            response = await call_next(request)
        except Exception:
            failed = True
            response = JSONResponse(
                status_code=500, content={"detail": "Internal server error"}
            )
        response.headers["X-Request-ID"] = request_id

        # Avoid arbitrary route strings, query strings, headers and user content.
        path = request.url.path
        if path not in _KNOWN_PATHS:
            path = "<unmatched>"
        log_level = os.environ.get("AET_LOG_LEVEL", "INFO").upper()
        _LOGGER.setLevel(log_level if log_level in
                         {"DEBUG", "INFO", "WARNING", "ERROR"} else "INFO")
        _LOGGER.info(json.dumps({
            "event": "request_completed" if not failed else "request_failed",
            "request_id": request_id,
            "method": request.method,
            "route": path,
            "status_code": response.status_code,
            "duration_ms": round((perf_counter() - started) * 1000, 2),
        }, separators=(",", ":")))
        return response
