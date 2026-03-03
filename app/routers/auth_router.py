from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.member_schema import RegisterRequest, LoginRequest, AuthResponse
from app.repositories.member_repository import MemberRepository
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])

auth_service = AuthService(MemberRepository())


@router.post("/register", response_model=AuthResponse)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    return await auth_service.register(db, body.name, body.phone, body.password, body.gym_id)


@router.post("/login", response_model=AuthResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    return await auth_service.login(db, body.phone, body.password, body.gym_id)