from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_member
from app.models.member_model import Member

from app.schemas.workout_plan_schema import AnswerRequest, OnboardingResponse
from app.schemas.member_profile_schema import ProfileUpdateRequest

from app.repositories.member_repository import MemberRepository
from app.repositories.member_profile_repository import MemberProfileRepository
from app.repositories.workout_plan_repository import WorkoutPlanRepository
from app.client.llm_client import GroqLLMClient
from app.services.member_profile_service import MemberProfileService
from app.services.workout_plan_service import WorkoutPlanService
from app.services.onboarding_service import OnboardingService

router = APIRouter(tags=["Feature 1 — Onboarding"])


def _get_onboarding_service() -> OnboardingService:
    member_repo = MemberRepository()
    profile_repo = MemberProfileRepository()
    plan_repo = WorkoutPlanRepository()
    llm_client = GroqLLMClient()

    profile_service = MemberProfileService(repo=profile_repo)
    workout_plan_service = WorkoutPlanService(
        profile_repo=profile_repo,
        plan_repo=plan_repo,
        llm_client=llm_client,
    )

    return OnboardingService(
        member_repo=member_repo,
        profile_service=profile_service,
        workout_plan_service=workout_plan_service,
    )


def _get_profile_service() -> MemberProfileService:
    return MemberProfileService(repo=MemberProfileRepository())


@router.post(
    "/onboarding/start",
    response_model=OnboardingResponse,
    summary="Initialize 6-question survey. Sets current_step = Q1.",
)
async def start(
    db: AsyncSession = Depends(get_db),
    current: Member = Depends(get_current_member),
    service: OnboardingService = Depends(_get_onboarding_service),
):
    return await service.start(db, current.id)


@router.post(
    "/onboarding/answer",
    response_model=OnboardingResponse,
    summary="Submit answer. Advances Q1→Q6. On Q6: saves profile and completes onboarding.",
)
async def answer(
    body: AnswerRequest,
    db: AsyncSession = Depends(get_db),
    current: Member = Depends(get_current_member),
    service: OnboardingService = Depends(_get_onboarding_service),
):
    return await service.answer(db, current.id, body.answer)


@router.post("/onboarding/generate-plan", summary="Generate AI workout plan after completing onboarding.")
async def generate_plan(
    db: AsyncSession = Depends(get_db),
    current: Member = Depends(get_current_member),
    service: OnboardingService = Depends(_get_onboarding_service),
):
    return await service.generate_plan(db, current.id)


@router.get("/onboarding/my-plan", summary="Get my active workout plan.")
async def get_my_plan(
    db: AsyncSession = Depends(get_db),
    current: Member = Depends(get_current_member),
    service: OnboardingService = Depends(_get_onboarding_service),
):
    return await service.get_plan(db, current.id)


@router.patch("/members/me/profile", summary="Update profile fields.")
async def update_profile(
    body: ProfileUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current: Member = Depends(get_current_member),
    service: MemberProfileService = Depends(_get_profile_service),
):
    update = body.model_dump(exclude_unset=True)
    if not update:
        from app.core.exceptions import ValidationError
        raise ValidationError(detail="No fields provided to update")

    await service.update_profile(db, current.id, update)
    return {"message": "تم تحديث الملف الشخصي", "updated_fields": list(update.keys())}