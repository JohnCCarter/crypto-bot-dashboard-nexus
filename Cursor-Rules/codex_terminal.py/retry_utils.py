import time
import random
from typing import Callable, Type, Tuple, Any
import openai


def retry_with_exponential_backoff(
    func: Callable,
    initial_delay: float = 1,
    exponential_base: float = 2,
    jitter: bool = True,
    max_retries: int = 6,
    max_sleep_time: float = 60,
    errors: Tuple[Type[Exception], ...] = (
        openai.RateLimitError,
        openai.APIError
    ),
) -> Callable:
    """Retries a function call with exponential backoff and optional jitter.

    Args:
        func: The function to be retried. Expected to be a callable with the
            signature `Callable[..., Any]`.
        initial_delay: Initial delay before retrying, in seconds.
        exponential_base: Base for exponential backoff calculation.
        jitter: If True, applies random jitter to the sleep time.
        max_retries: Maximum number of retry attempts.
        max_sleep_time: Maximum cap for sleep time in seconds.
        errors: Tuple of exception types to catch and retry on.

    Returns:
        The result of the function call if successful.

    Raises:
        RuntimeError: If the maximum number of retries is exceeded.
        Exception: If an unexpected error occurs.
    """
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        num_retries = 0
        delay = initial_delay

        while True:
            try:
                return func(*args, **kwargs)

            except errors as e:
                num_retries += 1
                if num_retries > max_retries:
                    raise RuntimeError(
                        f"Maximum number of retries exceeded ({max_retries})."
                    ) from e

                sleep_time = min(
                    delay * (exponential_base ** num_retries),
                    max_sleep_time
                )
                
                if jitter:
                    sleep_time *= random.uniform(0.5, 1.5)

                print(
                    f"Rate limit reached. Attempt {num_retries}, "
                    f"waiting {sleep_time:.2f} seconds..."
                )
                time.sleep(sleep_time)

            except Exception as e:
                print(f"An unexpected error occurred: {e}")
                raise

    return wrapper
