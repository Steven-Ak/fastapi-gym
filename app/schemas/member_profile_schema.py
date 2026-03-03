from pydantic import BaseModel
from uuid import UUID
from typing import Optional
from datetime import datetime


class ProfileUpdateRequest(BaseModel):
    goal: Optional[str] = None
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    days_per_week: Optional[int] = None
    level: Optional[str] = None
    injuries: Optional[str] = None
    diseases: Optional[str] = None
    allergies: Optional[str] = None


class MemberProfileUpsert(ProfileUpdateRequest):
    pass


class MemberProfileResponse(ProfileUpdateRequest):
    id: UUID
    member_id: UUID
    updated_at: datetime

    class Config:
        from_attributes = True