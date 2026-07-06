"""API v1 package."""
from fastapi import APIRouter

from app.api.v1.intent import router as intent_router

api_router = APIRouter()

# Include all v1 routers
api_router.include_router(intent_router)

__all__ = ["api_router"]
