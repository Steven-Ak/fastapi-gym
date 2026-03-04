from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.database import get_db
from app.schemas.gym_schema import GymCreate, GymResponse
from app.repositories.gym_repository import GymRepository
from app.services.gym_service import GymService

router = APIRouter(prefix="/gyms", tags=["Gyms"])


def _get_gym_service() -> GymService:
    return GymService(repo=GymRepository())


@router.post("/", response_model=GymResponse)
async def create_gym(
    body: GymCreate,
    db: AsyncSession = Depends(get_db),
    service: GymService = Depends(_get_gym_service),
):
    return await service.create_gym(db, body)


@router.get("/{gym_id}", response_model=GymResponse)
async def get_gym(
    gym_id: UUID,
    db: AsyncSession = Depends(get_db),
    service: GymService = Depends(_get_gym_service),
):
    return await service.get_gym(db, gym_id)