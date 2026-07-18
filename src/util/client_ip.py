"""
Shared client IP extraction. 
"""

from starlette.requests import Request


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        # Can be a comma-separated chain if multiple proxies are
        # involved; the first entry is the original client.
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"