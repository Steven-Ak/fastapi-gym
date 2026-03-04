import json
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile, HTTPException

from app.client.embedding_client import CohereEmbeddingClient
from app.repositories.vector_document_repository import VectorDocumentRepository

BATCH_SIZE = 10


class VectorDocumentService:

    def __init__(self):
        self.repo     = VectorDocumentRepository()
        self.embedder = CohereEmbeddingClient()


    async def embed_knowledge(
        self,
        db: AsyncSession,
        gym_id: uuid.UUID,
        file: UploadFile,
        doc_type_prefix: str = "nutrition",  
    ) -> dict:
        #  Parse uploaded file
        content = await file.read()
        try:
            data   = json.loads(content)
            chunks = data["chunks"]
        except Exception:
            raise HTTPException(
                status_code=400,
                detail="Invalid JSON — expected nutrition_rag_chunks.json"
            )

        inserted = 0
        skipped  = 0

        #  Embed in batches and insert
        for i in range(0, len(chunks), BATCH_SIZE):
            batch      = chunks[i : i + BATCH_SIZE]
            texts      = [c["embed_text"] for c in batch]
            embeddings = await self.embedder.embed_documents(texts)

            for c, emb in zip(batch, embeddings):
                source_id = f"{doc_type_prefix}_{c['topic']}"

                exists = await self.repo.chunk_exists(db, gym_id, source_id)
                if exists:
                    skipped += 1
                    continue

                await self.repo.insert_chunk(
                    db        = db,
                    gym_id    = gym_id,
                    doc_type  = f"{doc_type_prefix}_{c['doc_type']}",
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

        return {
            "status"  : "done ",
            "inserted": inserted,
            "skipped" : skipped,
            "total"   : len(chunks),
        }


    async def search(
        self,
        db: AsyncSession,
        gym_id: uuid.UUID,
        query: str,
        doc_type_prefix: str = "nutrition",
        top_k: int = 5,
    ) -> list[dict]:
        query_embedding = await self.embedder.embed_query(query)
        return await self.repo.search_similar(
            db              = db,
            gym_id          = gym_id,
            query_embedding = query_embedding,
            doc_type_prefix = doc_type_prefix,
            top_k           = top_k,
        )