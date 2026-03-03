from fastapi import FastAPI
from app.database import Base, engine
from app.models.gym_model import Gym  
from app.models.member_model import Member  
from app.models.member_profile_model import MemberProfile  
from app.models.workout_plan_model import WorkoutPlan  
from app.routers.auth_router import router as auth_router
from app.routers.onboarding_router import router as onboarding_router
from app.routers.gym_router import router as gym_router


app = FastAPI(
    title="GymIQ — AI Gym Intelligence",
    description="Powered by Zedny | Phase 1 — FastAPI + Supabase + Groq",
    version="1.0.0",
)

@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


app.include_router(auth_router)
app.include_router(onboarding_router)
app.include_router(gym_router)