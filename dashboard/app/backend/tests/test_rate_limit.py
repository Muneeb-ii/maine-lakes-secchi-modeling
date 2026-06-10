import unittest

from fastapi import HTTPException

import rate_limit


def request_for(ip="203.0.113.10"):
    from types import SimpleNamespace

    return SimpleNamespace(headers={"x-forwarded-for": ip}, client=SimpleNamespace(host=ip))


class RateLimitTests(unittest.TestCase):
    def setUp(self):
        self.original_api_limit = rate_limit._api_limiter.max_requests
        self.original_predict_limit = rate_limit._predict_limiter.max_requests
        rate_limit.reset_rate_limit_state_for_tests()

    def tearDown(self):
        rate_limit._api_limiter.max_requests = self.original_api_limit
        rate_limit._predict_limiter.max_requests = self.original_predict_limit
        rate_limit.reset_rate_limit_state_for_tests()

    def test_api_rate_limit_blocks_after_threshold(self):
        rate_limit._api_limiter.max_requests = 2
        request = request_for("198.51.100.8")

        rate_limit.enforce_api_rate_limit(request)
        rate_limit.enforce_api_rate_limit(request)

        with self.assertRaises(HTTPException) as error_ctx:
            rate_limit.enforce_api_rate_limit(request)

        self.assertEqual(error_ctx.exception.status_code, 429)
        self.assertIn("Retry-After", error_ctx.exception.headers)

    def test_predict_rate_limit_is_separate_from_api_budget(self):
        rate_limit._api_limiter.max_requests = 10
        rate_limit._predict_limiter.max_requests = 1
        request = request_for("198.51.100.9")

        rate_limit.enforce_predict_rate_limit(request)
        with self.assertRaises(HTTPException) as error_ctx:
            rate_limit.enforce_predict_rate_limit(request)

        self.assertEqual(error_ctx.exception.status_code, 429)
        self.assertIn("Prediction rate limit", error_ctx.exception.detail)

    def test_zero_limit_disables_enforcement(self):
        rate_limit._api_limiter.max_requests = 0
        request = request_for("198.51.100.10")

        for _ in range(5):
            rate_limit.enforce_api_rate_limit(request)


if __name__ == "__main__":
    unittest.main()
