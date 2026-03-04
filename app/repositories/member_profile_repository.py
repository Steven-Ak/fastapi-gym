from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.member_profile_model import MemberProfile


class MemberProfileRepository:
    async def get_by_member(self, db: AsyncSession, member_id: UUID) -> MemberProfile | None:
        res = await db.execute(select(MemberProfile).where(MemberProfile.member_id == member_id))
        return res.scalar_one_or_none()

    async def upsert(self, db: AsyncSession, member_id: UUID, data: dict) -> MemberProfile:
        profile = await self.get_by_member(db, member_id)

        if profile:
            for k, v in data.items():
                if hasattr(profile, k):
                    setattr(profile, k, v)
            await db.commit()
            await db.refresh(profile)
            return profile

        profile = MemberProfile(member_id=member_id, **data)
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
        return profile