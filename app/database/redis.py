import redis.asyncio as aioredis
from app.core.config import settings

class RedisManager:
    def __init__(self):
        self.redis = None

    async def connect(self):
        self.redis = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=settings.REDIS_MAX_CONNECTIONS,
            protocol=2
        )

        await self.redis.ping()

    async def close(self):
        if self.redis:
            await self.redis.aclose()


redis_manager = RedisManager()