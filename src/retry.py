import time
import random
import logging
from functools import wraps
from typing import Callable, Any, Tuple, Type

logger = logging.getLogger(__name__)


def retry_with_backoff(
    retries: int = 3,
    initial_delay: float = 2.0,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,)
) -> Callable:
    """
    Decorator for retrying functions on transient failures with exponential backoff and jitter.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            current_delay = initial_delay
            last_exception = None

            for attempt in range(1, retries + 1):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e
                    if attempt == retries:
                        logger.error(f"[{func.__name__}] Failed after {retries} attempts: {e}")
                        raise

                    sleep_time = current_delay
                    if jitter:
                        sleep_time += random.uniform(0.1, 1.0)

                    logger.warning(
                        f"[{func.__name__}] Attempt {attempt}/{retries} failed with error: {e}. "
                        f"Retrying in {sleep_time:.2f}s..."
                    )
                    time.sleep(sleep_time)
                    current_delay *= backoff_factor

            raise last_exception
        return wrapper
    return decorator
