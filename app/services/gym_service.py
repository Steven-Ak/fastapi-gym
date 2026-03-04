from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.gym_model import Gym
from app.repositories.base import GymRepositoryProtocol
from app.schemas.gym_schema import GymCreate


class GymService:
    def __init__(self, repo: GymRepositoryProtocol):
        self.repo = repo

    async def create_gym(self, db: AsyncSession, body: GymCreate) -> Gym:
        gym = Gym(**body.model_dump())
        return await self.repo.create(db, gym)

    async def get_gym(self, db: AsyncSession, gym_id: UUID) -> Gym:
        gym = await self.repo.get_by_id(db, gym_id)
        if not gym:
            raise NotFoundError(resource="Gym")
        return gym

    async def get_all_gyms(self, db: AsyncSession) -> list[Gym]:
        return await self.repo.get_all(db)