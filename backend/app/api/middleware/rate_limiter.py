import time
from collections import defaultdict

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from app.utils.logger import get_logger

logger = get_logger(__name__)

DEFAULT_LIMIT = 60
DEFAULT_WINDOW = 60
# 모니터링/생존 확인용 엔드포인트는 rate limit 대상에서 제외한다.
DEFAULT_EXEMPT_PREFIXES = ("/api/v1/health",)


class RateLimiterMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        *,
        limit: int = DEFAULT_LIMIT,
        window: int = DEFAULT_WINDOW,
        exempt_prefixes: tuple[str, ...] = DEFAULT_EXEMPT_PREFIXES,
    ) -> None:
        self.app = app
        self._limit = limit
        self._window = window
        self._exempt_prefixes = exempt_prefixes
        self._requests: dict[str, list[float]] = defaultdict(list)
        self._request_count: int = 0
        self._full_cleanup_interval: int = 100

    def _get_client_ip(self, scope: Scope) -> str:
        headers = dict(scope.get("headers", []))
        forwarded = headers.get(b"x-forwarded-for", b"").decode()
        if forwarded:
            return forwarded.split(",")[0].strip()
        client = scope.get("client")
        return client[0] if client else "unknown"

    def _cleanup(self, ip: str, now: float) -> None:
        cutoff = now - self._window
        self._requests[ip] = [t for t in self._requests[ip] if t > cutoff]

    def _full_cleanup(self, now: float) -> None:
        stale_cutoff = now - self._window * 2
        stale_ips = [
            ip
            for ip, timestamps in self._requests.items()
            if not timestamps or timestamps[-1] <= stale_cutoff
        ]
        for ip in stale_ips:
            del self._requests[ip]

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        if any(path.startswith(prefix) for prefix in self._exempt_prefixes):
            await self.app(scope, receive, send)
            return

        ip = self._get_client_ip(scope)
        now = time.monotonic()
        self._cleanup(ip, now)

        self._request_count += 1
        if self._request_count % self._full_cleanup_interval == 0:
            self._full_cleanup(now)

        if len(self._requests[ip]) >= self._limit:
            logger.warning("Rate limit exceeded: %s", ip)
            response = JSONResponse(
                status_code=429,
                content={"success": False, "error": "Too many requests"},
                headers={"Retry-After": str(self._window)},
            )
            await response(scope, receive, send)
            return

        self._requests[ip].append(now)
        await self.app(scope, receive, send)
