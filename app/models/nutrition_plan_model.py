import uuid
from sqlalchemy import Column, Integer, Boolean, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class NutritionPlan(Base):
    __tablename__ = "nutrition_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    member_id = Column(UUID(as_uuid=True), ForeignKey("members.id", ondelete="CASCADE"), nullable=False)

    meal_plan_json = Column(JSONB, nullable=False)
    calorie_target = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    generated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    # Relationship
    member = relationship("Member", lazy="selectin")