from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.account import Account
from app.models.transaction import Transaction
from app.schemas.sms import SMSParseRequest, SMSParseResult
from app.schemas.transaction import TransactionCreate, TransactionResponse
from app.services.balance_service import apply_transaction_balance, revert_transaction_balance
from app.services.sms_parser import parse_bank_sms

from app.models.enums import UserRole

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.post("/parse-sms", response_model=SMSParseResult)
def parse_sms(payload: SMSParseRequest) -> SMSParseResult:
    return parse_bank_sms(payload.sms_text)


@router.post("/", response_model=TransactionResponse)
def create_transaction(
    payload: TransactionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> TransactionResponse:
    account = db.query(Account).filter(Account.id == payload.account_id).first()
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

    if current_user.role != UserRole.ADMIN and account.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    apply_transaction_balance(db, account, payload.type, payload.amount)

    tx = Transaction(
        account_id=account.id,
        user_id=current_user.id,
        amount=payload.amount,
        type=payload.type,
        category=payload.category,
        description=payload.description,
        raw_sms=payload.raw_sms,
        date=payload.date,
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return TransactionResponse.model_validate(tx)


@router.delete("/{id}")
def delete_transaction(
    id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    tx = db.query(Transaction).filter(Transaction.id == id).first()
    if not tx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")

    if current_user.role != UserRole.ADMIN and tx.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    account = db.query(Account).filter(Account.id == tx.account_id).first()
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

    revert_transaction_balance(db, account, tx.type, tx.amount)
    db.delete(tx)
    db.commit()
    return {"detail": "Transaction deleted successfully"}
