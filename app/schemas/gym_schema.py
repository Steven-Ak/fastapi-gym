from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional


class GymBase(BaseModel):
    name: str
    address: Optional[str] = None
    contact_number: Optional[str] = None
    working_hours: Optional[str] = None
    pricing: Optional[str] = None


class GymCreate(GymBase):
    pass


class GymResponse(GymBase):
    id: UUID
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True