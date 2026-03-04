from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.repositories.base import MemberProfileRepositoryProtocol, WorkoutPlanRepositoryProtocol
from app.client.protocols import LLMClientProtocol


class WorkoutPlanService:
    def __init__(
        self,
        profile_repo: MemberProfileRepositoryProtocol,
        plan_repo: WorkoutPlanRepositoryProtocol,
        llm_client: LLMClientProtocol,
    ):
        self.profile_repo = profile_repo
        self.plan_repo = plan_repo
        self.llm_client = llm_client

    async def create_plan(self, db: AsyncSession, member_id: UUID) -> dict:
        profile = await self.profile_repo.get_by_member(db, member_id)
        if not profile:
            raise NotFoundError(resource="Member profile")

        profile_dict = {
            "goal": profile.goal,
            "level": profile.level,
            "days_per_week": profile.days_per_week,
            "weight_kg": profile.weight_kg,
            "height_cm": profile.height_cm,
            "injuries": profile.injuries,
            "diseases": profile.diseases,
        }

        plan_json = await self.llm_client.generate_workout_plan(profile_dict)
        created = await self.plan_repo.create(db, member_id=member_id, plan_json=plan_json)

        return {
            "plan_id": str(created.id),
            "plan": created.plan_json,
        }

    async def get_active_plan(self, db: AsyncSession, member_id: UUID):
        plan = await self.plan_repo.get_active(db, member_id)
        if not plan:
            return None
        return {
            "plan_id": str(plan.id),
            "plan": plan.plan_json,
            "week_number": plan.week_number,
            "generated_at": str(plan.generated_at),
        }