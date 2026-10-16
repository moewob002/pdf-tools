import os

# Keep the rate limiter out of the way of API tests; must run before app.config is imported.
os.environ.setdefault("RATE_LIMIT_MAX", "100000")
os.environ.setdefault("RATE_LIMIT_DELAY", "0")
