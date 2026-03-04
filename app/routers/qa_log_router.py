"""
Feature 3 — Exercise Q&A (RAG)
Endpoints:
  POST /exercises/seed      — Upload JSONL for a gym, embed & store (admin)
  POST /exercises/ask       — Member asks an exercise question in Arabic
  GET  /exercises/my-history — Member's Q&A history
"""

from uuid import UUID

from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_member
from app.models.member_model import Member

from app.repositories.vector_document_repository import VectorDocumentRepository
from app.repositories.qa_log_repository import QALogRepository
from app.repositories.member_profile_repository import MemberProfileRepository
from app.client.embedding_client import CohereEmbeddingClient
from app.client.llm_client import GroqLLMClient
from app.services.member_profile_service import MemberProfileService
from app.services.qa_log_service import ExerciseQAService
from app.schemas.qa_log_schema import AskRequest, AskResponse, SeedResponse, QAHistoryItem

router = APIRouter(prefix="/exercises", tags=["Exercise Q&A (RAG)"])


def _get_exercise_qa_service() -> ExerciseQAService:
    return ExerciseQAService(
        vector_repo=VectorDocumentRepository(),
        qa_log_repo=QALogRepository(),
        profile_service=MemberProfileService(repo=MemberProfileRepository()),
        embedding_client=CohereEmbeddingClient(),
        llm_client=GroqLLMClient(),
    )


@router.post(
    "/seed",
    response_model=SeedResponse,
    summary="Upload exercises JSONL for a gym → embed → store. Safe to re-run on updates.",
)
async def seed_exercises(
    gym_id: UUID = Form(..., description="The gym this exercise library belongs to"),
    file: UploadFile = File(..., description="exercises.jsonl file"),
    db: AsyncSession = Depends(get_db),
    service: ExerciseQAService = Depends(_get_exercise_qa_service),
):
    content = await file.read()
    jsonl_text = content.decode("utf-8")
    return await service.seed_exercises(db, gym_id=gym_id, jsonl_content=jsonl_text)


@router.post(
    "/ask",
    response_model=AskResponse,
    summary="Ask an exercise question in Arabic. RAG retrieves from your gym's exercise library.",
)
async def ask_exercise(
    body: AskRequest,
    db: AsyncSession = Depends(get_db),
    current: Member = Depends(get_current_member),
    service: ExerciseQAService = Depends(_get_exercise_qa_service),
):
    # gym_id comes from the authenticated member — no need to pass it manually
    return await service.ask(db, member_id=current.id, gym_id=current.gym_id, question=body.question, top_k=body.top_k)


@router.get(
    "/my-history",
    response_model=list[QAHistoryItem],
    summary="Get my exercise Q&A history (last 20 questions).",
)
async def get_my_history(
    db: AsyncSession = Depends(get_db),
    current: Member = Depends(get_current_member),
    service: ExerciseQAService = Depends(_get_exercise_qa_service),
):
    return await service.get_history(db, current.id)

@router.get(
    "/history/{member_id}",
    response_model=list[QAHistoryItem],
    summary="Get exercise Q&A history for a specific member by ID.",
)
async def get_member_history(
    member_id: UUID,
    db: AsyncSession = Depends(get_db),
    current: Member = Depends(get_current_member),
    service: ExerciseQAService = Depends(_get_exercise_qa_service),
):
    return await service.get_history(db, member_id)