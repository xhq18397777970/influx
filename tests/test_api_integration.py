import unittest
from unittest.mock import patch

from app import create_app
from app.orchestrator import TOOL_RUNNERS


def _build_tool_runners(status_map):
    runners = {}
    for tool_name in ("network", "code", "cpu", "metadata", "qps", "tp"):
        status = status_map[tool_name]

        def _runner(_cluster_name, _start_time, _end_time, _status=status, _tool=tool_name):
            if _status == "raise":
                raise RuntimeError(f"{_tool} failed")
            if _status == "timeout":
                return {
                    "tool": _tool,
                    "status": "timeout",
                    "data": None,
                    "error": {"type": "TimeoutError", "message": "timeout"},
                }
            if _status == "empty":
                return {
                    "tool": _tool,
                    "status": "empty",
                    "data": None,
                    "error": {"message": "no data"},
                }
            return {
                "tool": _tool,
                "status": "success",
                "data": {"tool": _tool, "ok": True},
                "error": None,
            }

        runners[tool_name] = _runner
    return runners


class ApiIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app({"TESTING": True, "MAX_CONCURRENCY": 10})
        self.client = self.app.test_client()
        self.valid_payload = {
            "start_time": "2026-01-13 09:00:00",
            "end_time": "2026-01-13 09:30:00",
            "cluster_name": "ga-lan-jdns1",
        }

    def test_analyze_all_success_returns_200(self):
        runners = _build_tool_runners(
            {
                "network": "success",
                "code": "success",
                "cpu": "success",
                "metadata": "success",
                "qps": "success",
                "tp": "success",
            }
        )
        with patch.dict(TOOL_RUNNERS, runners, clear=True):
            response = self.client.post(
                "/api/v1/cluster/analyze",
                json=self.valid_payload,
            )

        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertIn("request_id", body)
        self.assertEqual(body["input"], self.valid_payload)
        self.assertEqual(set(body["results"].keys()), set(runners.keys()))
        self.assertEqual(body["summary"]["success_count"], 6)

    def test_analyze_partial_failure_returns_200(self):
        runners = _build_tool_runners(
            {
                "network": "success",
                "code": "raise",
                "cpu": "success",
                "metadata": "empty",
                "qps": "success",
                "tp": "success",
            }
        )
        with patch.dict(TOOL_RUNNERS, runners, clear=True):
            response = self.client.post(
                "/api/v1/cluster/analyze",
                json=self.valid_payload,
            )

        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertEqual(body["results"]["code"]["status"], "error")
        self.assertIn("RuntimeError", body["results"]["code"]["error"]["type"])

    def test_analyze_all_failed_returns_502(self):
        runners = _build_tool_runners(
            {
                "network": "raise",
                "code": "raise",
                "cpu": "raise",
                "metadata": "raise",
                "qps": "raise",
                "tp": "raise",
            }
        )
        with patch.dict(TOOL_RUNNERS, runners, clear=True):
            response = self.client.post(
                "/api/v1/cluster/analyze",
                json=self.valid_payload,
            )

        self.assertEqual(response.status_code, 502)
        body = response.get_json()
        self.assertEqual(body["summary"]["success_count"], 0)
        self.assertEqual(body["summary"]["failure_count"], 6)

    def test_invalid_payload_returns_400(self):
        response = self.client.post(
            "/api/v1/cluster/analyze",
            json={"start_time": "bad"},
        )
        self.assertEqual(response.status_code, 400)
        body = response.get_json()
        self.assertEqual(body["error"], "invalid_request")
        self.assertIn("details", body)
        self.assertIn("end_time", body["details"])
        self.assertIn("cluster_name", body["details"])

    def test_concurrency_limit_returns_429(self):
        guard = self.app.extensions["concurrency_guard"]
        acquired_count = 0
        while guard.acquire(blocking=False):
            acquired_count += 1
        try:
            response = self.client.post(
                "/api/v1/cluster/analyze",
                json=self.valid_payload,
            )
        finally:
            for _ in range(acquired_count):
                guard.release()

        self.assertEqual(response.status_code, 429)
        body = response.get_json()
        self.assertEqual(body["error"], "too_many_requests")


if __name__ == "__main__":
    unittest.main()
