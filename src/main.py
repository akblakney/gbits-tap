"""
Tap entrypoint.

Run from inside src/: `python main.py`
"""

import argparse

import uvicorn

from client.wellspring_client import WellspringClient
from util.rate_limiter import RateLimiter
from service.tap_service import TapService
from controller.controller import create_app
from config import config
from config.logging_config import configure_logging


def parse_args():
    parser = argparse.ArgumentParser(description="Tap server")
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Shortcut for --log-level=DEBUG",
    )
    parser.add_argument(
        "--log-level",
        default=None,
        help="Logging level (DEBUG, INFO, WARNING, ERROR). "
             "Overrides TAP_LOG_LEVEL env var if set.",
    )
    return parser.parse_args()


def build_app():
    wellspring_client = WellspringClient()
    rate_limiter = RateLimiter(
        max_requests=config.RATE_LIMIT_REQUESTS,
        window_seconds=config.RATE_LIMIT_WINDOW_SECONDS,
    )
    tap_service = TapService(wellspring_client, rate_limiter)
    return create_app(tap_service)


if __name__ == "__main__":
    args = parse_args()
    configure_logging(level="DEBUG" if args.debug else args.log_level)
    app = build_app()
    uvicorn.run(app, host=config.API_HOST, port=config.API_PORT, log_config=None)
else:
    configure_logging()
    app = build_app()
