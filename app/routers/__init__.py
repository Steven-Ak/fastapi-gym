from fastapi import APIRouter

from app.routers.auth_router import router as auth_router
from app.routers.gym_router import router as gym_router
from app.routers.onboarding_router import router as onboarding_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(gym_router)
api_router.include_router(onboarding_router)
