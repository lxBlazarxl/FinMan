from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_password_hash
from app.api.deps import require_admin
from app.models.account import Account
from app.models.enums import AccountType, UserRole
from app.models.user import User
from app.schemas import MemberCreateRequest, UserResponse

router = APIRouter(prefix="/household", tags=["Household"])


@router.post("/members", response_model=UserResponse)
def create_member(
    payload: MemberCreateRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
) -> Dict[str, Any]:
    existing = db.query(User).filter(User.phone_number == payload.phone_number).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Phone number already taken")

    with db.begin():
        user = User(
            household_id=current_admin.household_id,
            name=payload.name,
            phone_number=payload.phone_number,
            password_hash=get_password_hash(payload.password),
            role=UserRole.MEMBER,
        )
        db.add(user)
        db.flush()

        db.add(
            Account(
                user_id=user.id,
                name=payload.initial_account_name or "Pocket Cash",
                type=AccountType.CASH,
                current_balance=0.0,
            )
        )

    return UserResponse.model_validate(user)


@router.get("/members", response_model=list[UserResponse])
def list_members(
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
) -> list[UserResponse]:
    members = db.query(User).filter(User.household_id == current_admin.household_id).all()
    return [UserResponse.model_validate(m) for m in members]
