import unittest

from app.validators import validate_analyze_request


class ValidatorTests(unittest.TestCase):
    def test_missing_required_fields(self):
        payload = {"start_time": "2026-01-13 09:00:00"}
        _, errors = validate_analyze_request(payload)
        self.assertIn("end_time", errors)
        self.assertIn("cluster_name", errors)

    def test_empty_required_fields(self):
        payload = {
            "start_time": "",
            "end_time": "2026-01-13 09:30:00",
            "cluster_name": "   ",
        }
        _, errors = validate_analyze_request(payload)
        self.assertIn("start_time", errors)
        self.assertIn("cluster_name", errors)

    def test_invalid_datetime_format(self):
        payload = {
            "start_time": "2026/01/13 09:00:00",
            "end_time": "2026-01-13 09:30:00",
            "cluster_name": "ga-lan-jdns1",
        }
        _, errors = validate_analyze_request(payload)
        self.assertIn("start_time", errors)

    def test_invalid_time_range(self):
        payload = {
            "start_time": "2026-01-13 09:30:00",
            "end_time": "2026-01-13 09:00:00",
            "cluster_name": "ga-lan-jdns1",
        }
        _, errors = validate_analyze_request(payload)
        self.assertIn("time_range", errors)

    def test_valid_payload(self):
        payload = {
            "start_time": "2026-01-13 09:00:00",
            "end_time": "2026-01-13 09:30:00",
            "cluster_name": " ga-lan-jdns1 ",
        }
        cleaned, errors = validate_analyze_request(payload)
        self.assertEqual(errors, {})
        self.assertEqual(cleaned["start_time"], "2026-01-13 09:00:00")
        self.assertEqual(cleaned["end_time"], "2026-01-13 09:30:00")
        self.assertEqual(cleaned["cluster_name"], "ga-lan-jdns1")


if __name__ == "__main__":
    unittest.main()
