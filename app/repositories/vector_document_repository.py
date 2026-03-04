"""
VectorDocumentRepository — upsert and similarity search for vector_documents.
All operations are scoped to a gym_id.
"""

from uuid import UUID

from sqlalchemy import delete, select, text, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vector_document_model import VectorDocument


class VectorDocumentRepository:

    async def delete_by_gym_and_type(self, db: AsyncSession, gym_id: UUID, doc_type: str) -> int:
        """Delete all docs for a gym of a given type before re-seeding."""
        result = await db.execute(
            delete(VectorDocument).where(
                VectorDocument.gym_id == gym_id,
                VectorDocument.doc_type == doc_type,
            )
        )
        await db.commit()
        return result.rowcount

    async def bulk_insert(self, db: AsyncSession, docs: list[VectorDocument]) -> int:
        """Insert a batch of VectorDocument objects."""
        db.add_all(docs)
        await db.commit()
        return len(docs)

    async def similarity_search(
        self,
        db: AsyncSession,
        gym_id: UUID,
        embedding: list[float],
        top_k: int = 10,
        doc_type: str = "exercise",
    ) -> list[VectorDocument]:
        """
        Cosine similarity search using pgvector <=> operator.
        Uses parameterized cast to avoid string interpolation issues with async SQLAlchemy.
        """
        vec_str = f"[{','.join(str(x) for x in embedding)}]"

        stmt = text("""
            SELECT id FROM vector_documents
            WHERE gym_id = :gym_id
              AND doc_type = :doc_type
              AND embedding IS NOT NULL
            ORDER BY embedding <=> CAST(:vec AS vector)
            LIMIT :top_k
        """)

        result = await db.execute(stmt, {
            "gym_id": str(gym_id),
            "doc_type": doc_type,
            "vec": vec_str,
            "top_k": top_k,
        })
        ids = [row[0] for row in result.fetchall()]

        if not ids:
            return []

        # Fetch full objects by id to preserve ORM mapping
        docs_result = await db.execute(
            select(VectorDocument).where(VectorDocument.id.in_(ids))
        )
        docs = docs_result.scalars().all()

        # Re-sort to match similarity order
        id_order = {str(id_): i for i, id_ in enumerate(ids)}
        return sorted(docs, key=lambda d: id_order.get(str(d.id), 999))

    async def count_by_gym(self, db: AsyncSession, gym_id: UUID, doc_type: str = "exercise") -> int:
        """Count how many docs exist for a gym."""
        result = await db.execute(
            select(func.count(VectorDocument.id)).where(
                VectorDocument.gym_id == gym_id,
                VectorDocument.doc_type == doc_type,
            )
        )
        return result.scalar_one()