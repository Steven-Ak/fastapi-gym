from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import json
import uuid

from app.database import get_db
from app.dependencies.auth import get_current_member
from app.models.member_model import Member
from app.schemas.nutrition_plan_schema import NutritionAskRequest, NutritionAskResponse
from app.services.nutrition_plan_service import NutritionPlanService
from app.services.vector_document_service import VectorDocumentService

router = APIRouter(tags=["Nutrition Coach"])

vector_service = VectorDocumentService()


def _get_service() -> NutritionPlanService:
    return NutritionPlanService()


@router.post(
    "/nutrition/generate",
    summary="Generate 30-day Arabic nutrition plan from member profile.",
)
async def generate_plan(
    db: AsyncSession = Depends(get_db),
    current: Member = Depends(get_current_member),
    service: NutritionPlanService = Depends(_get_service),
):
    return await service.generate_plan(db, current.id)


@router.get(
    "/members/me/nutrition",
    summary="Retrieve active monthly nutrition plan for logged-in member.",
)
async def get_my_nutrition(
    db: AsyncSession = Depends(get_db),
    current: Member = Depends(get_current_member),
    service: NutritionPlanService = Depends(_get_service),
):
    return await service.get_active_plan(db, current.id)


@router.post(
    "/nutrition/ask",
    response_model=NutritionAskResponse,
    summary="Ask a nutrition follow-up question. RAG answers grounded in your knowledge base.",
)
async def ask_nutrition(
    body: NutritionAskRequest,
    db: AsyncSession = Depends(get_db),
    current: Member = Depends(get_current_member),
    service: NutritionPlanService = Depends(_get_service),
):
    return await service.ask_question(db, current.id, body.question)


@router.post(
    "/nutrition/embed-knowledge",
    summary="Admin: upload nutrition_rag_chunks.json and embed into pgvector.",
)
async def embed_nutrition_knowledge(
    gym_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current: Member = Depends(get_current_member),
):
    content = await file.read()
    try:
        chunks = json.loads(content)["chunks"]
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON — expected nutrition_rag_chunks.json")

    result = await vector_service.embed_knowledge(
        db     = db,
        gym_id = uuid.UUID(gym_id),
        chunks = chunks,
    )
    return {"status": "done ", **result}