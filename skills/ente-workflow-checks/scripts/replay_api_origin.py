#!/usr/bin/env python3
"""Captured-request failure shapes; no network traffic or production API calls."""

import unittest

from check_api_origin import check_requests


class OriginReplay(unittest.TestCase):
    def check(self, urls, expected="http://localhost:8080"):
        return check_requests({"log": {"entries": [{"request": {"url": url}} for url in urls]}}, expected, ["/public-collection/"])

    def test_production_fallback_is_detected(self):
        result = self.check(["https://api.ente.io/public-collection/info?token=synthetic"])
        self.assertEqual(result["status"], "fail")
        self.assertNotIn("synthetic", str(result))

    def test_actual_local_api_request_passes(self):
        self.assertEqual(self.check(["http://localhost:8080/public-collection/info"])["status"], "pass")

    def test_mixed_local_and_production_requests_fail(self):
        self.assertEqual(self.check(["http://localhost:8080/public-collection/info", "https://api.ente.io/public-collection/info"])["status"], "fail")

    def test_no_exercised_api_path_is_incomplete(self):
        self.assertEqual(self.check(["http://localhost:8080/health"])["status"], "incomplete")

    def test_unrelated_asset_origin_does_not_block_local_api(self):
        self.assertEqual(self.check(["http://localhost:8080/public-collection/info", "https://static.example.invalid/icon.svg"])["status"], "pass")

    def test_default_port_is_normalized(self):
        self.assertEqual(self.check(["https://example.invalid:443/public-collection/info"], "https://example.invalid")["status"], "pass")

    def test_explicit_zero_port_is_not_treated_as_default(self):
        self.assertEqual(self.check(["https://example.invalid:0/public-collection/info"], "https://example.invalid")["status"], "fail")


if __name__ == "__main__":
    unittest.main(verbosity=2)
