"""
API for health endpoints
"""

from fastapi import APIRouter

health_router = APIRouter()


@health_router.get("/api/health")
async def health():
    """Health endpoint"""
    return {"status": "ok"}
