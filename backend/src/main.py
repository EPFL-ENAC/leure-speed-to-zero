from src.api.routes import router
from src.config.settings import settings
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
import logging

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.decorator import cache

from src.utils.region_config import RegionConfig

from redis import asyncio as aioredis
from fastapi.middleware.gzip import GZipMiddleware
import time


# Initialize cache on startup
@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Initialize cache with Redis fallback to in-memory cache."""
    logger = logging.getLogger(__name__)

    if not settings.ENABLE_CACHE:
        logger.info("🚫 Caching disabled (development mode)")
        yield
        return

    logger.info("🚀 Initializing caching system...")

    # Get current region for cache namespacing
    current_region = RegionConfig.get_current_region()
    cache_prefix = f"fastapi-cache-{current_region.lower()}"

    logger.info(f"🌍 Using region-specific cache namespace: {cache_prefix}")

    try:
        # Try to connect to Redis
        logger.info(
            f"🔗 Attempting to connect to Redis at {settings.REDIS_HOST}:{settings.REDIS_PORT}"
        )
        redis = aioredis.from_url(
            f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}"
        )
        # Test the connection
        await redis.ping()
        FastAPICache.init(RedisBackend(redis), prefix=cache_prefix)
        logger.info(
            f"✅ CACHE BACKEND: Redis cache initialized successfully at {settings.REDIS_HOST}:{settings.REDIS_PORT}"
        )
        logger.info(
            f"📊 Cache features: Persistent, shared across instances, high performance, region: {current_region}"
        )
    except Exception as e:
        # If Redis connection fails, fall back to in-memory cache
        logger.warning(f"⚠️  Redis connection failed: {str(e)}")
        logger.warning("🔄 Falling back to in-memory cache...")
        FastAPICache.init(InMemoryBackend(), prefix=cache_prefix)
        logger.info("✅ CACHE BACKEND: In-memory cache initialized as fallback")
        logger.info(
            f"📊 Cache features: Non-persistent, single instance only, basic performance, region: {current_region}"
        )
        logger.info(
            "💡 To enable Redis caching, ensure Redis server is running on configured host:port"
        )

    yield


app = FastAPI(lifespan=lifespan, root_path=settings.PATH_PREFIX)
app.include_router(router)
app.add_middleware(GZipMiddleware, minimum_size=100000, compresslevel=1)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def get_cache_backend_info():
    """Get information about the current cache backend."""
    try:
        backend = FastAPICache.get_backend()
        if isinstance(backend, RedisBackend):
            return {
                "type": "redis",
                "name": "Redis Cache",
                "persistent": True,
                "distributed": True,
                "performance": "high",
            }
        elif isinstance(backend, InMemoryBackend):
            return {
                "type": "inmemory",
                "name": "In-Memory Cache",
                "persistent": False,
                "distributed": False,
                "performance": "basic",
            }
        else:
            return {
                "type": "unknown",
                "name": "Unknown Cache Backend",
                "persistent": False,
                "distributed": False,
                "performance": "unknown",
            }
    except Exception:
        return {
            "type": "none",
            "name": "No Cache",
            "persistent": False,
            "distributed": False,
            "performance": "none",
        }


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
    logger = logging.getLogger(__name__)
    cache_info = get_cache_backend_info()

    logger.info(f"❤️  Redis health check - Current cache backend: {cache_info['name']}")

    try:
        import redis

        r = redis.from_url(f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}")
        ping = r.ping()

        logger.info("✅ Redis health check: Connection successful")

        return {
            "status": "ok",
            "redis_connection": "successful",
            "ping": ping,
            "cache_backend": "redis",
            "backend_info": cache_info,
        }
    except Exception as e:
        logger.warning(f"⚠️  Redis health check failed: {str(e)}")

        return {
            "status": "warning",
            "redis_connection": "failed",
            "message": str(e),
            "cache_backend": "in-memory fallback",
            "backend_info": cache_info,
        }


@app.get("/test-cache")
@cache(expire=10)
async def test_cache():
    """Test endpoint to verify caching is working."""
    logger = logging.getLogger(__name__)
    cache_info = get_cache_backend_info()

    logger.info(f"🧪 Cache test request - Using {cache_info['name']} backend")

    # Add a timestamp to see if response changes
    timestamp = time.time()

    # Simulate expensive operation
    time.sleep(1)

    return {
        "cached": True,
        "timestamp": timestamp,
        "message": "If caching works, this timestamp should remain the same for 10 seconds",
        "cache_backend": cache_info,
    }


@app.get("/debug-cache")
async def debug_cache():
    """Debug endpoint to check cache status."""
    logger = logging.getLogger(__name__)
    cache_info = get_cache_backend_info()

    logger.info(f"🔍 Cache debug request - Current backend: {cache_info['name']}")

    try:
        import redis

        r = redis.from_url(f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}")

        # List keys
        all_keys = r.keys("fastapi-cache*")

        logger.info(f"📊 Redis cache status: {len(all_keys)} keys found")

        return {
            "cache_backend": "redis",
            "backend_info": cache_info,
            "all_keys": [
                key.decode() if isinstance(key, bytes) else key for key in all_keys
            ],
            "total_keys": len(all_keys),
            "redis_connection": "successful",
        }
    except Exception as e:
        logger.warning(f"⚠️  Redis debug failed: {str(e)} - Using fallback info")

        return {
            "cache_backend": "in-memory fallback",
            "backend_info": cache_info,
            "message": f"Redis not available: {str(e)}",
            "note": "Using in-memory cache (keys not retrievable via Redis client)",
        }
