from contextlib import contextmanager
from threading import BoundedSemaphore
from typing import Iterator


class ConcurrencyGuard:
    def __init__(self, limit: int = 10) -> None:
        if limit <= 0:
            raise ValueError("limit must be > 0")
        self.limit = limit
        self._semaphore = BoundedSemaphore(value=limit)

    def acquire(self, blocking: bool = False, timeout: float | None = None) -> bool:
        if timeout is None:
            return self._semaphore.acquire(blocking=blocking)
        return self._semaphore.acquire(blocking=blocking, timeout=timeout)

    def release(self) -> None:
        self._semaphore.release()

    @contextmanager
    def hold(self, blocking: bool = False, timeout: float | None = None) -> Iterator[bool]:
        acquired = self.acquire(blocking=blocking, timeout=timeout)
        try:
            yield acquired
        finally:
            if acquired:
                self.release()
