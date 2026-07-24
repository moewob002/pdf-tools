import time
from collections import defaultdict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

RATE_LIMIT_WINDOW = 10
RATE_LIMIT_MAX = 5
PROCESSING_MIN_DELAY = 1.0


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, window=RATE_LIMIT_WINDOW, max_requests=RATE_LIMIT_MAX):
        super().__init__(app)
        self.window = window
        self.max_requests = max_requests
        self.requests: dict[str, list[float]] = defaultdict(list)
        self.last_request: dict[str, float] = {}

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

    async def dispatch(self, request, call_next):
        if request.url.path.startswith("/api/health"):
            return await call_next(request)

        ip = self._get_client_ip(request)
        now = time.time()

        if ip in self.last_request:
            elapsed = now - self.last_request[ip]
            if elapsed < PROCESSING_MIN_DELAY:
                wait = PROCESSING_MIN_DELAY - elapsed
                import asyncio
                await asyncio.sleep(wait)

        self.last_request[ip] = time.time()

        self._cleanup(ip)
        self.requests[ip].append(time.time())

        if len(self.requests[ip]) > self.max_requests:
            return JSONResponse(
                {"detail": "Too many requests. Please wait a moment before trying again."},
                status_code=429,
            )

        return await call_next(request)
