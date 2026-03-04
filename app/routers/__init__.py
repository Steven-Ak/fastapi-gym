from fastapi import APIRouter

from app.routers.auth_router import router as auth_router
from app.routers.gym_router import router as gym_router
from app.routers.onboarding_router import router as onboarding_router
from app.routers.qa_log_router import router as qa_log_router

router = APIRouter()

router.include_router(auth_router)
router.include_router(gym_router)
router.include_router(onboarding_router)
router.include_router(qa_log_router)