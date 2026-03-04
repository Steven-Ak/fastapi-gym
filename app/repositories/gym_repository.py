from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.gym_model import Gym


class GymRepository:
    async def get_by_id(self, db: AsyncSession, gym_id: UUID) -> Gym | None:
        result = await db.execute(select(Gym).where(Gym.id == gym_id))
        return result.scalar_one_or_none()

    async def get_all(self, db: AsyncSession) -> list[Gym]:
        result = await db.execute(select(Gym))
        return list(result.scalars().all())

    async def create(self, db: AsyncSession, gym: Gym) -> Gym:
        db.add(gym)
        await db.commit()
        await db.refresh(gym)
        return gym