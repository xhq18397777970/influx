import threading
import time
import unittest

from app.orchestrator import run_parallel_analysis


class OrchestratorTests(unittest.TestCase):
    def test_tools_start_in_parallel(self):
        tool_names = ("network", "code", "cpu", "metadata", "qps", "tp")
        started = set()
        started_lock = threading.Lock()
        all_started = threading.Event()
        release = threading.Event()

        def make_runner(name):
            def _runner(_cluster_name, _start_time, _end_time):
                with started_lock:
                    started.add(name)
                    if len(started) == len(tool_names):
                        all_started.set()
                release.wait(timeout=1)
                return {"status": "success", "data": {"tool": name}, "error": None}

            return _runner

        tool_runners = {name: make_runner(name) for name in tool_names}
        result_holder = {}

        def worker():
            result_holder["result"] = run_parallel_analysis(
                "cluster-a",
                "2026-01-13 09:00:00",
                "2026-01-13 09:30:00",
                tool_timeout_seconds=2,
                tool_runners=tool_runners,
            )

        thread = threading.Thread(target=worker)
        thread.start()

        self.assertTrue(
            all_started.wait(timeout=0.5),
            "all tools should be started before runners are released",
        )
        release.set()
        thread.join(timeout=2)
        self.assertFalse(thread.is_alive())

        result = result_holder["result"]
        self.assertEqual(set(result.keys()), set(tool_names))
        for tool_name in tool_names:
            self.assertEqual(result[tool_name]["status"], "success")
            self.assertIn("latency_ms", result[tool_name])

    def test_timeout_is_mapped_to_timeout_status(self):
        def slow_runner(_cluster_name, _start_time, _end_time):
            time.sleep(0.2)
            return {"status": "success", "data": {"ok": True}, "error": None}

        def fast_runner(_cluster_name, _start_time, _end_time):
            return {"status": "success", "data": {"ok": True}, "error": None}

        results = run_parallel_analysis(
            "cluster-a",
            "2026-01-13 09:00:00",
            "2026-01-13 09:30:00",
            tool_timeout_seconds=0.05,
            tool_runners={"slow": slow_runner, "fast": fast_runner},
        )

        self.assertEqual(results["slow"]["status"], "timeout")
        self.assertEqual(results["fast"]["status"], "success")
        self.assertIn("latency_ms", results["slow"])
        self.assertGreaterEqual(results["slow"]["latency_ms"], 0)

    def test_exception_is_mapped_to_error_and_other_tools_continue(self):
        def bad_runner(_cluster_name, _start_time, _end_time):
            raise RuntimeError("boom")

        def good_runner(_cluster_name, _start_time, _end_time):
            return {"status": "success", "data": {"ok": True}, "error": None}

        results = run_parallel_analysis(
            "cluster-a",
            "2026-01-13 09:00:00",
            "2026-01-13 09:30:00",
            tool_timeout_seconds=1,
            tool_runners={"bad": bad_runner, "good": good_runner},
        )

        self.assertEqual(results["bad"]["status"], "error")
        self.assertEqual(results["bad"]["error"]["type"], "RuntimeError")
        self.assertIn("boom", results["bad"]["error"]["message"])
        self.assertEqual(results["good"]["status"], "success")


if __name__ == "__main__":
    unittest.main()
