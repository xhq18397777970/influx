import unittest

from app.response_builder import build_response, decide_http_status


class ResponseBuilderTests(unittest.TestCase):
    def test_build_response_has_required_envelope_and_summary(self):
        request_id = "req-123"
        payload = {
            "start_time": "2026-01-13 09:00:00",
            "end_time": "2026-01-13 09:30:00",
            "cluster_name": "ga-lan-jdns1",
        }
        results = {
            "network": {
                "status": "success",
                "data": {"a": 1},
                "error": None,
                "latency_ms": 10,
            },
            "code": {
                "status": "empty",
                "data": None,
                "error": {"message": "no data"},
                "latency_ms": 12,
            },
            "cpu": {
                "status": "timeout",
                "data": None,
                "error": {"type": "TimeoutError"},
                "latency_ms": 30000,
            },
            "metadata": {
                "status": "error",
                "data": None,
                "error": {"type": "RuntimeError"},
                "latency_ms": 5,
            },
        }

        response = build_response(request_id, payload, results)

        self.assertEqual(response["request_id"], request_id)
        self.assertEqual(response["input"], payload)
        self.assertEqual(response["results"], results)
        self.assertEqual(response["summary"]["success_count"], 1)
        self.assertEqual(response["summary"]["empty_count"], 1)
        self.assertEqual(response["summary"]["failure_count"], 1)
        self.assertEqual(response["summary"]["timeout_count"], 1)
        self.assertEqual(response["summary"]["total_count"], 4)

    def test_decide_http_status_returns_200_when_any_success(self):
        status = decide_http_status(
            {
                "network": {"status": "error"},
                "code": {"status": "success"},
            }
        )
        self.assertEqual(status, 200)

    def test_decide_http_status_returns_200_when_any_empty(self):
        status = decide_http_status(
            {
                "network": {"status": "timeout"},
                "code": {"status": "empty"},
            }
        )
        self.assertEqual(status, 200)

    def test_decide_http_status_returns_502_when_all_failed(self):
        status = decide_http_status(
            {
                "network": {"status": "error"},
                "code": {"status": "timeout"},
            }
        )
        self.assertEqual(status, 502)

    def test_decide_http_status_returns_500_when_internal_error(self):
        status = decide_http_status(
            {"network": {"status": "success"}},
            internal_error=True,
        )
        self.assertEqual(status, 500)


if __name__ == "__main__":
    unittest.main()
