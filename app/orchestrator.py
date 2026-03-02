import time
from concurrent.futures import ALL_COMPLETED, ThreadPoolExecutor, wait
import logging
from typing import Any, Callable, Dict, Mapping, Optional

from app.logging_utils import emit_log
from app.tool_adapters import (
    run_code,
    run_cpu,
    run_metadata,
    run_network,
    run_qps,
    run_tp,
)


DEFAULT_ORCHESTRATOR_MAX_WORKERS = 10

TOOL_RUNNERS: Dict[str, Callable[[str, str, str], Dict[str, Any]]] = {
    "network": run_network,
    "code": run_code,
    "cpu": run_cpu,
    "metadata": run_metadata,
    "qps": run_qps,
    "tp": run_tp,
}


def _normalize_runner_output(tool_name: str, raw_result: Any) -> Dict[str, Any]:
    if isinstance(raw_result, dict) and "status" in raw_result:
        status = raw_result.get("status", "success")
        if status in {"success", "empty"}:
            return {
                "status": status,
                "data": raw_result.get("data"),
                "error": raw_result.get("error"),
            }
        if status in {"timeout", "error"}:
            return {
                "status": status,
                "data": raw_result.get("data"),
                "error": raw_result.get("error"),
            }

    return {"status": "success", "data": raw_result, "error": None}


def _build_timeout_result(elapsed_seconds: float) -> Dict[str, Any]:
    return {
        "status": "timeout",
        "data": None,
        "error": {"type": "TimeoutError", "message": "tool execution timed out"},
        "latency_ms": int(max(elapsed_seconds, 0) * 1000),
    }


def run_parallel_analysis(
    cluster_name: str,
    start_time: str,
    end_time: str,
    tool_timeout_seconds: float = 30.0,
    tool_runners: Optional[Mapping[str, Callable[[str, str, str], Any]]] = None,
    logger: logging.Logger | None = None,
    request_id: str | None = None,
) -> Dict[str, Dict[str, Any]]:
    if tool_timeout_seconds <= 0:
        raise ValueError("tool_timeout_seconds must be > 0")

    runners: Mapping[str, Callable[[str, str, str], Any]] = tool_runners or TOOL_RUNNERS
    if not runners:
        return {}

    start_marks: Dict[str, float] = {}
    results: Dict[str, Dict[str, Any]] = {}
    max_workers = min(DEFAULT_ORCHESTRATOR_MAX_WORKERS, len(runners))

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        # Submit all tasks first to ensure per-request parallel start.
        for tool_name, runner in runners.items():
            start_marks[tool_name] = time.perf_counter()
            future = executor.submit(runner, cluster_name, start_time, end_time)
            futures[future] = tool_name

        done, not_done = wait(
            futures.keys(),
            timeout=tool_timeout_seconds,
            return_when=ALL_COMPLETED,
        )

        for future in done:
            tool_name = futures[future]
            elapsed = time.perf_counter() - start_marks[tool_name]
            try:
                raw_result = future.result()
            except Exception as exc:
                results[tool_name] = {
                    "status": "error",
                    "data": None,
                    "error": {"type": type(exc).__name__, "message": str(exc)},
                    "latency_ms": int(max(elapsed, 0) * 1000),
                }
                continue

            normalized = _normalize_runner_output(tool_name, raw_result)
            normalized["latency_ms"] = int(max(elapsed, 0) * 1000)
            results[tool_name] = normalized
            if logger is not None:
                emit_log(
                    logger,
                    "tool_result",
                    request_id=request_id,
                    tool_name=tool_name,
                    status=normalized["status"],
                    tool_latency_ms=normalized["latency_ms"],
                )

        for future in not_done:
            tool_name = futures[future]
            future.cancel()
            elapsed = time.perf_counter() - start_marks[tool_name]
            results[tool_name] = _build_timeout_result(elapsed)
            if logger is not None:
                emit_log(
                    logger,
                    "tool_result",
                    request_id=request_id,
                    tool_name=tool_name,
                    status=results[tool_name]["status"],
                    tool_latency_ms=results[tool_name]["latency_ms"],
                )

    ordered_results: Dict[str, Dict[str, Any]] = {}
    for tool_name in runners.keys():
        ordered_results[tool_name] = results[tool_name]
    return ordered_results
