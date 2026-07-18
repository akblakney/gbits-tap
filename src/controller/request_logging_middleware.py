"""
"""

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from util.client_ip import get_client_ip

logger = logging.getLogger("tap.access")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.monotonic()
        client_ip = get_client_ip(request)
        full_path = request.url.path + (f"?{request.url.query}" if request.url.query else "")

        response = await call_next(request)

        elapsed_ms = (time.monotonic() - start) * 1000
        logger.info(
            "%s %s -> %d (%.1fms) ip=%s ua=%s",
            request.method,
            full_path,
            response.status_code,
            elapsed_ms,
            client_ip,
            request.headers.get("user-agent", "-"),
        )
        return response