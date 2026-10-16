import unittest

from fastapi.testclient import TestClient

from app.main import app


class CorsTests(unittest.TestCase):
    def test_wildcard_origin_without_credentials(self):
        # Regression (SEC-11): "*" was combined with allow_credentials=True.
        r = TestClient(app).options(
            "/api/compress",
            headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "POST"},
        )
        self.assertEqual(r.headers.get("access-control-allow-origin"), "*")
        self.assertNotIn("access-control-allow-credentials", r.headers)


if __name__ == "__main__":
    unittest.main()
