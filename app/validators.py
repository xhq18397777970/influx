from datetime import datetime
from typing import Dict, Optional, Tuple


DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
MAX_CLUSTER_NAME_LENGTH = 128


def _is_blank(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    return False


def _parse_datetime(value: str) -> Optional[datetime]:
    try:
        return datetime.strptime(value, DATETIME_FORMAT)
    except ValueError:
        return None


def validate_analyze_request(
    payload: object,
) -> Tuple[Optional[Dict[str, str]], Dict[str, str]]:
    errors: Dict[str, str] = {}

    if not isinstance(payload, dict):
        return None, {"body": "request body must be a JSON object"}

    cleaned: Dict[str, str] = {}
    required_fields = ("start_time", "end_time", "cluster_name")

    for field in required_fields:
        value = payload.get(field)
        if _is_blank(value):
            errors[field] = f"{field} is required"
            continue
        cleaned[field] = str(value).strip()

    start_dt = None
    end_dt = None

    if "start_time" in cleaned:
        start_dt = _parse_datetime(cleaned["start_time"])
        if start_dt is None:
            errors["start_time"] = (
                f"start_time must match format {DATETIME_FORMAT}"
            )

    if "end_time" in cleaned:
        end_dt = _parse_datetime(cleaned["end_time"])
        if end_dt is None:
            errors["end_time"] = f"end_time must match format {DATETIME_FORMAT}"

    if (
        "cluster_name" in cleaned
        and len(cleaned["cluster_name"]) > MAX_CLUSTER_NAME_LENGTH
    ):
        errors["cluster_name"] = (
            f"cluster_name must be <= {MAX_CLUSTER_NAME_LENGTH} characters"
        )

    if start_dt is not None and end_dt is not None and start_dt >= end_dt:
        errors["time_range"] = "start_time must be earlier than end_time"

    if errors:
        return None, errors
    return cleaned, {}
