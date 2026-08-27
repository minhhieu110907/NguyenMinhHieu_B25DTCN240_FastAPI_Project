import redis.exceptions as redis_exception
from app.core.config import settings
from app.core.exceptions import RateLimitServiceUnavailableError,RateLimitExceededError
from app.database.redis import redis_manager


LUA_RATE_LIMIT_SCRIPT = """
local current = redis.call("INCR", KEYS[1])

if current == 1 then
    redis.call("EXPIRE", KEYS[1], ARGV[1])
end

local ttl = redis.call("TTL", KEYS[1])

return {current, ttl}
"""

async def check_rate_limit(
    key: str,
    limit: int,
    window: int,
) -> None:
    redis = redis_manager.redis

    if redis is None:
        raise RateLimitServiceUnavailableError()

    try:
        script = redis.register_script(LUA_RATE_LIMIT_SCRIPT)

        current_count, ttl = await script(
            keys=[key],
            args=[window],
        )

    except redis_exception.RedisError:
        if settings.RL_FAIL_MODE == "closed":
            raise RateLimitServiceUnavailableError()

        return

    if current_count > limit:
        retry_after = ttl if ttl > 0 else window

        raise RateLimitExceededError(
            retry_after=retry_after
        )