"""Rate limiting: Redis when configured, else in-memory."""
import logging
from collections import defaultdict
from time import time
from threading import Lock

from app.config import get_settings

logger = logging.getLogger(__name__)


class InMemoryRateLimiter:
    """Sliding window rate limiter. Key -> list of timestamps."""

    def __init__(self, window_seconds: int = 60):
        self.window = window_seconds
        self._counts: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()

    def is_allowed(self, key: str, limit: int) -> bool:
        """Return True if request allowed, False if rate limited."""
        now = time()
        cutoff = now - self.window
        with self._lock:
            self._counts[key] = [t for t in self._counts[key] if t > cutoff]
            if len(self._counts[key]) >= limit:
                return False
            self._counts[key].append(now)
            return True

    def remaining(self, key: str, limit: int) -> int:
        """Remaining requests in window."""
        now = time()
        cutoff = now - self.window
        with self._lock:
            self._counts[key] = [t for t in self._counts[key] if t > cutoff]
            return max(0, limit - len(self._counts[key]))


# Redis sliding-window Lua script (atomic)
_REDIS_SLIDING_SCRIPT = """
local key = KEYS[1]
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])
redis.call('ZREMRANGEBYSCORE', key, '-inf', now - window)
local count = redis.call('ZCARD', key)
if count >= limit then
  return 0
end
redis.call('ZADD', key, now, now)
redis.call('EXPIRE', key, math.ceil(window) + 1)
return 1
"""


class RedisRateLimiter:
    """Sliding window rate limiter backed by Redis."""

    def __init__(self, redis_url: str, window_seconds: int = 60):
        import redis
        self.client = redis.from_url(redis_url, decode_responses=True)
        self.window = window_seconds
        self._script = self.client.register_script(_REDIS_SLIDING_SCRIPT)

    def is_allowed(self, key: str, limit: int) -> bool:
        """Return True if request allowed, False if rate limited."""
        try:
            rkey = f"rl:{key}"
            result = self._script(keys=[rkey], args=[str(time()), str(self.window), str(limit)])
            return result == 1
        except Exception as e:
            logger.warning("Redis rate limit check failed (%s), allowing request", e)
            return True

    def remaining(self, key: str, limit: int) -> int:
        """Remaining requests in window (best effort)."""
        try:
            rkey = f"rl:{key}"
            now = time()
            self.client.zremrangebyscore(rkey, "-inf", now - self.window)
            count = self.client.zcard(rkey)
            return max(0, limit - count)
        except Exception:
            return limit


_limiter = None


def _get_limiter():
    """Lazy-init limiter: Redis if configured, else in-memory."""
    global _limiter
    if _limiter is not None:
        return _limiter
    settings = get_settings()
    if settings.redis_url:
        try:
            _limiter = RedisRateLimiter(settings.redis_url, window_seconds=60)
            logger.info("Rate limiting using Redis")
        except Exception as e:
            logger.warning("Redis unavailable (%s), falling back to in-memory rate limit", e)
            _limiter = InMemoryRateLimiter(window_seconds=60)
    else:
        _limiter = InMemoryRateLimiter(window_seconds=60)
    return _limiter


def check_rate_limit(key: str, limit: int) -> bool:
    """Check if request is allowed. Returns True if allowed."""
    return _get_limiter().is_allowed(key, limit)


def get_remaining(key: str, limit: int) -> int:
    """Get remaining requests for key."""
    return _get_limiter().remaining(key, limit)
