from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import TransactionType


class ConfidenceLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class SMSParseRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sms_text: str = Field(..., min_length=5, max_length=1000)


class SMSParseResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    amount: Optional[float] = None
    type: Optional[TransactionType] = None
    merchant: Optional[str] = None
    detected_balance: Optional[float] = None
    suggested_category: Optional[str] = "Miscellaneous"
    bank_name: Optional[str] = None
    confidence: ConfidenceLevel = ConfidenceLevel.LOW
