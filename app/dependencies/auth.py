from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import decode_access_token
from app.database import get_db
from app.models.member_model import Member

bearer_scheme = HTTPBearer(auto_error=True)


async def get_current_member(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Member:
    token = credentials.credentials
    payload = decode_access_token(token)

    member_id = payload.get("member_id")
    if not member_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    result = await db.execute(select(Member).where(Member.id == UUID(member_id)))
    member = result.scalar_one_or_none()

    if not member:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Member not found")

    if not member.is_member_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Membership is inactive")

    return member