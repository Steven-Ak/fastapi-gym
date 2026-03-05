from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.qa_log_model import QALog


class QALogRepository:

    async def create(
        self,
        db: AsyncSession,
        member_id: UUID,
        question: str,
        answer: str,
        rag_context: list[dict] | None = None,
        log_type: str = "exercise",
    ) -> QALog:
        log = QALog(
            member_id=member_id,
            question=question,
            answer=answer,
            rag_context=rag_context,
            log_type=log_type,
        )
        db.add(log)
        await db.commit()
        await db.refresh(log)
        return log

    async def get_by_member(
        self,
        db: AsyncSession,
        member_id: UUID,
        log_type: str = "exercise",
        limit: int = 20,
    ) -> list[QALog]:
        result = await db.execute(
            select(QALog)
            .where(QALog.member_id == member_id, QALog.log_type == log_type)
            .order_by(QALog.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())