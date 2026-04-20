import redis

from app.core.settings import get_env, get_int_env

_redis_client = None


def get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis(
            host=get_env("REDIS_HOST"),
            port=get_int_env("REDIS_PORT"),
            decode_responses=False
        )
    return _redis_client
