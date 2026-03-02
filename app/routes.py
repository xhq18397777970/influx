from collections.abc import Callable
import logging
import time
from typing import Any

from app.concurrency import ConcurrencyGuard
from app.logging_utils import emit_log, new_request_id
from app.orchestrator import run_parallel_analysis
from app.response_builder import build_response, decide_http_status
from app.validators import validate_analyze_request

try:
    from flask import jsonify, request  # type: ignore
except ImportError:  # pragma: no cover
    jsonify = None
    request = None


RATE_LIMIT_BODY = {"error": "too_many_requests"}


def execute_with_concurrency_guard(
    guard: ConcurrencyGuard,
    handler: Callable[[], tuple[Any, int]],
    logger: logging.Logger | None = None,
    request_id: str | None = None,
) -> tuple[Any, int]:
    start_time = time.perf_counter()
    acquired = guard.acquire(blocking=False)
    if not acquired:
        if logger is not None:
            emit_log(
                logger,
                "rate_limit",
                request_id=request_id,
                rate_limit_hit=True,
                total_latency_ms=int((time.perf_counter() - start_time) * 1000),
            )
        return RATE_LIMIT_BODY.copy(), 429

    try:
        return handler()
    finally:
        guard.release()
        if logger is not None:
            emit_log(
                logger,
                "request_guard_finished",
                request_id=request_id,
                rate_limit_hit=False,
                total_latency_ms=int((time.perf_counter() - start_time) * 1000),
            )


def register_routes(
    app: Any,
    guard: ConcurrencyGuard,
    logger: logging.Logger,
) -> None:
    if request is None or jsonify is None:
        return

    @app.post("/api/v1/cluster/analyze")
    def analyze_cluster():
        request_id = new_request_id()
        payload = request.get_json(silent=True)
        cleaned, errors = validate_analyze_request(payload)
        if errors:
            return jsonify({"error": "invalid_request", "details": errors}), 400

        def _handle():
            results = run_parallel_analysis(
                cleaned["cluster_name"],
                cleaned["start_time"],
                cleaned["end_time"],
                tool_timeout_seconds=float(app.config.get("TOOL_TIMEOUT_SECONDS", 30)),
                logger=logger,
                request_id=request_id,
            )
            body = build_response(request_id, cleaned, results)
            return body, decide_http_status(results)

        try:
            body, status = execute_with_concurrency_guard(
                guard,
                _handle,
                logger=logger,
                request_id=request_id,
            )
        except Exception as exc:
            emit_log(
                logger,
                "request_error",
                request_id=request_id,
                error_type=type(exc).__name__,
                message=str(exc),
            )
            return jsonify({"request_id": request_id, "error": "internal_error"}), 500

        return jsonify(body), status
