import json
import logging
import uuid
from typing import Any


DEFAULT_LOGGER_NAME = "app.observability"


def get_logger(name: str = DEFAULT_LOGGER_NAME, level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(handler)
    return logger


def new_request_id() -> str:
    return uuid.uuid4().hex


def emit_log(logger: logging.Logger, event: str, **fields: Any) -> None:
    payload = {"event": event, **fields}
    logger.info(json.dumps(payload, ensure_ascii=False, sort_keys=True))
