from functools import wraps
from datetime import datetime, timedelta
from typing import Any

_cache: dict[str, tuple[Any, datetime]] = {}


def cache(ttl_seconds: int = 60):
    """简单内存缓存装饰器（跳过第一个参数，通常是 db session）"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 跳过第一个参数（db session），只使用业务参数生成缓存键
            cache_args = args[1:] if len(args) > 0 else args
            key = f"{func.__name__}:{str(cache_args)}:{str(sorted(kwargs.items()))}"
            now = datetime.now()

            if key in _cache:
                value, expires_at = _cache[key]
                if now < expires_at:
                    return value

            result = await func(*args, **kwargs)
            _cache[key] = (result, now + timedelta(seconds=ttl_seconds))
            return result
        return wrapper
    return decorator


def clear_cache():
    """清除所有缓存"""
    _cache.clear()
