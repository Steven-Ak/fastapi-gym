from pydantic import BaseModel
from typing import Optional


class AnswerRequest(BaseModel):
    answer: str


class ProfileUpdateRequest(BaseModel):
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    injuries: Optional[str] = None
    diseases: Optional[str] = None
    allergies: Optional[str] = None


class OnboardingResponse(BaseModel):
    message: str
    current_step: str
    question: Optional[str] = None
    plan_id: Optional[str] = None
    plan: Optional[dict] = None