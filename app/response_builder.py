from typing import Any, Dict, Mapping


SUCCESS_STATUSES = {"success", "empty"}
FAILURE_STATUSES = {"error", "timeout"}


def _get_status(result: Mapping[str, Any]) -> str:
    raw = result.get("status")
    if isinstance(raw, str):
        return raw
    return "error"


def summarize_results(results: Mapping[str, Mapping[str, Any]]) -> Dict[str, int]:
    success_count = 0
    empty_count = 0
    failure_count = 0
    timeout_count = 0

    for result in results.values():
        status = _get_status(result)
        if status == "success":
            success_count += 1
        elif status == "empty":
            empty_count += 1
        elif status == "timeout":
            timeout_count += 1
        else:
            failure_count += 1

    return {
        "success_count": success_count,
        "empty_count": empty_count,
        "failure_count": failure_count,
        "timeout_count": timeout_count,
        "total_count": len(results),
    }


def decide_http_status(
    results: Mapping[str, Mapping[str, Any]], internal_error: bool = False
) -> int:
    if internal_error:
        return 500
    if not results:
        return 502

    for result in results.values():
        status = _get_status(result)
        if status in SUCCESS_STATUSES:
            return 200
        if status not in FAILURE_STATUSES:
            return 200

    return 502


def build_response(
    request_id: str,
    request_input: Mapping[str, Any],
    results: Mapping[str, Mapping[str, Any]],
) -> Dict[str, Any]:
    return {
        "request_id": request_id,
        "input": dict(request_input),
        "summary": summarize_results(results),
        "results": dict(results),
    }
