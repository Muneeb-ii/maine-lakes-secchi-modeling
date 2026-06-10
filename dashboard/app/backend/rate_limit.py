import os
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request

RATE_LIMIT_WINDOW_SECONDS = 60
API_RATE_LIMIT_PER_MINUTE = int(os.getenv("API_RATE_LIMIT_PER_MINUTE", "180"))
PREDICT_RATE_LIMIT_PER_MINUTE = int(os.getenv("PREDICT_RATE_LIMIT_PER_MINUTE", "60"))


class SlidingWindowLimiter:
    def __init__(self, max_requests: int, window_seconds: int = RATE_LIMIT_WINDOW_SECONDS):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._request_times: dict[str, deque] = defaultdict(deque)

    def clear(self) -> None:
        self._request_times.clear()

    def check(self, key: str, *, message: str) -> None:
        if self.max_requests <= 0:
            return

        now = time.monotonic()
        request_times = self._request_times[key]
        while request_times and now - request_times[0] > self.window_seconds:
            request_times.popleft()

        if len(request_times) >= self.max_requests:
            retry_after = max(1, int(self.window_seconds - (now - request_times[0])))
            raise HTTPException(
                status_code=429,
                detail=message,
                headers={"Retry-After": str(retry_after)},
            )

        request_times.append(now)


_api_limiter = SlidingWindowLimiter(API_RATE_LIMIT_PER_MINUTE)
_predict_limiter = SlidingWindowLimiter(PREDICT_RATE_LIMIT_PER_MINUTE)


def client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for", "")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip() or "unknown"
    return request.client.host if request.client else "unknown"


def enforce_api_rate_limit(request: Request) -> None:
    _api_limiter.check(
        client_ip(request),
        message="Too many requests. Please wait a moment and try again.",
    )


def enforce_predict_rate_limit(request: Request) -> None:
    _predict_limiter.check(
        client_ip(request),
        message="Prediction rate limit exceeded. Try again shortly.",
    )


def reset_rate_limit_state_for_tests() -> None:
    _api_limiter.clear()
    _predict_limiter.clear()
