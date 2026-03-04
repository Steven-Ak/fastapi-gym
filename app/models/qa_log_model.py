"""
qa_logs table — records every Exercise Q&A interaction.
Stores the question, retrieved RAG context, and LLM answer.
"""

import uuid
from sqlalchemy import Column, String, Text, JSON, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database import Base


class QALog(Base):
    __tablename__ = "qa_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    member_id = Column(UUID(as_uuid=True), ForeignKey("members.id", ondelete="CASCADE"), nullable=False)

    question = Column(Text, nullable=False)
    rag_context = Column(JSON, nullable=True)   # list of source exercise ids/names used
    answer = Column(Text, nullable=False)
    log_type = Column(String(50), default="exercise")  # "exercise" | "nutrition"

    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())