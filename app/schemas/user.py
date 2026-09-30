from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import UserRole


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    household_id: str
    name: str
    phone_number: str
    role: UserRole
    created_at: datetime


class MemberCreateRequest(BaseModel):
    name: str
    phone_number: str = Field(..., min_length=10, max_length=15)
    password: str = Field(..., min_length=6)
    initial_account_name: Optional[str] = "Pocket Cash"
