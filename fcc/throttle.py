import asyncio
import time
from typing import Optional


class TokenBucket:
    """Rate-limiting async token bucket."""

    def __init__(self, rate: float, capacity: float, interval: float = 0.5):
        """Create token bucket replenished at `rate` up to `capacity`.

        Args:
            rate - Number of tokens to replenish (tokens per second)
            capacity - Max number of tokens
            interval - Frequency to replenish tokens
        """
        # Current number of tokens
        self.level = capacity
        # Max number of tokens
        self.capacity = capacity
        # Token replenish rate, per second
        self.rate = rate
        # Frequency to replenish
        self.interval = interval

        # Timestamp of last token addition
        self._last_add = time.monotonic()
        # Synchronization for token requesters
        self._cv = asyncio.Condition()
        # Scheduled replenishment task.
        self._timer: Optional[asyncio.Task] = None

    async def consume(self, n: float):
        """Take `n` tokens from the bucket.

        Blocks until tokens are available.

        Args:
            n - Number of tokens (can be fractional)
        """
        while True:
            async with self._cv:
                # Ensure bucket is topped off
                self._fill()
                # Check if tokens are available
                if n > self.level:
                    # Make sure a replenishment task is scheduled
                    self._schedule()
                    # Block indefinitely until woken by a replenishment task
                    await self._cv.wait()
                    continue
                else:
                    self.level -= n
                    return

    def _schedule(self):
        """Ensure that a replenishment task is scheduled.

        If one is scheduled already, this is a no-op.
        """
        if self._timer:
            return
        self._timer = asyncio.create_task(self._fill_after(self.interval))

    async def _fill_after(self, timeout: float):
        """Replenish the token bucket after napping for an interval.

        Args:
            timeout - Time in seconds to sleep before replenishing
        """
        await asyncio.sleep(timeout)
        async with self._cv:
            # Fill up the bucket now
            self._fill()
            # Wake up a few sleeping tasks. Note that the token level is often
            # fractional, so we round it. We also add an extra sleeping
            # coroutine to wake. This guarantees that if there are more tasks
            # sleeping than we have tokens for, the last awakened task will
            # call `_schedule` again to replenish another time. That way we
            # don't have to explicitly keep track of exactly who's waiting.
            #
            # Lastly, a task might request multiple tokens. That just means
            # that we are waking even more tasks than we need to. But
            # ultimately they will just go back to sleep and try again on the
            # next replenishment.
            self._cv.notify(n=int(self.level) + 1)
            self._timer = None

    def _fill(self):
        """Add new tokens to the bucket.

        Tokens are often fractional, as they are prorated based on the last
        replenishment. Eventually the tokens are limited by the capacity.
        """
        t = time.monotonic()
        delta = t - self._last_add
        self.level = min(self.capacity, self.level + delta * self.rate)
        self._last_add = t


class Throttle:
    """A limiter for both rate and concurrency.

    Rate limiting uses a token bucket to ensure no more than X operations
    happen per second. Additionally, concurrency is limited so that only Y
    operations can happen concurrently.
    """

    def __init__(self, rate: float, concurrency: int):
        """Create a limiter for frequency and concurrency.

        Args:
            rate - Number of ops per second
            concurrency - Number of concurrent ops
        """
        self.sem = asyncio.Semaphore(concurrency)
        self.bucket = TokenBucket(rate, rate)

    async def acquire(self):
        """Wait until throttle has capacity for this request."""
        await self.sem.acquire()
        await self.bucket.consume(1)

    def release(self):
        """Release the lock."""
        self.sem.release()

    async def __aenter__(self):
        """Enter async context."""
        await self.acquire()

    async def __aexit__(self, exc_t, exc_v, exc_tb):
        """Exit the async context."""
        self.release()
