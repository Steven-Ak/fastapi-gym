from pydantic import BaseModel, Field
from typing import Optional


class AskRequest(BaseModel):
    question: str = Field(..., min_length=3, description="سؤالك عن التمارين بالعربية أو الإنجليزية")
    top_k: int = Field(default=5, ge=1, le=20, description="عدد التمارين المسترجعة من RAG")

    model_config = {
        "json_schema_extra": {
            "example": {
                "question": "ما هي أفضل تمارين لبناء عضلة الصدر للمبتدئين؟",
                "top_k": 5,
            }
        }
    }


class ExerciseSource(BaseModel):
    exercise_id: Optional[str] = None
    name: Optional[str] = None
    name_ar: Optional[str] = None
    level: Optional[str] = None
    equipment: Optional[list[str]] = None
    video_urls: Optional[list[str]] = None


class AskResponse(BaseModel):
    answer: str
    sources: list[ExerciseSource]


class SeedResponse(BaseModel):
    message: str
    deleted_old: int
    inserted: int


class QAHistoryItem(BaseModel):
    id: str
    question: str
    answer: str
    sources: Optional[list[dict]] = None
    created_at: str