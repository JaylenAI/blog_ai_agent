import time
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.utils.logger import get_logger

logger = get_logger(__name__)

DEFAULT_LIMIT = 60
DEFAULT_WINDOW = 60


class RateLimiterMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, *, limit: int = DEFAULT_LIMIT, window: int = DEFAULT_WINDOW):
        super().__init__(app)
        self._limit = limit
        self._window = window
        self._requests: dict[str, list[float]] = defaultdict(list)
        self._request_count: int = 0
        self._full_cleanup_interval: int = 100

    def _get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _cleanup(self, ip: str, now: float) -> None:
        cutoff = now - self._window
        self._requests[ip] = [t for t in self._requests[ip] if t > cutoff]

    def _full_cleanup(self, now: float) -> None:
        stale_cutoff = now - self._window * 2
        stale_ips = [
            ip for ip, timestamps in self._requests.items()
            if not timestamps or timestamps[-1] <= stale_cutoff
        ]
        for ip in stale_ips:
            del self._requests[ip]

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        ip = self._get_client_ip(request)
        now = time.monotonic()
        self._cleanup(ip, now)

        self._request_count += 1
        if self._request_count % self._full_cleanup_interval == 0:
            self._full_cleanup(now)

        if len(self._requests[ip]) >= self._limit:
            logger.warning("Rate limit exceeded: %s", ip)
            return JSONResponse(
                status_code=429,
                content={"success": False, "error": "Too many requests"},
                headers={"Retry-After": str(self._window)},
            )

        self._requests[ip].append(now)
        return await call_next(request)
