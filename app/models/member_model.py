import uuid
from sqlalchemy import Column, String, Boolean, TIMESTAMP, ForeignKey, UniqueConstraint, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Member(Base):
    __tablename__ = "members"
    __table_args__ = (
        UniqueConstraint("gym_id", "phone", name="uq_members_gym_phone"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    gym_id = Column(UUID(as_uuid=True), ForeignKey("gyms.id", ondelete="CASCADE"), nullable=False)

    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    password_hash = Column(Text, nullable=False)

    language = Column(String, default="ar")
    current_step = Column(String, nullable=True)

    is_member_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    gym = relationship("Gym", back_populates="members", lazy="selectin")
    profile = relationship("MemberProfile", back_populates="member", uselist=False, lazy="selectin")
    workout_plans = relationship("WorkoutPlan", back_populates="member", lazy="selectin")