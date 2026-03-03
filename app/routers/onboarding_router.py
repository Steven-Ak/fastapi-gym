from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import re

from app.database import get_db
from app.dependencies.auth import get_current_member
from app.models.member_model import Member

from app.schemas.workout_plan_schema import AnswerRequest, OnboardingResponse
from app.schemas.member_profile_schema import ProfileUpdateRequest

from app.services import member_profile_service, workout_plan_service
from app.repositories.member_repository import MemberRepository

router = APIRouter(tags=["Feature 1 — Onboarding"])

member_repo = MemberRepository()

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


@router.post(
    "/onboarding/start",
    response_model=OnboardingResponse,
    summary="Initialize 6-question survey. Sets current_step = Q1.",
)
async def start(
    db: AsyncSession = Depends(get_db),
    current: Member = Depends(get_current_member),
):
    member = await member_repo.get_by_id(db, current.id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    if member.current_step == "done":
        raise HTTPException(
            status_code=400,
            detail="Onboarding already completed. Use PUT /members/me/profile to update.",
        )

    await member_repo.update_step(db, member.id, "Q1")

    return OnboardingResponse(
        message=f"مرحباً {member.name}! سنبدأ إنشاء خطتك الشخصية.",
        current_step="Q1",
        question=QUESTIONS["Q1"],
    )


@router.post(
    "/onboarding/answer",
    response_model=OnboardingResponse,
    summary="Submit answer. Advances Q1→Q6. On Q6: saves profile and completes onboarding.",
)
async def answer(
    body: AnswerRequest,
    db: AsyncSession = Depends(get_db),
    current: Member = Depends(get_current_member),
):
    member = await member_repo.get_by_id(db, current.id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    step = member.current_step

    if not step or step == "done":
        raise HTTPException(status_code=400, detail="No active onboarding. Call POST /onboarding/start first.")

    ans = body.answer.strip()
    update: dict = {}

    if step == "Q1":
        valid = ["lose_weight", "build_muscle", "get_fit"]
        if ans not in valid:
            return OnboardingResponse(message=f"اختر: {' / '.join(valid)}", current_step="Q1", question=QUESTIONS["Q1"])
        update["goal"] = ans

    elif step == "Q2":
        nums = re.findall(r"\d+\.?\d*", ans)
        if len(nums) < 2:
            return OnboardingResponse(message="أدخل الوزن والطول. مثال: 80 175", current_step="Q2", question=QUESTIONS["Q2"])
        update["weight_kg"] = float(nums[0])
        update["height_cm"] = float(nums[1])

    elif step == "Q3":
        nums = re.findall(r"\d+", ans)
        if not nums or not (1 <= int(nums[0]) <= 7):
            return OnboardingResponse(message="أدخل رقماً بين 1 و 7", current_step="Q3", question=QUESTIONS["Q3"])
        update["days_per_week"] = int(nums[0])

    elif step == "Q4":
        valid = ["beginner", "intermediate", "advanced"]
        if ans not in valid:
            return OnboardingResponse(message=f"اختر: {' / '.join(valid)}", current_step="Q4", question=QUESTIONS["Q4"])
        update["level"] = ans

    elif step == "Q5":
        update["injuries"] = None if ans in NO_ANSWERS else ans

    elif step == "Q6":
        update["diseases"] = None if ans in NO_ANSWERS else ans
        update["allergies"] = None if ans in NO_ANSWERS else ans

    # save answer
    await member_profile_service.update_profile(db, member.id, update)

    idx = STEPS.index(step)
    next_step = STEPS[idx + 1] if idx + 1 < len(STEPS) else "done"
    await member_repo.update_step(db, member.id, next_step)

    if next_step == "done":
        return OnboardingResponse(
            message="تم حفظ بياناتك بنجاح! استخدم POST /onboarding/generate-plan لإنشاء خطتك.",
            current_step="done",
        )

    return OnboardingResponse(
        message="تم حفظ إجابتك",
        current_step=next_step,
        question=QUESTIONS[next_step],
    )


@router.post("/onboarding/generate-plan", summary="Generate AI workout plan after completing onboarding.")
async def generate_plan(
    db: AsyncSession = Depends(get_db),
    current: Member = Depends(get_current_member),
):
    
    member = await member_repo.get_by_id(db, current.id)
    if not member or member.current_step != "done":
        raise HTTPException(
            status_code=400,
            detail="Complete onboarding first (answer all 6 questions).",
        )

   
    profile = await member_profile_service.get_profile(db, current.id)
    if not profile:
        raise HTTPException(status_code=400, detail="Profile not found. Complete onboarding first.")

   
    plan = await workout_plan_service.create_plan(db, current.id)
    return plan


@router.get("/onboarding/my-plan", summary="Get my active workout plan.")
async def get_my_plan(
    db: AsyncSession = Depends(get_db),
    current: Member = Depends(get_current_member),
):
    plan = await workout_plan_service.get_active_plan(db, current.id)
    if not plan:
        raise HTTPException(
            status_code=404,
            detail="No active plan. Use POST /onboarding/generate-plan to create one.",
        )
    return plan


@router.patch("/members/me/profile", summary="Update profile fields.")
async def update_profile(
    body: ProfileUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current: Member = Depends(get_current_member),
):
    update = {k: v for k, v in body.model_dump().items() if v is not None}
    if not update:
        raise HTTPException(status_code=400, detail="No fields provided to update")

    await member_profile_service.update_profile(db, current.id, update)
    return {"message": "تم تحديث الملف الشخصي", "updated_fields": list(update.keys())}