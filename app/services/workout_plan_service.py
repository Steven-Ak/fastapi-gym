from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.member_profile_repository import MemberProfileRepository
from app.repositories.workout_plan_repository import WorkoutPlanRepository
from app.client.llm_client import generate_workout_plan

profile_repo = MemberProfileRepository()
plan_repo = WorkoutPlanRepository()


async def create_plan(db: AsyncSession, member_id: UUID) -> dict:
    profile = await profile_repo.get_by_member(db, member_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Member profile not found")

    profile_dict = {
        "goal": profile.goal,
        "level": profile.level,
        "days_per_week": profile.days_per_week,
        "weight_kg": profile.weight_kg,
        "height_cm": profile.height_cm,
        "injuries": profile.injuries,
        "diseases": profile.diseases,
    }

    plan_json = await generate_workout_plan(profile_dict)
    created = await plan_repo.create(db, member_id=member_id, plan_json=plan_json)

    return {
        "plan_id": str(created.id),
        "plan": created.plan_json,
    }


async def get_active_plan(db: AsyncSession, member_id: UUID):
    plan = await plan_repo.get_active(db, member_id)
    if not plan:
        return None
    return {
        "plan_id": str(plan.id),
        "plan": plan.plan_json,
        "week_number": plan.week_number,
        "generated_at": str(plan.generated_at),
    }