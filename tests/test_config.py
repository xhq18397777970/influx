import os
import unittest
from unittest.mock import patch

from app import create_app
from app.config import load_settings


class ConfigTests(unittest.TestCase):
    def test_load_settings_defaults(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("MAX_CONCURRENCY", None)
            os.environ.pop("TOOL_TIMEOUT_SECONDS", None)
            os.environ.pop("LOG_LEVEL", None)

            settings = load_settings()

        self.assertEqual(settings.max_concurrency, 10)
        self.assertEqual(settings.tool_timeout_seconds, 30)
        self.assertEqual(settings.log_level, "INFO")

    def test_load_settings_env_override(self):
        with patch.dict(
            os.environ,
            {
                "MAX_CONCURRENCY": "12",
                "TOOL_TIMEOUT_SECONDS": "45",
                "LOG_LEVEL": "DEBUG",
            },
            clear=False,
        ):
            settings = load_settings()

        self.assertEqual(settings.max_concurrency, 12)
        self.assertEqual(settings.tool_timeout_seconds, 45)
        self.assertEqual(settings.log_level, "DEBUG")

    def test_create_app_applies_config(self):
        with patch.dict(
            os.environ, {"MAX_CONCURRENCY": "10", "TOOL_TIMEOUT_SECONDS": "30"}, clear=False
        ):
            app = create_app()

        self.assertEqual(app.config["MAX_CONCURRENCY"], 10)
        self.assertEqual(app.config["TOOL_TIMEOUT_SECONDS"], 30)
        self.assertIn("LOG_LEVEL", app.config)


if __name__ == "__main__":
    unittest.main()
