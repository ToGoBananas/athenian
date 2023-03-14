from redis.asyncio.client import Redis
from redis.asyncio.connection import BlockingConnectionPool
from redis.asyncio.lock import Lock

from core.settings.redis import RedisConfig

redis_client = Redis(
    connection_pool=BlockingConnectionPool(
        max_connections=1000, decode_responses=True, **RedisConfig.get_default().dict()
    ),
)


class RedisLockClient:
    @classmethod
    def get(cls, name: str):
        return Lock(redis=redis_client, name=name, blocking_timeout=10, timeout=9)
