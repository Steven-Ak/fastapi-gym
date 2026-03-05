from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.core.exceptions import AuthenticationError, AuthorizationError
from app.database import get_db
from app.repositories.member_repository import MemberRepository

bearer_scheme = HTTPBearer(auto_error=True)


def _get_member_repo() -> MemberRepository:
    return MemberRepository()


async def get_current_member(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
    member_repo: MemberRepository = Depends(_get_member_repo),
):
    token = credentials.credentials
    payload = decode_access_token(token)

    member_id = payload.get("member_id")
    if not member_id:
        raise AuthenticationError(detail="Invalid token payload")

    member = await member_repo.get_by_id(db, UUID(member_id))

    if not member:
        raise AuthenticationError(detail="Member not found")

    if not member.is_member_active:
        raise AuthorizationError(detail="Membership is inactive")

    return member