from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.member_model import Member


class MemberRepository:
    async def get_by_id(self, db: AsyncSession, member_id: UUID) -> Member | None:
        result = await db.execute(select(Member).where(Member.id == member_id))
        return result.scalar_one_or_none()

    async def get_by_phone_and_gym(self, db: AsyncSession, phone: str, gym_id: UUID) -> Member | None:
        result = await db.execute(
            select(Member).where(Member.phone == phone, Member.gym_id == gym_id)
        )
        return result.scalar_one_or_none()

    async def create(self, db: AsyncSession, member: Member) -> Member:
        db.add(member)
        await db.commit()
        await db.refresh(member)
        return member

    async def update_step(self, db: AsyncSession, member_id: UUID, step: str | None) -> Member | None:
        member = await self.get_by_id(db, member_id)
        if not member:
            return None
        member.current_step = step
        await db.commit()
        await db.refresh(member)
        return member