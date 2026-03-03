import uuid
from sqlalchemy import Column, String, Integer, Float, TIMESTAMP, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database import Base


class MemberProfile(Base):
    __tablename__ = "member_profiles"
    __table_args__ = (
        UniqueConstraint("member_id", name="uq_member_profiles_member_id"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    member_id = Column(UUID(as_uuid=True), ForeignKey("members.id", ondelete="CASCADE"), nullable=False)

    goal = Column(String, nullable=True)
    weight_kg = Column(Float, nullable=True)
    height_cm = Column(Float, nullable=True)
    days_per_week = Column(Integer, nullable=True)
    level = Column(String, nullable=True)
    injuries = Column(String, nullable=True)
    diseases = Column(String, nullable=True)
    allergies = Column(String, nullable=True)

    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)