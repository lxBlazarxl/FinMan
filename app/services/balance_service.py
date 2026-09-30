from __future__ import annotations

from typing import Dict, List

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.enums import TransactionType


def apply_transaction_balance(
    db: Session,
    account: Account,
    tx_type: TransactionType,
    amount: float,
):
    if tx_type == TransactionType.EXPENSE:
        account.current_balance -= amount
    elif tx_type == TransactionType.INCOME:
        account.current_balance += amount

    account.current_balance = round(account.current_balance, 2)


def revert_transaction_balance(
    db: Session,
    account: Account,
    tx_type: TransactionType,
    amount: float,
):
    if tx_type == TransactionType.EXPENSE:
        account.current_balance += amount
    elif tx_type == TransactionType.INCOME:
        account.current_balance -= amount

    account.current_balance = round(account.current_balance, 2)


def get_user_cumulative_balance(db: Session, user_id: str) -> float:
    total = db.execute(
        select(func.coalesce(func.sum(Account.current_balance), 0.0)).where(
            Account.user_id == user_id
        )
    ).scalar_one()
    return round(float(total), 2)


def get_household_cumulative_balance(db: Session, household_id: str) -> Dict:
    from app.models.user import User

    users = db.execute(
        select(User).where(User.household_id == household_id)
    ).scalars().all()

    members: List[Dict] = []
    household_total = 0.0

    for user in users:
        user_total = get_user_cumulative_balance(db, user.id)
        user_accounts_count = db.execute(
            select(func.count()).select_from(Account).where(Account.user_id == user.id)
        ).scalar_one()
        household_total += user_total
        members.append(
            {
                "user_id": user.id,
                "user_name": user.name,
                "total_balance": user_total,
                "accounts_count": int(user_accounts_count),
            }
        )

    return {
        "household_id": household_id,
        "total_household_balance": round(float(household_total), 2),
        "members": members,
    }
