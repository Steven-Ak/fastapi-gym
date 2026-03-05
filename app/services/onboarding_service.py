import re
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.repositories.base import MemberRepositoryProtocol
from app.services.member_profile_service import MemberProfileService
from app.services.workout_plan_service import WorkoutPlanService


STEPS = ["Q1", "Q2", "Q3", "Q4", "Q5", "Q6"]
NO_ANSWERS = ["لا", "no", "la", "لا يوجد"]

QUESTIONS = {
    "Q1": "ما هو هدفك؟ (lose_weight / build_muscle / get_fit)",
    "Q2": "ما هو وزنك بالكيلو وطولك بالسنتيمتر؟ (مثال: 80 175)",
    "Q3": "كم يوماً في الأسبوع تستطيع التدريب؟ (1-7)",
    "Q4": "ما هو مستواك الحالي؟ (beginner / intermediate / advanced)",
    "Q5": "هل لديك أي إصابات أو قيود جسدية؟ (اكتب لا إذا لم يكن)",
    "Q6": "هل لديك أمراض أو حساسية من أطعمة؟ (اكتب لا إذا لم يكن)",
}


class OnboardingService:
    def __init__(
        self,
        member_repo: MemberRepositoryProtocol,
        profile_service: MemberProfileService,
        workout_plan_service: WorkoutPlanService,
    ):
        self.member_repo = member_repo
        self.profile_service = profile_service
        self.workout_plan_service = workout_plan_service

    # ── helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _validate_answer(step: str, answer: str) -> dict | str:
        """
        Returns a dict of profile fields to update on success,
        or a string error message on failure.
        """
        ans = answer.strip()

        if step == "Q1":
            valid = ["lose_weight", "build_muscle", "get_fit"]
            if ans not in valid:
                return f"اختر: {' / '.join(valid)}"
            return {"goal": ans}

        if step == "Q2":
            nums = re.findall(r"\d+\.?\d*", ans)
            if len(nums) < 2:
                return "أدخل الوزن والطول. مثال: 80 175"
            return {"weight_kg": float(nums[0]), "height_cm": float(nums[1])}

        if step == "Q3":
            nums = re.findall(r"\d+", ans)
            if not nums or not (1 <= int(nums[0]) <= 7):
                return "أدخل رقماً بين 1 و 7"
            return {"days_per_week": int(nums[0])}

        if step == "Q4":
            valid = ["beginner", "intermediate", "advanced"]
            if ans not in valid:
                return f"اختر: {' / '.join(valid)}"
            return {"level": ans}

        if step == "Q5":
            return {"injuries": None if ans in NO_ANSWERS else ans}

        if step == "Q6":
            value = None if ans in NO_ANSWERS else ans
            return {"diseases": value, "allergies": value}

        return "Unknown step"

    # ── public API ─────────────────────────────────────────────────────

    async def start(self, db: AsyncSession, member_id: UUID) -> dict:
        member = await self.member_repo.get_by_id(db, member_id)
        if not member:
            raise NotFoundError(resource="Member")

        if member.current_step == "done":
            raise ValidationError(
                detail="Onboarding already completed. Use PUT /members/me/profile to update."
            )

        await self.member_repo.update_step(db, member.id, "Q1")

        return {
            "message": f"مرحباً {member.name}! سنبدأ إنشاء خطتك الشخصية.",
            "current_step": "Q1",
            "question": QUESTIONS["Q1"],
        }

    async def answer(self, db: AsyncSession, member_id: UUID, raw_answer: str) -> dict:
        member = await self.member_repo.get_by_id(db, member_id)
        if not member:
            raise NotFoundError(resource="Member")

        step = member.current_step
        if not step or step == "done":
            raise ValidationError(
                detail="No active onboarding. Call POST /onboarding/start first."
            )

        result = self._validate_answer(step, raw_answer)

        # validation failed → return the same question with an error hint
        if isinstance(result, str):
            return {
                "message": result,
                "current_step": step,
                "question": QUESTIONS[step],
            }

        # save valid answer
        await self.profile_service.update_profile(db, member.id, result)

        idx = STEPS.index(step)
        next_step = STEPS[idx + 1] if idx + 1 < len(STEPS) else "done"
        await self.member_repo.update_step(db, member.id, next_step)

        if next_step == "done":
            return {
                "message": "تم حفظ بياناتك بنجاح! استخدم POST /onboarding/generate-plan لإنشاء خطتك.",
                "current_step": "done",
            }

        return {
            "message": "تم حفظ إجابتك",
            "current_step": next_step,
            "question": QUESTIONS[next_step],
        }

    async def generate_plan(self, db: AsyncSession, member_id: UUID) -> dict:
        member = await self.member_repo.get_by_id(db, member_id)
        if not member or member.current_step != "done":
            raise ValidationError(
                detail="Complete onboarding first (answer all 6 questions)."
            )

        profile = await self.profile_service.get_profile(db, member_id)
        if not profile:
            raise NotFoundError(resource="Member profile")

        return await self.workout_plan_service.create_plan(db, member_id)

    async def get_plan(self, db: AsyncSession, member_id: UUID) -> dict:
        plan = await self.workout_plan_service.get_active_plan(db, member_id)
        if not plan:
            raise NotFoundError(
                detail="No active plan. Use POST /onboarding/generate-plan to create one."
            )
        return plan
