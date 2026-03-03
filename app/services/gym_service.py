from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.gym_model import Gym
from app.repositories.gym_repository import GymRepository
from app.schemas.gym_schema import GymCreate

repo = GymRepository()


async def create_gym(db: AsyncSession, body: GymCreate) -> Gym:
    gym = Gym(**body.model_dump())
    return await repo.create(db, gym)


async def get_gym(db: AsyncSession, gym_id: UUID) -> Gym:
    gym = await repo.get_by_id(db, gym_id)
    if not gym:
        raise HTTPException(status_code=404, detail="Gym not found")
    return gym


async def get_all_gyms(db: AsyncSession) -> list[Gym]:
    return await repo.get_all(db)