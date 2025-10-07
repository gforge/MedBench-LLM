"""Rate limiting utility for API calls."""

import time
from typing import Optional


class RateLimiter:
    """Rate limiter to control API call frequency.

    Ensures a minimum time interval between successive operations,
    useful for respecting API rate limits.

    Attributes:
        seconds_between_calls: Minimum seconds to wait between calls
    """

    def __init__(self, seconds_between_calls: int):
        """Initialize rate limiter.

        Args:
            seconds_between_calls: Minimum seconds to wait between calls
        """
        self.seconds_between_calls = seconds_between_calls
        self._last_call_time: Optional[float] = None

    def wait_if_needed(self) -> None:
        """Wait if needed to respect rate limit.

        Calculates elapsed time since last call and sleeps if necessary
        to maintain the minimum interval between calls.
        """
        if self._last_call_time is None:
            self._last_call_time = time.time()
            return

        elapsed_time = time.time() - self._last_call_time
        if elapsed_time < self.seconds_between_calls:
            sleep_time = self.seconds_between_calls - elapsed_time
            time.sleep(sleep_time)

        self._last_call_time = time.time()

    def reset(self) -> None:
        """Reset the rate limiter, clearing the last call time."""
        self._last_call_time = None
