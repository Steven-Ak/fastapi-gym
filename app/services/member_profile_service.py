from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.member_profile_repository import MemberProfileRepository

repo = MemberProfileRepository()

async def update_profile(db: AsyncSession, member_id: UUID, data: dict):
    return await repo.upsert(db, member_id, data)

async def get_profile(db: AsyncSession, member_id: UUID):
    return await repo.get_by_member(db, member_id)