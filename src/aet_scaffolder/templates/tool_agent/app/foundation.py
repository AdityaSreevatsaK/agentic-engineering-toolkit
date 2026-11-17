"""Optional production security controls for the generated HTTP application.

Local mode preserves the offline demo. Hardened mode requires per-tenant bearer
keys and applies process-local request and concurrency limits. A trusted ingress
must still enforce TLS, distributed quotas and network isolation.
"""
import hmac
import ipaddress
import json
import logging
import os
import re
import traceback
from collections import deque
from pathlib import Path
from threading import Lock
from time import monotonic, perf_counter
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

_LOGGER = logging.getLogger("aet.request")
if not _LOGGER.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(message)s"))
    _LOGGER.addHandler(_handler)
_LOGGER.propagate = False

_KNOWN_PATHS = frozenset({"/invoke", "/ask", "/health", "/ready", "/provider-status"})
_PROTECTED_PATHS = frozenset({"/invoke", "/ask"})
_TENANT_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
_LOCK = Lock()
_GLOBAL_REQUESTS: deque[float] = deque()
_TENANT_REQUESTS: dict[str, deque[float]] = {}
_GLOBAL_DAILY_REQUESTS: deque[float] = deque()
_TENANT_DAILY_REQUESTS: dict[str, deque[float]] = {}
_TENANT_IN_FLIGHT: dict[str, int] = {}
_IN_FLIGHT = 0


def _positive_limit(name: str, default: int) -> int:
    try:
        value = int(os.environ.get(name, str(default)))
    except ValueError as exc:
        raise ValueError("Invalid security limit") from exc
    if not 1 <= value <= 100_000:
        raise ValueError("Invalid security limit")
    return value


def security_mode() -> str:
    mode = os.environ.get("AET_SECURITY_MODE", "local")
    if mode not in {"local", "hardened"}:
        raise ValueError("Invalid security mode")
    return mode


def check_security_ready() -> dict[str, str]:
    """Validate production keys and limits without contacting a paid provider."""
    if security_mode() == "local":
        return {}
    try:
        keys = json.loads(os.environ.get("AET_TENANT_KEYS_JSON", ""))
    except (ValueError, TypeError) as exc:
        raise ValueError("Invalid tenant credentials") from exc
    if (
        not isinstance(keys, dict) or not 1 <= len(keys) <= 100
        or any(
            not isinstance(tenant, str) or not _TENANT_ID.fullmatch(tenant)
            or not isinstance(secret, str) or len(secret) < 32
            or len(secret) > 512 or not secret.isascii()
            for tenant, secret in keys.items()
        )
        or len(set(keys.values())) != len(keys)
    ):
        raise ValueError("Invalid tenant credentials")
    _positive_limit("AET_TENANT_RATE_PER_MINUTE", 30)
    _positive_limit("AET_GLOBAL_RATE_PER_MINUTE", 300)
    _positive_limit("AET_MAX_CONCURRENT", 20)
    _positive_limit("AET_MAX_TENANT_CONCURRENT", 5)
    _positive_limit("AET_GLOBAL_DAILY_REQUEST_LIMIT", 1000)
    _positive_limit("AET_TENANT_DAILY_REQUEST_LIMIT", 100)
    return keys


def tenant_knowledge_path(default_path: str, tenant: str | None) -> str:
    """Isolate RAG data by authenticated tenant; never fall back to shared data."""
    if tenant is None:
        return default_path
    if not _TENANT_ID.fullmatch(tenant):
        raise ValueError("Invalid tenant")
    source = Path(default_path).expanduser()
    if not source.is_absolute():
        source = Path(__file__).resolve().parent.parent / source
    root = source.parent / "tenants"
    tenant_dir = root / tenant
    target = tenant_dir / source.name
    if root.is_symlink() or tenant_dir.is_symlink() or target.is_symlink():
        raise ValueError("Unsafe tenant corpus")
    if not target.resolve().is_relative_to(root.resolve()):
        raise ValueError("Unsafe tenant corpus")
    return str(target)


def _is_loopback_client(request: Request) -> bool:
    host = request.client.host if request.client else ""
    # Starlette's in-process TestClient does not have a network peer.
    if host == "testclient" and "PYTEST_CURRENT_TEST" in os.environ:
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def _authenticate(request: Request, keys: dict[str, str]) -> str | None:
    headers = request.headers.getlist("authorization")
    # Reject duplicate credentials: intermediaries may interpret them differently.
    if len(headers) != 1:
        return None
    header = headers[0]
    if not header.startswith("Bearer ") or len(header) > 520:
        return None
    token = header[7:].encode("utf-8")
    matched = None
    for tenant, secret in keys.items():
        if hmac.compare_digest(token, secret.encode("ascii")):
            matched = tenant
    return matched


