from collections import defaultdict, deque
from time import time

from fastapi import HTTPException, status


_attempts: dict[str, deque[float]] = defaultdict(deque)


def check_rate_limit(key: str, *, limit: int = 5, window_seconds: int = 300) -> None:
    now = time()
    bucket = _attempts[key]
    while bucket and now - bucket[0] > window_seconds:
        bucket.popleft()
    if len(bucket) >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Wait a few minutes and try again.",
        )
    bucket.append(now)


def clear_rate_limit(key: str) -> None:
    _attempts.pop(key, None)
