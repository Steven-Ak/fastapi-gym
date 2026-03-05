from uuid import UUID
from datetime import date
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.checkin_model import Checkin


class CheckinRepository:

    async def create(self, db: AsyncSession, member_id: UUID, status: str, ai_response: Optional[str], checkin_date: date) -> Checkin:
        checkin = Checkin(
            member_id=member_id,
            status=status,
            ai_response=ai_response,
            checkin_date=checkin_date,
        )
        db.add(checkin)
        await db.commit()
        await db.refresh(checkin)
        return checkin

    async def get_by_member_id(self, db: AsyncSession, member_id: UUID) -> list[Checkin]:
        result = await db.execute(
            select(Checkin).where(Checkin.member_id == member_id).order_by(Checkin.checkin_date.desc())
        )
        return result.scalars().all()

    async def get_by_member_id_and_date(self, db: AsyncSession, member_id: UUID, checkin_date: date) -> Optional[Checkin]:
        result = await db.execute(
            select(Checkin).where(Checkin.member_id == member_id, Checkin.checkin_date == checkin_date)
        )
        return result.scalar_one_or_none()

    async def get_checkins_between_dates(self, db: AsyncSession, member_id: UUID, start_date: date, end_date: date) -> list[Checkin]:
        result = await db.execute(
            select(Checkin)
            .where(Checkin.member_id == member_id, Checkin.checkin_date >= start_date, Checkin.checkin_date <= end_date)
            .order_by(Checkin.checkin_date.desc())
        )
        return result.scalars().all()

    async def count_by_member_id(self, db: AsyncSession, member_id: UUID) -> int:
        result = await db.execute(
            select(func.count()).where(Checkin.member_id == member_id)
        )
        return result.scalar() or 0