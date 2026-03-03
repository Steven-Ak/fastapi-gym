import uuid
from sqlalchemy import Column, Integer, Boolean, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func

from app.database import Base


class WorkoutPlan(Base):
    __tablename__ = "workout_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    member_id = Column(UUID(as_uuid=True), ForeignKey("members.id", ondelete="CASCADE"), nullable=False)

    plan_json = Column(JSONB, nullable=False)
    week_number = Column(Integer, default=1, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    adapted_from_id = Column(UUID(as_uuid=True), nullable=True)
    generated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)