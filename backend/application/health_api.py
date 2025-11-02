"""
API pour les endpoints de santé
Endpoints FastAPI pour la santé
"""

from fastapi import APIRouter

health_router = APIRouter()


@health_router.get("/api/hello")
async def hello():
    """Endpoint Hello World"""
    return {"message": "Hello World from Python Backend!"}


@health_router.get("/api/health")
async def health():
    """Endpoint de santé"""
    return {"status": "ok"}