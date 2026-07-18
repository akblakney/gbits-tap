import logging
from typing import Any

import requests
from requests import Response

from config import config

logger = logging.getLogger(__name__)


class WellspringUnavailableError(Exception):
    """Raised when Wellspring can't be reached at all (network/timeout),
    as opposed to Wellspring responding with an error status code."""
    pass


class WellspringClient:
    def __init__(
        self,
        base_url: str | None = None,
        shared_secret: str | None = None,
        timeout: float | None = None,
    ):
        self._base_url = (base_url if base_url is not None else config.WELLSPRING_BASE_URL).rstrip("/")
        self._shared_secret = shared_secret if shared_secret is not None else config.WELLSPRING_SHARED_SECRET
        self._timeout = timeout if timeout is not None else config.WELLSPRING_REQUEST_TIMEOUT_SECONDS

    def get_bits(self, num_bytes: int, plot: bool = False) -> tuple[int, dict[str, Any]]:
        return self._get("/bits", params={"num_bytes": num_bytes, "plot": plot})

    def get_beacon_latest(self) -> tuple[int, dict[str, Any]]:
        return self._get("/beacon/latest")

    def get_beacon_by_index(self, pulse_index: int) -> tuple[int, dict[str, Any]]:
        return self._get(f"/beacon/pulse/{pulse_index}")

    def get_beacon_by_timestamp(self, timestamp_iso: str) -> tuple[int, dict[str, Any]]:
        return self._get("/beacon/at", params={"timestamp": timestamp_iso})

    def get_stats_hour(self) -> tuple[int, dict[str, Any]]:
        return self._get("/stats/hour")

    def get_stats_day(self) -> tuple[int, dict[str, Any]]:
        return self._get("/stats/day")

    def get_metrics(self) -> tuple[int, dict[str, Any]]:
        return self._get("/metrics")

    def get_wellspring_health(self) -> tuple[int, dict[str, Any]]:
        return self._get("/health")

    def _get(self, path: str, params: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
        """
        Returns (status_code, json_body) 
        """
        url = f"{self._base_url}{path}"
        headers = {}
        if self._shared_secret:
            headers["Authorization"] = f"Bearer {self._shared_secret}"

        try:
            response: Response = requests.get(url, params=params, headers=headers, timeout=self._timeout)
        except requests.RequestException as e:
            logger.error("Failed to reach Wellspring at %s: %s", url, e)
            raise WellspringUnavailableError(f"Could not reach Wellspring: {e}") from e

        try:
            body = response.json()
        except ValueError:
            body = {"detail": response.text}

        return response.status_code, body
