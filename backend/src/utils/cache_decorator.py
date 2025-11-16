from src.config.settings import settings
from fastapi_cache.decorator import cache
from functools import wraps


def conditional_cache(expire: int = 600):
    """
    Decorator that applies caching only when ENABLE_CACHE is True.
    
    Args:
        expire: Cache expiration time in seconds (default: 600)
    """
    def decorator(func):
        if settings.ENABLE_CACHE:
            # Apply caching
            return cache(expire=expire)(func)
        else:
            # Return function without caching
            @wraps(func)
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs)
            return wrapper
    return decorator
