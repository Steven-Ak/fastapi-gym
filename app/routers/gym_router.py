from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.database import get_db
from app.schemas.gym_schema import GymCreate, GymResponse
from app.services import gym_service

router = APIRouter(prefix="/gyms", tags=["Gyms"])


@router.post("/", response_model=GymResponse)
async def create_gym(body: GymCreate, db: AsyncSession = Depends(get_db)):
    return await gym_service.create_gym(db, body)


@router.get("/{gym_id}", response_model=GymResponse)
async def get_gym(gym_id: UUID, db: AsyncSession = Depends(get_db)):
    return await gym_service.get_gym(db, gym_id)