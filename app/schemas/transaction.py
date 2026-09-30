from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import TransactionType


class TransactionCreate(BaseModel):
    account_id: str
    amount: float = Field(..., gt=0)
    type: TransactionType
    category: str
    description: Optional[str] = None
    date: Optional[datetime] = None
    raw_sms: Optional[str] = None


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    account_id: str
    user_id: str
    amount: float
    type: TransactionType
    category: str
    description: Optional[str]
    date: datetime
    raw_sms: Optional[str]
    created_at: datetime
