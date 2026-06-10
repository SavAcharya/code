import hashlib
import json
import logging
import redis.asyncio as aioredis
from config import settings

logger = logging.getLogger(__name__)

_pool = None


async def _get_redis():
    global _pool
    if _pool is None:
        _pool = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _pool


def _hash(*args) -> str:
    return hashlib.sha256("::".join(str(a) for a in args).encode()).hexdigest()[:20]


async def get(task: str, *inputs) -> dict | None:
    try:
        r = await _get_redis()
        key = f"llm:{task}:{_hash(*inputs)}"
        data = await r.get(key)
        if data:
            logger.info(f"Cache HIT: {key}")
            return json.loads(data)
    except Exception as e:
        logger.warning(f"Cache get error: {e}")
    return None


async def set(task: str, result: dict, *inputs):
    try:
        r = await _get_redis()
        key = f"llm:{task}:{_hash(*inputs)}"
        await r.set(key, json.dumps(result, default=str), ex=settings.cache_ttl_seconds)
        logger.info(f"Cache SET: {key} (TTL {settings.cache_ttl_seconds}s)")
    except Exception as e:
        logger.warning(f"Cache set error: {e}")
