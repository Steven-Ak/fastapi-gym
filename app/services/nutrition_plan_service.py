import json
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.repositories.nutrition_plan_repository import NutritionPlanRepository
from app.repositories.member_profile_repository import MemberProfileRepository
from app.client.llm_client import GroqLLMClient
from app.services.nutrition_knowledge_service import NutritionKnowledge


class NutritionPlanService:

    def __init__(self):
        self.plan_repo = NutritionPlanRepository()
        self.profile_repo = MemberProfileRepository()
        self.llm = GroqLLMClient()
        self.knowledge = NutritionKnowledge()

    async def generate_plan(self, db: AsyncSession, member_id: UUID) -> dict:
        #  Load profile
        profile = await self.profile_repo.get_by_member(db, member_id)
        if not profile:
            raise NotFoundError(resource="Member profile — complete onboarding first")

        goal      = profile.goal      or "maintain_weight"
        weight    = profile.weight_kg or 70.0
        height    = profile.height_cm or 170.0
        diseases  = profile.diseases
        allergies = profile.allergies

        #  Calculate calorie target
        calorie_target = self.knowledge.calculate_calories(weight, height, goal)

        # Build RAG context
        rag_context = self.knowledge.build_rag_context(
            goal=goal,
            weight_kg=weight,
            height_cm=height,
            diseases=diseases,
            allergies=allergies,
            calorie_target=calorie_target,
        )

        #  Call LLM client
        meal_plan_json = await self.llm.generate_nutrition_plan(
            goal=goal,
            weight=weight,
            height=height,
            calorie_target=calorie_target,
            diseases=diseases,
            allergies=allergies,
            rag_context=rag_context,
        )

        #  Save to DB
        plan = await self.plan_repo.create(
            db,
            member_id=member_id,
            meal_plan_json=meal_plan_json,
            calorie_target=calorie_target,
        )

        return {
            "plan_id": str(plan.id),
            "calorie_target": plan.calorie_target,
            "generated_at": str(plan.generated_at),
            "meal_plan_json": plan.meal_plan_json,
        }


    async def get_active_plan(self, db: AsyncSession, member_id: UUID) -> dict:
        plan = await self.plan_repo.get_active(db, member_id)
        if not plan:
            raise NotFoundError(resource="Active nutrition plan")

        return {
            "plan_id": str(plan.id),
            "calorie_target": plan.calorie_target,
            "generated_at": str(plan.generated_at),
            "meal_plan_json": plan.meal_plan_json,
        }

    async def ask_question(
        self, db: AsyncSession, member_id: UUID, question: str
    ) -> dict:
        #  Load active plan
        plan = await self.plan_repo.get_active(db, member_id)
        if not plan:
            raise NotFoundError(
                resource="Active nutrition plan — generate one first via POST /nutrition/generate"
            )

        #  Load profile
        profile   = await self.profile_repo.get_by_member(db, member_id)
        goal      = profile.goal      if profile else "maintain_weight"
        weight    = profile.weight_kg if profile else 70.0
        height    = profile.height_cm if profile else 170.0
        diseases  = profile.diseases  if profile else None
        allergies = profile.allergies if profile else None

        # Build RAG context
        rag_context = self.knowledge.build_rag_context(
            goal=goal,
            weight_kg=weight,
            height_cm=height,
            diseases=diseases,
            allergies=allergies,
            calorie_target=plan.calorie_target,
        )

        # Truncate plan to first week to save tokens
        plan_json = plan.meal_plan_json
        if isinstance(plan_json, dict) and "days" in plan_json:
            first_week = dict(list(plan_json["days"].items())[:7])
            plan_snippet = json.dumps({"days": first_week}, ensure_ascii=False)
        else:
            plan_snippet = json.dumps(plan_json, ensure_ascii=False)[:2000]

        #  Call LLM client
        answer = await self.llm.ask_nutrition_question(
            question=question,
            calorie_target=plan.calorie_target,
            diseases=diseases,
            allergies=allergies,
            rag_context=rag_context,
            plan_snippet=plan_snippet,
        )

        return {"question": question, "answer": answer}