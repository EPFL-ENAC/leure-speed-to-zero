from src.api.routes import router
from src.config.settings import settings
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from pydantic import ValidationError
import logging
from fastapi.responses import ORJSONResponse

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.decorator import cache

from redis import asyncio as aioredis


# Set servers in OpenAPI schema
from fastapi.openapi.utils import get_openapi
import os
from fastapi.middleware.gzip import GZipMiddleware


# Initialize cache on startup
@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Initialize cache with Redis fallback to in-memory cache."""
    logger = logging.getLogger(__name__)
    
    try:
        # Try to connect to Redis
        redis = aioredis.from_url(f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}")
        # Test the connection
        await redis.ping()
        FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
        logger.info(f"✅ Redis cache initialized successfully at {settings.REDIS_HOST}:{settings.REDIS_PORT}")
    except Exception as e:
        # If Redis connection fails, fall back to in-memory cache
        logger.warning(f"⚠️  Redis connection failed ({str(e)}). Falling back to in-memory cache.")
        logger.warning("📝 Note: Cache will not persist between application restarts.")
        FastAPICache.init(InMemoryBackend(), prefix="fastapi-cache")
        logger.info("✅ In-memory cache initialized as fallback")
    
    yield


app = FastAPI(lifespan=lifespan, root_path=settings.PATH_PREFIX)
app.include_router(router)
app.add_middleware(GZipMiddleware, minimum_size=100000, compresslevel=1)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.errors(),
            "body": exc.model.model_dump() if exc.model else None,
        },
    )


# Optional: Serve the main HTML file at the root
@app.get("/")
async def get_index():
    from fastapi.responses import FileResponse
    from pathlib import Path

    index_path = Path(__file__).parent.parent / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "Welcome to AddLidar API"}


@app.get("/redis-health")
async def check_redis():
    """Check Redis connection status."""
    try:
        import redis

        r = redis.from_url(f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}")
        ping = r.ping()
        return {
            "status": "ok", 
            "redis_connection": "successful", 
            "ping": ping,
            "cache_backend": "redis"
        }
    except Exception as e:
        return {
            "status": "warning", 
            "redis_connection": "failed",
            "message": str(e),
            "cache_backend": "in-memory fallback"
        }


import time


@app.get("/test-cache")
@cache(expire=10)
async def test_cache():
    """Test endpoint to verify caching is working."""
    # Add a timestamp to see if response changes
    timestamp = time.time()

    # Simulate expensive operation
    time.sleep(1)

    return {
        "cached": True,
        "timestamp": timestamp,
        "message": "If caching works, this timestamp should remain the same for 5 seconds",
    }


@app.get("/debug-cache")
async def debug_cache():
    """Debug endpoint to check cache status."""
    try:
        import redis

        r = redis.from_url(f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}")
        
        # List keys
        all_keys = r.keys("fastapi-cache:*")
        
        return {
            "cache_backend": "redis",
            "all_keys": [key.decode() if isinstance(key, bytes) else key for key in all_keys],
            "total_keys": len(all_keys),
            "redis_connection": "successful"
        }
    except Exception as e:
        return {
            "cache_backend": "in-memory fallback",
            "message": f"Redis not available: {str(e)}",
            "note": "Using in-memory cache (keys not retrievable via Redis client)"
        }
