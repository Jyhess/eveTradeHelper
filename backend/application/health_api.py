"""
API pour les endpoints de santé
"""

from fastapi import APIRouter

health_router = APIRouter()


@health_router.get("/api/health")
async def health():
    """Endpoint de santé"""
    return {"status": "ok"}