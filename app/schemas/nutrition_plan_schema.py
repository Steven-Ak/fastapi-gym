from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime



class NutritionAskRequest(BaseModel):
    question: str



class NutritionPlanResponse(BaseModel):
    plan_id: UUID
    calorie_target: Optional[int]
    meal_plan_json: dict
    generated_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


class NutritionAskResponse(BaseModel):
    question: str
    answer: str