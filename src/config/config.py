"""
Central configuration for Tap.
"""

import os

# Wellspring is only reachable over the WireGuard tunnel, at its wg0
# address -- never a public IP. Override via env var for local testing
# against a stub.
WELLSPRING_BASE_URL = os.environ.get("WELLSPRING_BASE_URL", "http://10.8.0.2:8000")

# Shared secret sent as a Bearer token on every call to Wellspring.
# Wellspring must be configured to check for the same value. Empty
# string = no auth header sent (fine for local testing, NOT for
# production -- set WELLSPRING_SHARED_SECRET before going public).
WELLSPRING_SHARED_SECRET = os.environ.get("WELLSPRING_SHARED_SECRET", "")

WELLSPRING_REQUEST_TIMEOUT_SECONDS = 5.0

# Caddy runs on the same VPS and reverse-proxies to this -- Tap itself
# should never be reachable directly from the public internet.
API_HOST = "127.0.0.1"
API_PORT = 8000

# Per-client-IP rate limiting (see util/rate_limiter.py).
RATE_LIMIT_REQUESTS = 30
RATE_LIMIT_WINDOW_SECONDS = 60
