"""Retry utilities for handling transient failures"""
import asyncio
import logging
from typing import Callable, TypeVar, Any
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')


async def retry_async(
    func: Callable[..., T],
    *args,
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
    **kwargs
) -> T:
    """
    Retry an async function with exponential backoff

    Args:
        func: Async function to retry
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay (exponential backoff)
        exceptions: Tuple of exceptions to catch and retry
        *args, **kwargs: Arguments to pass to func

    Returns:
        Result of the function call

    Raises:
        Last exception if all retries fail
    """
    last_exception = None
    current_delay = delay

    for attempt in range(max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except exceptions as e:
            last_exception = e

            if attempt < max_retries:
                logger.warning(
                    f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}: {e}. "
                    f"Retrying in {current_delay:.1f}s..."
                )
                await asyncio.sleep(current_delay)
                current_delay *= backoff
            else:
                logger.error(
                    f"All {max_retries + 1} attempts failed for {func.__name__}: {e}"
                )

    # This should never be reached, but for type safety
    raise last_exception if last_exception else RuntimeError("Retry failed")


def with_retry(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    Decorator to add retry logic to async functions

    Usage:
        @with_retry(max_retries=3, delay=1.0, exceptions=(DockerException,))
        async def my_docker_operation():
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await retry_async(
                func,
                *args,
                max_retries=max_retries,
                delay=delay,
                backoff=backoff,
                exceptions=exceptions,
                **kwargs
            )
        return wrapper
    return decorator
