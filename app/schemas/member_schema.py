from pydantic import BaseModel
from uuid import UUID
from typing import Optional


class RegisterRequest(BaseModel):
    name: str
    phone: str
    password: str
    gym_id: UUID


class LoginRequest(BaseModel):
    phone: str
    password: str
    gym_id: UUID


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    member_id: UUID
    name: str