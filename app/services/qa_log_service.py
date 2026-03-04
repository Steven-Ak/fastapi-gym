"""
ExerciseQAService — Feature 3 core logic.

Seed flow:
  1. Parse JSONL file upload
  2. Delete existing gym exercise docs (clean re-seed)
  3. Embed all rag_text fields via Cohere in batches
  4. Bulk insert into vector_documents scoped to gym_id

Ask flow:
  1. Embed member's question (search_query input type)
  2. Cosine similarity search scoped to member's gym_id
  3. Filter out exercises that conflict with member's injuries AND diseases
  4. Build Arabic prompt with retrieved context
  5. Call Groq LLM → Arabic answer
  6. Log to qa_logs
  7. Return answer + source exercises
"""

import json
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.client.embedding_client import CohereEmbeddingClient
from app.client.llm_client import GroqLLMClient
from app.core.exceptions import ExternalServiceError, ValidationError
from app.models.vector_document_model import VectorDocument
from app.repositories.vector_document_repository import VectorDocumentRepository
from app.repositories.qa_log_repository import QALogRepository
from app.services.member_profile_service import MemberProfileService

EMBED_BATCH_SIZE = 90


class ExerciseQAService:
    def __init__(
        self,
        vector_repo: VectorDocumentRepository,
        qa_log_repo: QALogRepository,
        profile_service: MemberProfileService,
        embedding_client: CohereEmbeddingClient,
        llm_client: GroqLLMClient,
    ):
        self.vector_repo = vector_repo
        self.qa_log_repo = qa_log_repo
        self.profile_service = profile_service
        self.embedding_client = embedding_client
        self.llm_client = llm_client

    # Seed

    async def seed_exercises(self, db: AsyncSession, gym_id: UUID, jsonl_content: str) -> dict:
        """
        Parse JSONL, embed all exercises, wipe old gym docs, insert new ones.
        Idempotent — safe to call multiple times as the file is updated.
        """
        lines = [l.strip() for l in jsonl_content.strip().splitlines() if l.strip()]
        if not lines:
            raise ValidationError(detail="Uploaded file is empty or invalid.")

        exercises = []
        for i, line in enumerate(lines):
            try:
                exercises.append(json.loads(line))
            except json.JSONDecodeError:
                raise ValidationError(detail=f"Invalid JSON on line {i + 1}")

        # Step 1: Dynamically generate Arabic keywords via LLM in batches
        # This makes search work for ANY Arabic query — no hardcoded maps needed
        LLM_BATCH_SIZE = 20  # Keep batches small for reliable JSON output
        all_arabic_keywords: list[str] = []
        for i in range(0, len(exercises), LLM_BATCH_SIZE):
            batch = exercises[i: i + LLM_BATCH_SIZE]
            keywords = await self.llm_client.generate_arabic_keywords(batch)
            all_arabic_keywords.extend(keywords)

        # Step 2: Build final bilingual embed text per exercise
        def _build_embed_text(ex: dict, arabic_keywords: str) -> str:
            parts = []
            if ex.get("name_ar"):
                parts.append(f"الاسم بالعربي: {ex['name_ar']}")
            if arabic_keywords:
                parts.append(f"الكلمات المفتاحية بالعربي: {arabic_keywords}")
            if ex.get("target_muscle"):
                parts.append(f"العضلات المستهدفة: {', '.join(ex['target_muscle'])}")
            if ex.get("secondary_muscles"):
                parts.append(f"العضلات الثانوية: {', '.join(ex['secondary_muscles'])}")
            parts.append(ex.get("rag_text") or ex.get("name", ""))
            return "\n".join(parts)

        rag_texts = [
            _build_embed_text(ex, kw)
            for ex, kw in zip(exercises, all_arabic_keywords)
        ]

        # Embed in batches
        all_embeddings: list[list[float]] = []
        for i in range(0, len(rag_texts), EMBED_BATCH_SIZE):
            batch = rag_texts[i: i + EMBED_BATCH_SIZE]
            embeddings = await self.embedding_client.embed_documents(batch)
            all_embeddings.extend(embeddings)

        # Wipe old docs for this gym
        deleted = await self.vector_repo.delete_by_gym_and_type(db, gym_id, "exercise")

        # Build VectorDocument objects
        docs = []
        for ex, embedding in zip(exercises, all_embeddings):
            docs.append(
                VectorDocument(
                    gym_id=gym_id,
                    doc_type="exercise",
                    source_id=ex.get("exercise_id"),
                    content=ex.get("rag_text", ex.get("name", "")),
                    metadata_=ex,
                    embedding=embedding,
                )
            )

        inserted = await self.vector_repo.bulk_insert(db, docs)

        return {
            "message": "تم رفع ومعالجة التمارين بنجاح",
            "deleted_old": deleted,
            "inserted": inserted,
        }

    # ASK

    async def ask(
        self,
        db: AsyncSession,
        member_id: UUID,
        gym_id: UUID,
        question: str,
        top_k: int = 10,
    ) -> dict:
        """
        Full RAG pipeline: embed question → retrieve (gym-scoped) → filter → LLM → log → return.
        """
        # 1. Get member profile for injury & disease-aware filtering
        profile = await self.profile_service.get_profile(db, member_id)

        member_injuries: list[str] = []
        if profile and profile.injuries:
            member_injuries = [i.strip().lower() for i in profile.injuries.split(",")]

        member_diseases: list[str] = []
        if profile and profile.diseases:
            member_diseases = [d.strip().lower() for d in profile.diseases.split(",")]

        # Combined conditions to check against contraindications
        member_conditions = member_injuries + member_diseases

        # 2. Embed the question
        query_embedding = await self.embedding_client.embed_query(question)

        # 3. Retrieve top-K similar exercises scoped to this gym
        # DEBUG: verify gym has seeded docs before similarity search
        total_docs = await self.vector_repo.count_by_gym(db, gym_id, doc_type="exercise")
        if total_docs == 0:
            return {
                "answer": "لم يتم رفع قاعدة بيانات التمارين لهذا الصالة بعد. يرجى استخدام POST /exercises/seed أولاً.",
                "sources": [],
                "debug": {"gym_id": str(gym_id), "total_docs": 0},
            }

        docs = await self.vector_repo.similarity_search(
            db, gym_id=gym_id, embedding=query_embedding, top_k=top_k, doc_type="exercise"
        )

        if not docs:
            return {
                "answer": "عذراً، لم أجد تمارين مرتبطة بسؤالك. حاول إعادة الصياغة.",
                "sources": [],
                "debug": {"gym_id": str(gym_id), "total_docs": total_docs, "retrieved": 0},
            }

        # 4. Filter out exercises that conflict with member injuries OR diseases
        safe_docs = []
        flagged_reasons: list[str] = []
        for doc in docs:
            meta = doc.metadata_ or {}
            contraindications_str = " ".join(c.lower() for c in meta.get("contraindications", []))
            matched = [c for c in member_conditions if c in contraindications_str]
            if matched:
                flagged_reasons.extend(matched)
            else:
                safe_docs.append(doc)

        # Fallback: if all filtered out, keep originals but warn the member
        use_docs = safe_docs if safe_docs else docs
        if not safe_docs and flagged_reasons:
            unique_reasons = ", ".join(sorted(set(flagged_reasons)))
            safety_warning = (
                f"\n\n⚠️ تنبيه: التمارين المقترحة قد لا تناسبك بسبب: {unique_reasons}. "
                "يُرجى استشارة مختص قبل ممارستها."
            )
        elif flagged_reasons:
            safety_warning = "\n\n✅ تم استبعاد بعض التمارين التي قد تتعارض مع وضعك الصحي."
        else:
            safety_warning = ""

        # 5. Build context string for the prompt
        context_parts = []
        sources = []
        for doc in use_docs:
            meta = doc.metadata_ or {}
            context_parts.append(doc.content)
            sources.append({
                "exercise_id": meta.get("exercise_id"),
                "name": meta.get("name"),
                "name_ar": meta.get("name_ar"),
                "level": meta.get("level"),
                "equipment": meta.get("equipment", []),
                "video_urls": meta.get("video_urls", []),
            })

        context_text = "\n\n---\n\n".join(context_parts)

        # 6. Call LLM with full health context
        answer_raw = await self.llm_client.answer_exercise_question(
            question=question,
            context=context_text,
            injuries=profile.injuries if profile else None,
            diseases=profile.diseases if profile else None,
        )
        answer = answer_raw + safety_warning

        # 7. Log the interaction
        await self.qa_log_repo.create(
            db,
            member_id=member_id,
            question=question,
            answer=answer,
            rag_context=sources,
            log_type="exercise",
        )

        return {
            "answer": answer,
            "sources": sources,
        }
    # History

    async def get_history(self, db: AsyncSession, member_id: UUID) -> list[dict]:
        logs = await self.qa_log_repo.get_by_member(db, member_id, log_type="exercise")
        return [
            {
                "id": str(log.id),
                "question": log.question,
                "answer": log.answer,
                "sources": log.rag_context,
                "created_at": str(log.created_at),
            }
            for log in logs
        ]