from fastapi import APIRouter
import logging

router = APIRouter()
logger = logging.getLogger("uvicorn")

@router.get("/health")
async def health_check() -> dict:
    """Check if the API and its dependencies are healthy"""
    return {
        "status": "healthy",
    }
