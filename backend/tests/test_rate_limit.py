import importlib
import os
import time
import unittest
from unittest import mock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.middleware import RateLimitMiddleware


def _client(**kwargs) -> TestClient:
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware, **kwargs)

    @app.get("/api/ping")
    async def ping():
        return {"ok": True}

    return TestClient(app)


class RateLimitTests(unittest.TestCase):
    def test_limits_after_max_requests(self):
        client = _client(max_requests=3, min_delay=0)
        codes = [client.get("/api/ping").status_code for _ in range(5)]
        self.assertEqual(codes, [200, 200, 200, 429, 429])

    def test_min_delay_is_applied(self):
        client = _client(max_requests=10, min_delay=0.3)
        client.get("/api/ping")
        start = time.perf_counter()
        client.get("/api/ping")
        self.assertGreaterEqual(time.perf_counter() - start, 0.25)

    def test_defaults_come_from_config(self):
        # Regression (SEC-04): RATE_LIMIT_MAX / RATE_LIMIT_DELAY used to be ignored.
        with mock.patch.dict(os.environ, {"RATE_LIMIT_MAX": "2", "RATE_LIMIT_DELAY": "0"}):
            import app.config
            import app.middleware

            importlib.reload(app.config)
            middleware_module = importlib.reload(app.middleware)
            try:
                app_ = FastAPI()
                app_.add_middleware(middleware_module.RateLimitMiddleware)

                @app_.get("/api/ping")
                async def ping():
                    return {}

                client = TestClient(app_)
                codes = [client.get("/api/ping").status_code for _ in range(3)]
                self.assertEqual(codes, [200, 200, 429])
            finally:
                importlib.reload(app.config)
                importlib.reload(app.middleware)

    def test_idle_clients_are_forgotten(self):
        # Regression (SEC-05): per-IP state used to grow without bound.
        app = FastAPI()
        middleware = RateLimitMiddleware(app, window=10, max_requests=5, min_delay=0)
        middleware.last_request = {"1.1.1.1": 0.0, "2.2.2.2": 0.0}
        middleware.requests.update({"1.1.1.1": [0.0], "2.2.2.2": [0.0]})
        middleware._last_sweep = 0.0
        middleware._sweep(now=1000.0)
        self.assertEqual(middleware.last_request, {})
        self.assertEqual(dict(middleware.requests), {})

    def test_health_is_not_limited(self):
        app = FastAPI()
        app.add_middleware(RateLimitMiddleware, max_requests=1, min_delay=0)

        @app.get("/api/health")
        async def health():
            return {}

        client = TestClient(app)
        codes = {client.get("/api/health").status_code for _ in range(5)}
        self.assertEqual(codes, {200})


if __name__ == "__main__":
    unittest.main()
