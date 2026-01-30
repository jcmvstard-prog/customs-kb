"""
Retry utilities with exponential backoff.
"""
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
import httpx

from src.config.settings import settings


def retry_on_http_error():
    """
    Decorator for retrying HTTP requests with exponential backoff.

    Retries on:
    - Connection errors
    - Timeout errors
    - 429 (Too Many Requests)
    - 503 (Service Unavailable)
    """
    return retry(
        stop=stop_after_attempt(settings.max_retries),
        wait=wait_exponential(multiplier=settings.retry_delay, min=1, max=10),
        retry=retry_if_exception_type((
            httpx.ConnectError,
            httpx.TimeoutException,
            httpx.HTTPStatusError
        )),
        reraise=True
    )
