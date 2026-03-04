from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.repositories.checkin_repository import CheckinRepository
from app.repositories.member_repository import MemberRepository
from app.services.checkin_service import CheckinService


def get_checkin_service() -> CheckinService:
    return CheckinService(
        checkin_repo=CheckinRepository(),
        member_repo=MemberRepository(),
    )