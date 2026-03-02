from importlib import import_module
from typing import Any, Callable, Dict, Tuple


TOOL_FUNCTIONS: Dict[str, Tuple[str, str]] = {
    "network": ("tools.bps", "get_cluster_network_analysis"),
    "code": ("tools.code", "get_cluster_status_code_analysis"),
    "cpu": ("tools.cpu", "get_cluster_cpu_analysis"),
    "metadata": ("tools.get_cluster_metadata", "get_cluster_metadata"),
    "qps": ("tools.qps", "get_cluster_qps_analysis"),
    "tp": ("tools.tp", "get_cluster_connect_delay_analysis"),
}


def _resolve_tool_callable(tool_name: str) -> Callable[[str, str, str], Any]:
    spec = TOOL_FUNCTIONS.get(tool_name)
    if spec is None:
        raise ValueError(f"unsupported tool: {tool_name}")

    module_name, function_name = spec
    module = import_module(module_name)
    tool_callable = getattr(module, function_name, None)
    if tool_callable is None or not callable(tool_callable):
        raise AttributeError(f"{function_name} is not callable in module {module_name}")
    return tool_callable


def run_tool(
    tool_name: str, cluster_name: str, start_time: str, end_time: str
) -> Dict[str, Any]:
    try:
        tool_callable = _resolve_tool_callable(tool_name)
        data = tool_callable(cluster_name, start_time, end_time)
        return {"tool": tool_name, "status": "success", "data": data, "error": None}
    except Exception as exc:
        return {
            "tool": tool_name,
            "status": "error",
            "data": None,
            "error": {"type": type(exc).__name__, "message": str(exc)},
        }


def run_network(cluster_name: str, start_time: str, end_time: str) -> Dict[str, Any]:
    return run_tool("network", cluster_name, start_time, end_time)


def run_code(cluster_name: str, start_time: str, end_time: str) -> Dict[str, Any]:
    return run_tool("code", cluster_name, start_time, end_time)


def run_cpu(cluster_name: str, start_time: str, end_time: str) -> Dict[str, Any]:
    return run_tool("cpu", cluster_name, start_time, end_time)


def run_metadata(cluster_name: str, start_time: str, end_time: str) -> Dict[str, Any]:
    return run_tool("metadata", cluster_name, start_time, end_time)


def run_qps(cluster_name: str, start_time: str, end_time: str) -> Dict[str, Any]:
    return run_tool("qps", cluster_name, start_time, end_time)


def run_tp(cluster_name: str, start_time: str, end_time: str) -> Dict[str, Any]:
    return run_tool("tp", cluster_name, start_time, end_time)
