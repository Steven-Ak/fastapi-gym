from pydantic import BaseModel
from uuid import UUID
from typing import Optional
from datetime import datetime


class AnswerRequest(BaseModel):
    answer: str


class OnboardingResponse(BaseModel):
    message: str
    current_step: str
    question: Optional[str] = None
    plan_id: Optional[str] = None
    plan: Optional[dict] = None


class WorkoutPlanResponse(BaseModel):
    id: UUID
    member_id: UUID
    plan_json: dict
    week_number: int
    is_active: bool
    generated_at: datetime

    class Config:
        from_attributes = True