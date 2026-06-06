from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime, timedelta

from redis import Redis
from redis.exceptions import RedisError

from app.core.config import settings

_memory_attempts: dict[str, list[datetime]] = defaultdict(list)


class RateLimitExceeded(Exception):
    pass


class LoginRateLimiter:
    def __init__(self) -> None:
        self._redis: Redis | None = None
        if settings.redis_url:
            try:
                self._redis = Redis.from_url(settings.redis_url, decode_responses=True)
                self._redis.ping()
            except RedisError:
                self._redis = None

    def check(self, key: str) -> None:
        attempts = settings.login_rate_limit_attempts
        window = settings.login_rate_limit_window_seconds
        redis_key = f"login-rate:{key.lower()}"

        if self._redis is not None:
            try:
                count = self._redis.incr(redis_key)
                if count == 1:
                    self._redis.expire(redis_key, window)
                if count > attempts:
                    raise RateLimitExceeded("Too many login attempts")
                return
            except RedisError:
                self._redis = None

        now = datetime.now(UTC)
        cutoff = now - timedelta(seconds=window)
        _memory_attempts[key] = [ts for ts in _memory_attempts[key] if ts >= cutoff]
        _memory_attempts[key].append(now)
        if len(_memory_attempts[key]) > attempts:
            raise RateLimitExceeded("Too many login attempts")


login_rate_limiter = LoginRateLimiter()
