from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.security import hash_password, verify_password, create_access_token
from app.core.exceptions import AlreadyExistsError, AuthenticationError, AuthorizationError
from app.models.member_model import Member
from app.repositories.base import MemberRepositoryProtocol


class AuthService:
    def __init__(self, repo: MemberRepositoryProtocol):
        self.repo = repo

    async def register(self, db: AsyncSession, name: str, phone: str, password: str, gym_id: UUID) -> dict:
        existing = await self.repo.get_by_phone_and_gym(db, phone, gym_id)
        if existing:
            raise AlreadyExistsError(detail="Phone already registered in this gym")

        member = Member(
            name=name,
            phone=phone,
            gym_id=gym_id,
            password_hash=hash_password(password),
            language="ar",
            current_step=None,
            is_member_active=True,
        )
        member = await self.repo.create(db, member)

        token = create_access_token({"member_id": str(member.id), "gym_id": str(member.gym_id)})
        return {
            "access_token": token,
            "token_type": "bearer",
            "member_id": member.id,
            "name": member.name,
        }

    async def login(self, db: AsyncSession, phone: str, password: str, gym_id: UUID) -> dict:
        member = await self.repo.get_by_phone_and_gym(db, phone, gym_id)
        if not member:
            raise AuthenticationError(detail="Phone number not found")

        if not member.is_member_active:
            raise AuthorizationError(detail="Membership is inactive")

        if not verify_password(password, member.password_hash):
            raise AuthenticationError(detail="Incorrect password")

        token = create_access_token({"member_id": str(member.id), "gym_id": str(member.gym_id)})
        return {
            "access_token": token,
            "token_type": "bearer",
            "member_id": member.id,
            "name": member.name,
        }