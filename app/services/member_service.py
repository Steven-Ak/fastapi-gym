from fastapi import HTTPException

from app.repositories import member_repository
from app.services.auth_service import hash_password, verify_password, create_token


async def register(name: str, phone: str, password: str, gym_id: str) -> dict:
    existing = await member_repository.get_by_phone_and_gym(phone=phone, gym_id=gym_id)
    if existing:
        raise HTTPException(status_code=400, detail="Phone already registered in this gym")

    member = await member_repository.create(
        name=name,
        phone=phone,
        password_hash=hash_password(password),
        gym_id=gym_id,
    )

    return {
        "access_token": create_token(member["id"], gym_id),
        "token_type": "bearer",
        "member_id": member["id"],
        "name": name,
    }


async def login(phone: str, password: str) -> dict:
    member = await member_repository.get_by_phone(phone=phone)

    if not member:
        raise HTTPException(status_code=401, detail="Phone number not found")

    if not member.get("is_member_active", False):
        raise HTTPException(status_code=403, detail="Membership is inactive")

    if not verify_password(password, member["password_hash"]):
        raise HTTPException(status_code=401, detail="Incorrect password")

    return {
        "access_token": create_token(member["id"], member["gym_id"]),
        "token_type": "bearer",
        "member_id": member["id"],
        "name": member["name"],
    }