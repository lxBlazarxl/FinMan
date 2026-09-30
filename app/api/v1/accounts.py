from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.account import Account
from app.schemas import AccountCreate, AccountResponse, PersonalBalanceResponse, UserResponse
from app.services.balance_service import get_user_cumulative_balance

router = APIRouter(prefix="/accounts", tags=["Accounts"])


@router.post("/", response_model=AccountResponse)
def create_account(
    payload: AccountCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> Dict[str, Any]:
    account = Account(
        user_id=current_user.id,
        name=payload.name,
        type=payload.type,
        current_balance=payload.initial_balance,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return AccountResponse.model_validate(account)


@router.get("/", response_model=List[AccountResponse])
def list_accounts(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> List[AccountResponse]:
    accounts = db.query(Account).filter(Account.user_id == current_user.id).all()
    return [AccountResponse.model_validate(a) for a in accounts]


@router.get("/{account_id}", response_model=AccountResponse)
def get_account(
    account_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> AccountResponse:
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    if account.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    return AccountResponse.model_validate(account)
