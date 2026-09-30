from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TokenPayload(BaseModel):
    sub: str
    role: str


from typing import Optional

from app.schemas.user import UserResponse


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Optional[UserResponse] = None


class LoginRequest(BaseModel):
    phone_number: str
    password: str


class RegisterHouseholdRequest(BaseModel):
    household_name: str
    admin_name: str
    phone_number: str = Field(..., min_length=10, max_length=15)
    password: str = Field(..., min_length=6)
