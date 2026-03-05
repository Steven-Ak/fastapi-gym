import uuid
from datetime import date, datetime
from typing import Optional
import enum

from sqlalchemy import Date, DateTime, ForeignKey, func, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CheckinStatus(str, enum.Enum):
    done = "done"
    partial = "partial"
    skipped = "skipped"


class Checkin(Base):
    __tablename__ = "checkins"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    member_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("members.id"), nullable=False)
    status: Mapped[CheckinStatus] = mapped_column(Enum(CheckinStatus, name="checkin_status", create_type=False), nullable=False)
    ai_response: Mapped[Optional[str]] = mapped_column(nullable=True)
    checkin_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())