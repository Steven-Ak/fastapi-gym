from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.base import MemberProfileRepositoryProtocol


class MemberProfileService:
    def __init__(self, repo: MemberProfileRepositoryProtocol):
        self.repo = repo

    async def update_profile(self, db: AsyncSession, member_id: UUID, data: dict):
        return await self.repo.upsert(db, member_id, data)

    async def get_profile(self, db: AsyncSession, member_id: UUID):
        return await self.repo.get_by_member(db, member_id)