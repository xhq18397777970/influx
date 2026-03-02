import unittest
from unittest.mock import Mock, patch

from app.tool_adapters import (
    TOOL_FUNCTIONS,
    run_code,
    run_cpu,
    run_metadata,
    run_network,
    run_qps,
    run_tool,
    run_tp,
)


class ToolAdaptersTests(unittest.TestCase):
    def test_tool_mapping_is_correct(self):
        self.assertEqual(
            TOOL_FUNCTIONS["network"], ("tools.bps", "get_cluster_network_analysis")
        )
        self.assertEqual(
            TOOL_FUNCTIONS["code"], ("tools.code", "get_cluster_status_code_analysis")
        )
        self.assertEqual(
            TOOL_FUNCTIONS["cpu"], ("tools.cpu", "get_cluster_cpu_analysis")
        )
        self.assertEqual(
            TOOL_FUNCTIONS["metadata"],
            ("tools.get_cluster_metadata", "get_cluster_metadata"),
        )
        self.assertEqual(TOOL_FUNCTIONS["qps"], ("tools.qps", "get_cluster_qps_analysis"))
        self.assertEqual(
            TOOL_FUNCTIONS["tp"], ("tools.tp", "get_cluster_connect_delay_analysis")
        )

    def test_wrapper_calls_network_tool(self):
        tool_func = Mock(return_value={"k": "v"})
        with patch("app.tool_adapters._resolve_tool_callable", return_value=tool_func):
            result = run_network("cluster-a", "2026-01-13 09:00:00", "2026-01-13 09:30:00")

        tool_func.assert_called_once_with(
            "cluster-a", "2026-01-13 09:00:00", "2026-01-13 09:30:00"
        )
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["data"], {"k": "v"})
        self.assertIsNone(result["error"])

    def test_wrappers_cover_all_tools(self):
        tool_func = Mock(return_value={"ok": True})
        with patch("app.tool_adapters._resolve_tool_callable", return_value=tool_func):
            run_code("c", "s", "e")
            run_cpu("c", "s", "e")
            run_metadata("c", "s", "e")
            run_qps("c", "s", "e")
            run_tp("c", "s", "e")

        self.assertEqual(tool_func.call_count, 5)

    def test_unknown_tool_returns_structured_error(self):
        result = run_tool("unknown", "c", "s", "e")
        self.assertEqual(result["status"], "error")
        self.assertIsNone(result["data"])
        self.assertEqual(result["error"]["type"], "ValueError")

    def test_tool_exception_is_captured(self):
        def _raise(*_args):
            raise RuntimeError("boom")

        with patch("app.tool_adapters._resolve_tool_callable", return_value=_raise):
            result = run_tool("network", "c", "s", "e")

        self.assertEqual(result["status"], "error")
        self.assertIsNone(result["data"])
        self.assertEqual(result["error"]["type"], "RuntimeError")
        self.assertIn("boom", result["error"]["message"])


if __name__ == "__main__":
    unittest.main()
