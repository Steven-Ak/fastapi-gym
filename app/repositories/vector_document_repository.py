from uuid import UUID
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, delete, func
from app.models.vector_document_model import VectorDocument
from app.client.embedding_client import CohereEmbeddingClient


class VectorDocumentRepository:

    async def insert_chunk(
        self,
        db: AsyncSession,
        gym_id: uuid.UUID,
        doc_type: str,
        source_id: str,
        content: str,
        metadata: dict,
        embedding: list[float],
    ) -> VectorDocument:
        doc = VectorDocument(
            gym_id    = gym_id,
            doc_type  = doc_type,
            source_id = source_id,
            content   = content,
            metadata_ = metadata,
            embedding = embedding,
        )
        db.add(doc)
        await db.flush()
        return doc

    async def chunk_exists(
        self,
        db: AsyncSession,
        gym_id: uuid.UUID,
        source_id: str,
    ) -> bool:
        result = await db.execute(
            select(VectorDocument.id).where(
                VectorDocument.gym_id    == gym_id,
                VectorDocument.source_id == source_id,
            )
        )
        return result.scalar() is not None

    async def search_similar(
        self,
        db: AsyncSession,
        gym_id: uuid.UUID,
        query_embedding: list[float],
        doc_type_prefix: str | None = None,
        top_k: int = 5,
    ) -> list[dict]:
        where = "gym_id = :gym_id"
        params: dict = {
            "gym_id"   : str(gym_id),
            "embedding": str(query_embedding),
            "top_k"    : top_k,
        }

        if doc_type_prefix:
            where += " AND doc_type LIKE :doc_type_prefix"
            params["doc_type_prefix"] = f"{doc_type_prefix}%"

        stmt = text(f"""
            SELECT id, content, metadata, doc_type, source_id,
                   1 - (embedding <=> :embedding::vector) AS similarity
            FROM vector_documents
            WHERE {where}
            ORDER BY embedding <=> :embedding::vector
            LIMIT :top_k
        """)

        result = await db.execute(stmt, params)
        rows   = result.fetchall()

        return [
            {
                "id"        : str(row.id),
                "content"   : row.content,
                "metadata"  : row.metadata,
                "doc_type"  : row.doc_type,
                "source_id" : row.source_id,
                "similarity": round(float(row.similarity), 4),
            }
            for row in rows
        ]

    async def delete_by_gym_and_type(
        self,
        db: AsyncSession,
        gym_id: uuid.UUID,
        doc_type_prefix: str,
    ) -> int:
        result = await db.execute(
            text("""
                DELETE FROM vector_documents
                WHERE gym_id = :gym_id AND doc_type LIKE :prefix
            """),
            {"gym_id": str(gym_id), "prefix": f"{doc_type_prefix}%"}
        )
        return result.rowcount

    async def embed_nutrition_chunks(
        self,
        db: AsyncSession,
        gym_id: uuid.UUID,
        chunks: list[dict],
        embedder: CohereEmbeddingClient,
        batch_size: int = 10,
    ) -> dict:
        inserted = 0
        skipped  = 0

        for i in range(0, len(chunks), batch_size):
            batch      = chunks[i : i + batch_size]
            texts      = [c["embed_text"] for c in batch]
            embeddings = await embedder.embed_documents(texts)

            for c, emb in zip(batch, embeddings):
                source_id = f"nutrition_{c['topic']}"

                exists = await self.chunk_exists(db, gym_id, source_id)
                if exists:
                    skipped += 1
                    continue

                await self.insert_chunk(
                    db        = db,
                    gym_id    = gym_id,
                    doc_type  = "nutrition",
                    source_id = source_id,
                    content   = c["embed_text"],
                    metadata  = {
                        "tags"   : c.get("tags", []),
                        "text_ar": c.get("text_ar"),
                        "text_en": c.get("text_en"),
                        "topic"  : c.get("topic"),
                    },
                    embedding = emb,
                )
                inserted += 1

        await db.commit()
        return {"inserted": inserted, "skipped": skipped, "total": len(chunks)}
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
