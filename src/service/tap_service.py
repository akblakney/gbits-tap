"""
TapService — policy layer. Checks rate limits, then delegates to
WellspringClient. Controller stays thin; this is where "is this
request allowed" lives.
"""

import logging
from typing import Any

from client.wellspring_client import WellspringClient
from util.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


class RateLimitExceededError(Exception):
    pass


class TapService:
    def __init__(self, wellspring_client: WellspringClient, rate_limiter: RateLimiter):
        self._wellspring_client = wellspring_client
        self._rate_limiter = rate_limiter

    def get_bits(self, client_ip: str, num_bytes: int, plot: bool) -> tuple[int, dict[str, Any]]:
        self._check_rate_limit(client_ip)
        return self._wellspring_client.get_bits(num_bytes, plot)

    def get_beacon_latest(self, client_ip: str) -> tuple[int, dict[str, Any]]:
        self._check_rate_limit(client_ip)
        return self._wellspring_client.get_beacon_latest()

    def get_beacon_by_index(self, client_ip: str, pulse_index: int) -> tuple[int, dict[str, Any]]:
        self._check_rate_limit(client_ip)
        return self._wellspring_client.get_beacon_by_index(pulse_index)

    def get_beacon_by_timestamp(self, client_ip: str, timestamp_iso: str) -> tuple[int, dict[str, Any]]:
        self._check_rate_limit(client_ip)
        return self._wellspring_client.get_beacon_by_timestamp(timestamp_iso)

    def get_stats_hour(self, client_ip: str) -> tuple[int, dict[str, Any]]:
        self._check_rate_limit(client_ip)
        return self._wellspring_client.get_stats_hour()

    def get_stats_day(self, client_ip: str) -> tuple[int, dict[str, Any]]:
        self._check_rate_limit(client_ip)
        return self._wellspring_client.get_stats_day()

    def get_metrics(self, client_ip: str) -> tuple[int, dict[str, Any]]:
        self._check_rate_limit(client_ip)
        return self._wellspring_client.get_metrics()

    def _check_rate_limit(self, client_ip: str) -> None:
        if not self._rate_limiter.allow(client_ip):
            logger.warning("Rate limit exceeded for %s", client_ip)
            raise RateLimitExceededError(f"Rate limit exceeded for {client_ip}")
