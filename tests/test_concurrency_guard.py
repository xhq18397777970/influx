import unittest

from app.concurrency import ConcurrencyGuard
from app.routes import execute_with_concurrency_guard


class ConcurrencyGuardTests(unittest.TestCase):
    def test_guard_rejects_over_limit(self):
        guard = ConcurrencyGuard(limit=10)

        acquired = [guard.acquire(blocking=False) for _ in range(10)]
        self.assertTrue(all(acquired))
        self.assertFalse(guard.acquire(blocking=False))

        for _ in range(10):
            guard.release()

    def test_release_allows_next_acquire(self):
        guard = ConcurrencyGuard(limit=1)
        self.assertTrue(guard.acquire(blocking=False))
        self.assertFalse(guard.acquire(blocking=False))

        guard.release()
        self.assertTrue(guard.acquire(blocking=False))
        guard.release()

    def test_execute_returns_429_when_limited(self):
        guard = ConcurrencyGuard(limit=1)
        self.assertTrue(guard.acquire(blocking=False))

        def handler():
            return {"ok": True}, 200

        body, status = execute_with_concurrency_guard(guard, handler)
        self.assertEqual(status, 429)
        self.assertEqual(body["error"], "too_many_requests")

        guard.release()

    def test_execute_releases_on_exception(self):
        guard = ConcurrencyGuard(limit=1)

        def bad_handler():
            raise RuntimeError("boom")

        with self.assertRaises(RuntimeError):
            execute_with_concurrency_guard(guard, bad_handler)

        self.assertTrue(guard.acquire(blocking=False))
        guard.release()


if __name__ == "__main__":
    unittest.main()
