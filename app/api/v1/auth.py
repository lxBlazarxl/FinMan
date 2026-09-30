from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_password_hash, verify_password, create_access_token
from app.models.enums import AccountType, UserRole
from app.models.account import Account
from app.models.household import Household
from app.models.user import User
from app.schemas import (
    LoginRequest,
    RegisterHouseholdRequest,
    Token,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register-household", response_model=Token)
def register_household(
    payload: RegisterHouseholdRequest,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    existing_admin = db.query(User).filter(User.phone_number == payload.phone_number).first()
    if existing_admin:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Phone number already taken")

    household = Household(name=payload.household_name)
    db.add(household)
    db.flush()

    user = User(
        household_id=household.id,
        name=payload.admin_name,
        phone_number=payload.phone_number,
        password_hash=get_password_hash(payload.password),
        role=UserRole.ADMIN,
    )
    db.add(user)
    db.flush()

    db.add(
        Account(
            user_id=user.id,
            name="Cash Wallet",
            type=AccountType.CASH,
            current_balance=0.0,
        )
    )

    db.commit()
    token = create_access_token({"sub": user.id, "role": user.role.value})
    return {"access_token": token, "token_type": "bearer", "user": UserResponse.model_validate(user)}


@router.post("/login", response_model=Token)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    user = db.query(User).filter(User.phone_number == payload.phone_number).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token({"sub": user.id, "role": user.role.value})
    return {"access_token": token, "token_type": "bearer", "user": UserResponse.model_validate(user)}
