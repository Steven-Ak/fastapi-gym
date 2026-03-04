from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.checkin_schema import (
    CheckinCreateRequest,
    CheckinResponse,
    CheckinListResponse,
)
from app.services.checkin_service import CheckinService
from app.dependencies.auth import get_current_member
from app.dependencies.checkin_deps import get_checkin_service
from app.database import get_db


router = APIRouter(prefix="/checkins", tags=["Check-ins"])


@router.post(
    "",
    response_model=CheckinResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Simulate QR Check-in",
)
async def create_checkin(
    request: CheckinCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_member=Depends(get_current_member),
    service: CheckinService = Depends(get_checkin_service),
):
    checkin = await service.create_checkin(
        db=db,
        member_id=current_member.id,
        status=request.status.value,
    )
    return CheckinResponse(
        id=checkin.id,
        member_id=checkin.member_id,
        status=checkin.status,
        ai_response=checkin.ai_response,
        checkin_date=checkin.checkin_date,
        created_at=checkin.created_at,
    )


@router.get(
    "/me",
    response_model=CheckinListResponse,
    summary="My Check-in History",
)
async def get_my_checkins(
    db: AsyncSession = Depends(get_db),
    current_member=Depends(get_current_member),
    service: CheckinService = Depends(get_checkin_service),
):
    checkins = await service.get_my_checkins(db=db, member_id=current_member.id)
    return CheckinListResponse(
        checkins=[
            CheckinResponse(
                id=c.id,
                member_id=c.member_id,
                status=c.status,
                ai_response=c.ai_response,
                checkin_date=c.checkin_date,
                created_at=c.created_at,
            )
            for c in checkins
        ],
        total=len(checkins),
    )


@router.get(
    "/{member_id}",
    response_model=CheckinListResponse,
    summary="Admin — Member Check-in History",
)
async def get_member_checkins(
    member_id: UUID,
    db: AsyncSession = Depends(get_db),
    service: CheckinService = Depends(get_checkin_service),
):
    checkins = await service.get_member_checkins(db=db, member_id=member_id)
    return CheckinListResponse(
        checkins=[
            CheckinResponse(
                id=c.id,
                member_id=c.member_id,
                status=c.status,
                ai_response=c.ai_response,
                checkin_date=c.checkin_date,
                created_at=c.created_at,
            )
            for c in checkins
        ],
        total=len(checkins),
    )