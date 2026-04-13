from uuid import UUID
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.checkin_repository import CheckinRepository
from app.repositories.member_repository import MemberRepository
from app.client.llm_client import GroqLLMClient
from app.core.exceptions import NotFoundError, BadRequestError
from app.models.checkin_model import Checkin


class CheckinService:

    STATUS_MAP = {
        "done": "أكمل التمرين بالكامل",
        "partial": "أكمل جزءاً من التمرين",
        "skipped": "لم يتمرن اليوم",
    }

    def __init__(
        self,
        checkin_repo: CheckinRepository,
        member_repo: MemberRepository,
    ):
        self.checkin_repo = checkin_repo
        self.member_repo = member_repo
        self.llm = GroqLLMClient()

    async def create_checkin(self, db: AsyncSession, member_id: UUID, status: str) -> Checkin:
        member = await self.member_repo.get_by_id(db, member_id)
        if not member:
            raise NotFoundError(f"Member with id {member_id} not found")

        if not member.is_member_active:
            raise BadRequestError("Member subscription is not active")

        today = date.today()
        existing = await self.checkin_repo.get_by_member_id_and_date(db, member_id, today)
        if existing:
            raise BadRequestError("Member already checked in today")

        system = "أنت مدرب رياضي محفّز. اكتب رسالة تحفيزية قصيرة بالعربية [جملة واحدة] فقط بدون رموز تعبيرية كثيرة."
        user = f"العضو {member.name} سجّل حضوره اليوم. حالة التمرين: {self.STATUS_MAP.get(status, status)}."
        ai_response = await self.llm._chat(system=system, user=user)

        checkin = await self.checkin_repo.create(
            db=db,
            member_id=member_id,
            status=status,
            ai_response=ai_response,
            checkin_date=today,
        )

        return checkin

    async def get_my_checkins(self, db: AsyncSession, member_id: UUID) -> list[Checkin]:
        member = await self.member_repo.get_by_id(db, member_id)
        if not member:
            raise NotFoundError(f"Member with id {member_id} not found")
        return await self.checkin_repo.get_by_member_id(db, member_id)

    async def get_member_checkins(self, db: AsyncSession, member_id: UUID) -> list[Checkin]:
        member = await self.member_repo.get_by_id(db, member_id)
        if not member:
            raise NotFoundError(f"Member with id {member_id} not found")
        return await self.checkin_repo.get_by_member_id(db, member_id)