from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, desc

from app.models.workout_plan_model import WorkoutPlan


class WorkoutPlanRepository:
    async def get_active(self, db: AsyncSession, member_id: UUID) -> WorkoutPlan | None:
        res = await db.execute(
            select(WorkoutPlan)
            .where(WorkoutPlan.member_id == member_id, WorkoutPlan.is_active == True) 
            .order_by(desc(WorkoutPlan.generated_at))
            .limit(1)
        )
        return res.scalar_one_or_none()

    async def create(self, db: AsyncSession, member_id: UUID, plan_json: dict) -> WorkoutPlan:
        # deactivate old active plans
        await db.execute(
            update(WorkoutPlan)
            .where(WorkoutPlan.member_id == member_id, WorkoutPlan.is_active == True)  
            .values(is_active=False)
        )

        obj = WorkoutPlan(
            member_id=member_id,
            plan_json=plan_json,
            week_number=1,
            is_active=True,
            adapted_from_id=None,
        )
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj