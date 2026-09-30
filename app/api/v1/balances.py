from typing import Any, Dict, List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.core.database import get_db
from app.models.account import Account
from app.schemas import (
    HouseholdBalanceResponse,
    PersonalBalanceResponse,
    AccountResponse,
)
from app.services.balance_service import get_household_cumulative_balance, get_user_cumulative_balance

router = APIRouter(prefix="/balances", tags=["Balances"])


@router.get("/me", response_model=PersonalBalanceResponse)
def personal_balance(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> PersonalBalanceResponse:
    tot = get_user_cumulative_balance(db, current_user.id)
    accounts = db.query(Account).filter(Account.user_id == current_user.id).all()
    return PersonalBalanceResponse(
        user_id=current_user.id,
        total_balance=tot,
        accounts=[AccountResponse.model_validate(a) for a in accounts],
    )


@router.get("/household", response_model=HouseholdBalanceResponse)
def household_balance(
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
) -> HouseholdBalanceResponse:
    return HouseholdBalanceResponse(**get_household_cumulative_balance(db, admin.household_id))
