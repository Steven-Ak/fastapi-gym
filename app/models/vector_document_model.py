"""
vector_documents table — stores exercise embeddings for RAG.
Scoped to a gym — every doc belongs to a gym, no member linkage.
"""

import uuid
from sqlalchemy import Column, String, Text, JSON, TIMESTAMP, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector

from app.database import Base
from app.client.embedding_client import EMBED_DIMENSION


class VectorDocument(Base):
    __tablename__ = "vector_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    gym_id = Column(UUID(as_uuid=True), ForeignKey("gyms.id", ondelete="CASCADE"), nullable=False)

    doc_type = Column(String(50), nullable=False)        
    source_id = Column(String(100), nullable=True)       
    content = Column(Text, nullable=False)               
    metadata_ = Column("metadata", JSON, nullable=True) 
    embedding = Column(Vector(EMBED_DIMENSION), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    __table_args__ = (
        # IVFFlat index for fast cosine similarity search
        Index(
            "ix_vector_documents_embedding",
            "embedding",
            postgresql_using="ivfflat",
            postgresql_with={"lists": 50},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )