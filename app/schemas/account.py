from datetime import datetime
from typing import List

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import AccountType


class AccountCreate(BaseModel):
    name: str
    type: AccountType = AccountType.BANK
    initial_balance: float = Field(0.0, ge=0)


class AccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    name: str
    type: AccountType
    current_balance: float
    created_at: datetime


class PersonalBalanceResponse(BaseModel):
    user_id: str
    total_balance: float
    accounts: List[AccountResponse]


class HouseholdMemberBalance(BaseModel):
    user_id: str
    user_name: str
    total_balance: float
    accounts_count: int


class HouseholdBalanceResponse(BaseModel):
    household_id: str
    total_household_balance: float
    members: List[HouseholdMemberBalance]
