"""
TapController — thin HTTP layer. Extracts the real client IP (respecting
X-Forwarded-For from Caddy, since Tap itself only ever sees Caddy's own
loopback address as the raw connection source), delegates to TapService,
and passes through Wellspring's status codes/bodies unchanged.
"""

import logging
from typing import Any, Callable

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from service.tap_service import TapService, RateLimitExceededError
from client.wellspring_client import WellspringUnavailableError
from util.client_ip import get_client_ip
from controller.request_logging_middleware import RequestLoggingMiddleware

logger = logging.getLogger(__name__)


def create_app(tap_service: TapService) -> FastAPI:
    app = FastAPI(title="Tap")

    # Order matters: middleware registered LAST wraps OUTERMOST, so it
    # sees the request first / response last. Logging is added last so
    # it captures the true final status code (e.g. after CORS handling)
    # and full end-to-end latency.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["GET"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestLoggingMiddleware)

    def call(service_fn: Callable[..., tuple[int, dict[str, Any]]], *args: Any) -> JSONResponse:
        """
        Shared error-handling wrapper for every route below: calls the
        given TapService method, converts Tap-level failures (rate
        limit, Wellspring unreachable) into HTTP errors, and passes
        Wellspring's own status code/body straight through otherwise.
        """
        try:
            status_code, body = service_fn(*args)
            return JSONResponse(content=body, status_code=status_code)
        except RateLimitExceededError:
            raise HTTPException(status_code=429, detail="Rate limit exceeded, try again later")
        except WellspringUnavailableError:
            raise HTTPException(status_code=502, detail="Entropy source unavailable")

    @app.get("/bits")
    def handle_get_bits(request: Request, num_bytes: int = Query(64, gt=0), plot: bool = False):
        ip = get_client_ip(request)
        return call(tap_service.get_bits, ip, num_bytes, plot)

    @app.get("/beacon/latest")
    def handle_get_beacon_latest(request: Request):
        ip = get_client_ip(request)
        return call(tap_service.get_beacon_latest, ip)

    @app.get("/beacon/pulse/{pulse_index}")
    def handle_get_beacon_by_index(request: Request, pulse_index: int):
        ip = get_client_ip(request)
        return call(tap_service.get_beacon_by_index, ip, pulse_index)

    @app.get("/beacon/at")
    def handle_get_beacon_by_timestamp(request: Request, timestamp: str = Query(...)):
        ip = get_client_ip(request)
        return call(tap_service.get_beacon_by_timestamp, ip, timestamp)

    @app.get("/stats/hour")
    def handle_get_stats_hour(request: Request):
        ip = get_client_ip(request)
        return call(tap_service.get_stats_hour, ip)

    @app.get("/stats/day")
    def handle_get_stats_day(request: Request):
        ip = get_client_ip(request)
        return call(tap_service.get_stats_day, ip)

    @app.get("/metrics")
    def handle_get_metrics(request: Request):
        ip = get_client_ip(request)
        return call(tap_service.get_metrics, ip)

    @app.get("/health")
    def handle_health():
        # Tap's own liveness, deliberately NOT dependent on Wellspring
        # being reachable -- this should always return 200 as long as
        # the Tap process itself is up, so it's useful for uptime
        # monitoring independent of VPN/Wellspring status.
        return {"status": "ok", "service": "tap"}

    return app