from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.database import Base, engine
from app.core.exceptions import (
    NotFoundError,
    AlreadyExistsError,
    AuthenticationError,
    AuthorizationError,
    ValidationError,
    ExternalServiceError,
)

from app.models.gym_model import Gym 
from app.models.member_model import Member  
from app.models.member_profile_model import MemberProfile  
from app.models.workout_plan_model import WorkoutPlan 

from app.routers import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="GymIQ — AI Gym Intelligence",
    description="Powered by Zedny | Phase 1 — FastAPI + Supabase + Groq",
    version="1.0.0",
    lifespan=lifespan,
)




@app.exception_handler(NotFoundError)
async def not_found_handler(_: Request, exc: NotFoundError):
    return JSONResponse(status_code=404, content={"detail": exc.detail})


@app.exception_handler(AlreadyExistsError)
async def already_exists_handler(_: Request, exc: AlreadyExistsError):
    return JSONResponse(status_code=400, content={"detail": exc.detail})


@app.exception_handler(AuthenticationError)
async def authentication_handler(_: Request, exc: AuthenticationError):
    return JSONResponse(status_code=401, content={"detail": exc.detail})


@app.exception_handler(AuthorizationError)
async def authorization_handler(_: Request, exc: AuthorizationError):
    return JSONResponse(status_code=403, content={"detail": exc.detail})


@app.exception_handler(ValidationError)
async def validation_handler(_: Request, exc: ValidationError):
    return JSONResponse(status_code=422, content={"detail": exc.detail})


@app.exception_handler(ExternalServiceError)
async def external_service_handler(_: Request, exc: ExternalServiceError):
    return JSONResponse(status_code=502, content={"detail": exc.detail})


#Router
app.include_router(router)