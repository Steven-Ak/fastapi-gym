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

    model_config = {
        "json_schema_extra": {
            "example": {
                "goal": "build_muscle",
                "weight_kg": 80.0,
                "height_cm": 175.0,
                "days_per_week": 4,
                "level": "intermediate",
                "injuries": "knee pain",
                "diseases": "diabetes",
                "allergies": "lactose"
            }
        }
    }


class MemberProfileUpsert(ProfileUpdateRequest):
    pass


class MemberProfileResponse(ProfileUpdateRequest):
    id: UUID
    member_id: UUID
    updated_at: datetime

    class Config:
        from_attributes = True