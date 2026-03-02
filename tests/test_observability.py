import json
import time
import unittest

from app.concurrency import ConcurrencyGuard
from app.logging_utils import get_logger
from app.orchestrator import run_parallel_analysis
from app.routes import execute_with_concurrency_guard


class ObservabilityTests(unittest.TestCase):
    def test_orchestrator_logs_request_id_and_tool_latency(self):
        logger = get_logger("app.test.observability.orchestrator")

        def fast_runner(_cluster_name, _start_time, _end_time):
            return {"status": "success", "data": {"ok": True}, "error": None}

        with self.assertLogs(logger.name, level="INFO") as captured:
            run_parallel_analysis(
                "cluster-a",
                "2026-01-13 09:00:00",
                "2026-01-13 09:30:00",
                tool_timeout_seconds=1,
                tool_runners={"network": fast_runner},
                logger=logger,
                request_id="req-orch-1",
            )

        payloads = [json.loads(record.getMessage()) for record in captured.records]
        self.assertTrue(
            any(
                item.get("request_id") == "req-orch-1" and "tool_latency_ms" in item
                for item in payloads
            )
        )

    def test_route_logs_rate_limit_hit(self):
        logger = get_logger("app.test.observability.route.rate_limit")
        guard = ConcurrencyGuard(limit=1)
        self.assertTrue(guard.acquire(blocking=False))

        try:
            with self.assertLogs(logger.name, level="INFO") as captured:
                body, status = execute_with_concurrency_guard(
                    guard,
                    lambda: ({"ok": True}, 200),
                    logger=logger,
                    request_id="req-route-1",
                )
        finally:
            guard.release()

        self.assertEqual(status, 429)
        self.assertEqual(body["error"], "too_many_requests")
        payloads = [json.loads(record.getMessage()) for record in captured.records]
        self.assertTrue(
            any(
                item.get("request_id") == "req-route-1"
                and item.get("rate_limit_hit") is True
                for item in payloads
            )
        )

    def test_route_logs_total_latency(self):
        logger = get_logger("app.test.observability.route.latency")
        guard = ConcurrencyGuard(limit=1)

        def handler():
            time.sleep(0.01)
            return {"ok": True}, 200

        with self.assertLogs(logger.name, level="INFO") as captured:
            body, status = execute_with_concurrency_guard(
                guard,
                handler,
                logger=logger,
                request_id="req-route-2",
            )

        self.assertEqual(status, 200)
        self.assertEqual(body["ok"], True)
        payloads = [json.loads(record.getMessage()) for record in captured.records]
        self.assertTrue(
            any(
                item.get("request_id") == "req-route-2"
                and item.get("rate_limit_hit") is False
                and "total_latency_ms" in item
                for item in payloads
            )
        )


if __name__ == "__main__":
    unittest.main()
