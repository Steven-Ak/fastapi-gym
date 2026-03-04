from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, desc

from app.models.nutrition_plan_model import NutritionPlan


class NutritionPlanRepository:

    async def get_active(self, db: AsyncSession, member_id: UUID) -> NutritionPlan | None:
        res = await db.execute(
            select(NutritionPlan)
            .where(NutritionPlan.member_id == member_id, NutritionPlan.is_active == True)
            .order_by(desc(NutritionPlan.generated_at))
            .limit(1)
        )
        return res.scalar_one_or_none()

    async def create(
        self,
        db: AsyncSession,
        member_id: UUID,
        meal_plan_json: dict,
        calorie_target: int | None,
    ) -> NutritionPlan:
        # Deactivate all existing active plans for this member
        await db.execute(
            update(NutritionPlan)
            .where(NutritionPlan.member_id == member_id, NutritionPlan.is_active == True)
            .values(is_active=False)
        )

        plan = NutritionPlan(
            member_id=member_id,
            meal_plan_json=meal_plan_json,
            calorie_target=calorie_target,
            is_active=True,
        )
        db.add(plan)
        await db.commit()
        await db.refresh(plan)
        return plan