from app.config import load_settings
from app.concurrency import ConcurrencyGuard
from app.logging_utils import get_logger
from app.routes import register_routes

try:
    from flask import Flask  # type: ignore
except ImportError:  # pragma: no cover
    Flask = None


class LightweightApp:
    """Fallback app object for environments where Flask is unavailable."""

    def __init__(self, import_name: str) -> None:
        self.import_name = import_name
        self.config = {}
        self.extensions = {}


def create_app(test_config: dict | None = None):
    settings = load_settings()
    if Flask is None:
        app = LightweightApp(__name__)
    else:
        app = Flask(__name__)

    app.config.update(settings.to_flask_config())
    if test_config:
        app.config.update(test_config)

    concurrency_guard = ConcurrencyGuard(limit=int(app.config["MAX_CONCURRENCY"]))
    event_logger = get_logger("app.service")
    app.extensions["concurrency_guard"] = concurrency_guard
    app.extensions["event_logger"] = event_logger

    if Flask is not None:
        register_routes(app, concurrency_guard, event_logger)
    return app
