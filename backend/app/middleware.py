import asyncio
import time
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from .config import RATE_LIMIT_DELAY, RATE_LIMIT_MAX

RATE_LIMIT_WINDOW = 10


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        window=RATE_LIMIT_WINDOW,
        max_requests=RATE_LIMIT_MAX,
        min_delay=RATE_LIMIT_DELAY,
    ):
        super().__init__(app)
        self.window = window
        self.max_requests = max_requests
        self.min_delay = min_delay
        self.requests: dict[str, list[float]] = defaultdict(list)
        self.last_request: dict[str, float] = {}
        self._last_sweep = time.time()

    def _get_client_ip(self, request):
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _cleanup(self, ip):
        now = time.time()
        self.requests[ip] = [
            t for t in self.requests[ip] if now - t < self.window
        ]

    def _sweep(self, now):
        """Forget clients with no requests inside the window so state cannot grow forever."""
        if now - self._last_sweep < self.window:
            return
        self._last_sweep = now
        for ip in list(self.last_request):
            if now - self.last_request[ip] >= max(self.window, self.min_delay):
                self.last_request.pop(ip, None)
                self.requests.pop(ip, None)

    async def dispatch(self, request, call_next):
        if request.url.path.startswith("/api/health"):
            return await call_next(request)

        ip = self._get_client_ip(request)
        now = time.time()
        self._sweep(now)

        if ip in self.last_request:
            elapsed = now - self.last_request[ip]
            if elapsed < self.min_delay:
                await asyncio.sleep(self.min_delay - elapsed)

        self.last_request[ip] = time.time()

        self._cleanup(ip)
        self.requests[ip].append(time.time())

        if len(self.requests[ip]) > self.max_requests:
            return JSONResponse(
                {"detail": "Too many requests. Please wait a moment before trying again."},
                status_code=429,
            )

        return await call_next(request)