def _reserve(tenant: str) -> int:
    """Reserve one request; return retry delay in seconds (zero means accepted).

    Daily counters impose a conservative process-local ceiling on calls that
    may incur model charges. They are not token or currency budgets.
    """
    global _IN_FLIGHT
    now = monotonic()
    with _LOCK:
        while _GLOBAL_REQUESTS and _GLOBAL_REQUESTS[0] <= now - 60:
            _GLOBAL_REQUESTS.popleft()
        requests = _TENANT_REQUESTS.setdefault(tenant, deque())
        while requests and requests[0] <= now - 60:
            requests.popleft()
        while _GLOBAL_DAILY_REQUESTS and _GLOBAL_DAILY_REQUESTS[0] <= now - 86_400:
            _GLOBAL_DAILY_REQUESTS.popleft()
        daily = _TENANT_DAILY_REQUESTS.setdefault(tenant, deque())
        while daily and daily[0] <= now - 86_400:
            daily.popleft()
        if (
            len(_GLOBAL_DAILY_REQUESTS) >= _positive_limit("AET_GLOBAL_DAILY_REQUEST_LIMIT", 1000)
            or len(daily) >= _positive_limit("AET_TENANT_DAILY_REQUEST_LIMIT", 100)
        ):
            return 86_400
        if (
            len(_GLOBAL_REQUESTS) >= _positive_limit("AET_GLOBAL_RATE_PER_MINUTE", 300)
            or len(requests) >= _positive_limit("AET_TENANT_RATE_PER_MINUTE", 30)
            or _IN_FLIGHT >= _positive_limit("AET_MAX_CONCURRENT", 20)
            or _TENANT_IN_FLIGHT.get(tenant, 0)
            >= _positive_limit("AET_MAX_TENANT_CONCURRENT", 5)
        ):
            return 60
        _GLOBAL_REQUESTS.append(now)
        requests.append(now)
        _GLOBAL_DAILY_REQUESTS.append(now)
        daily.append(now)
        _IN_FLIGHT += 1
        _TENANT_IN_FLIGHT[tenant] = _TENANT_IN_FLIGHT.get(tenant, 0) + 1
        return 0


def _release(tenant: str) -> None:
    global _IN_FLIGHT
    with _LOCK:
        _IN_FLIGHT -= 1
        remaining = _TENANT_IN_FLIGHT[tenant] - 1
        if remaining:
            _TENANT_IN_FLIGHT[tenant] = remaining
        else:
            del _TENANT_IN_FLIGHT[tenant]


def install_foundations(app: FastAPI) -> None:
    """Add sanitised logging, local-only live access and opt-in tenant controls."""

    @app.middleware("http")
    async def request_foundation(request: Request, call_next):
        request_id = uuid4().hex
        started = perf_counter()
        exception_type = None
        stack = None
        reserved_tenant = None
        try:
            if request.url.path in _PROTECTED_PATHS:
                mode = security_mode()
                if mode == "hardened":
                    keys = check_security_ready()
                    tenant = _authenticate(request, keys)
                    if tenant is None:
                        response = JSONResponse(status_code=401, content={"detail": "Authentication required"})
                        response.headers["WWW-Authenticate"] = "Bearer"
                    else:
                        retry_after = _reserve(tenant)
                        if retry_after:
                            response = JSONResponse(status_code=429, content={"detail": "Request limit exceeded"})
                            response.headers["Retry-After"] = str(retry_after)
                        else:
                            reserved_tenant = tenant
                            request.state.tenant_id = tenant
                            response = await call_next(request)
                else:
                    # Never permit remote clients to spend live-provider capacity
                    # with the unauthenticated reference profile.
                    from .config import get_settings
                    if get_settings().provider != "mock" and not _is_loopback_client(request):
                        response = JSONResponse(status_code=403, content={"detail": "Hardened security mode required"}
                        )
                    else:
                        request.state.tenant_id = None
                        response = await call_next(request)
            else:
                response = await call_next(request)
        except ValueError:
            response = JSONResponse(status_code=503, content={"detail": "Invalid service configuration"})
        except Exception as exc:
            exception_type = type(exc).__name__
            if os.environ.get("AET_OPERATOR_STACK_FRAMES") == "1":
                # Frame metadata only: no SDK exception strings or source lines.
                stack = [
                    {"file": Path(frame.filename).name, "function": frame.name,
                     "line": frame.lineno}
                    for frame in traceback.extract_tb(exc.__traceback__)[-8:]
                ]
            response = JSONResponse(status_code=500, content={"detail": "Internal server error"})
        finally:
            if reserved_tenant is not None:
                _release(reserved_tenant)
        response.headers["X-Request-ID"] = request_id
        path = request.url.path
        if path not in _KNOWN_PATHS:
            path = "<unmatched>"
        log_level = os.environ.get("AET_LOG_LEVEL", "INFO").upper()
        _LOGGER.setLevel(log_level if log_level in
                         {"DEBUG", "INFO", "WARNING", "ERROR"} else "INFO")
        event = {
            "event": "request_failed" if response.status_code >= 500 else "request_completed",
            "request_id": request_id,
            "method": request.method,
            "route": path,
            "status_code": response.status_code,
            "duration_ms": round((perf_counter() - started) * 1000, 2),
        }
        if exception_type is not None:
            event["exception_type"] = exception_type
        if stack is not None:
            event["stack_frames"] = stack
        _LOGGER.info(json.dumps(event, separators=(",", ":")))
        return response
