import os
from dataclasses import dataclass


DEFAULT_MAX_CONCURRENCY = 10
DEFAULT_TOOL_TIMEOUT_SECONDS = 30
DEFAULT_LOG_LEVEL = "INFO"


def _read_int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return value if value > 0 else default


@dataclass(frozen=True)
class AppSettings:
    max_concurrency: int = DEFAULT_MAX_CONCURRENCY
    tool_timeout_seconds: int = DEFAULT_TOOL_TIMEOUT_SECONDS
    log_level: str = DEFAULT_LOG_LEVEL

    @classmethod
    def from_env(cls) -> "AppSettings":
        return cls(
            max_concurrency=_read_int_env("MAX_CONCURRENCY", DEFAULT_MAX_CONCURRENCY),
            tool_timeout_seconds=_read_int_env(
                "TOOL_TIMEOUT_SECONDS", DEFAULT_TOOL_TIMEOUT_SECONDS
            ),
            log_level=os.getenv("LOG_LEVEL", DEFAULT_LOG_LEVEL),
        )

    def to_flask_config(self) -> dict:
        return {
            "MAX_CONCURRENCY": self.max_concurrency,
            "TOOL_TIMEOUT_SECONDS": self.tool_timeout_seconds,
            "LOG_LEVEL": self.log_level,
        }


def load_settings() -> AppSettings:
    return AppSettings.from_env()
