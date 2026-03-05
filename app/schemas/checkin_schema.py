from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional
from uuid import UUID
from enum import Enum


class CheckinStatus(str, Enum):
    done = "done"
    skipped = "skipped"
    partial = "partial"


class CheckinCreateRequest(BaseModel):
    member_id: UUID = Field(..., description="Member ID — simulates QR code scan")
    status: CheckinStatus = Field(..., description="Session completion status")

    class Config:
        json_schema_extra = {
            "example": {
                "member_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "done"
            }
        }


class CheckinResponse(BaseModel):
    id: UUID
    member_id: UUID
    status: CheckinStatus
    ai_response: Optional[str] = None
    checkin_date: date
    created_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "660e8400-e29b-41d4-a716-446655440000",
                "member_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "done",
                "ai_response": "string",
                "checkin_date": "2025-03-04",
                "created_at": "2025-03-04T10:30:00"
            }
        }


class CheckinListResponse(BaseModel):
    checkins: list[CheckinResponse]
    total: int

    class Config:
        json_schema_extra = {
            "example": {
                "checkins": [],
                "total": 0
            }
        }