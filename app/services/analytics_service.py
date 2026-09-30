from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.models.enums import TransactionType
from app.models.transaction import Transaction
from app.schemas.analytics import CategoryBreakdownItem, CategoryBreakdownResponse, MonthlySummaryResponse


def get_month_date_range(
    year: Optional[int] = None,
    month: Optional[int] = None,
) -> tuple[datetime, datetime]:
    now = datetime.utcnow()
    y = year if year is not None else now.year
    m = month if month is not None else now.month

    start = datetime(y, m, 1)
    if m == 12:
        end = datetime(y + 1, 1, 1)
    else:
        end = datetime(y, m + 1, 1)

    return start, end


def get_category_breakdown(
    db: Session,
    user_ids: list[str],
    start_date: datetime,
    end_date: datetime,
) -> CategoryBreakdownResponse:
    total_expenses = (
        db.query(func.coalesce(func.sum(Transaction.amount), 0.0))
        .filter(
            Transaction.user_id.in_(user_ids),
            Transaction.type == TransactionType.EXPENSE,
            Transaction.date >= start_date,
            Transaction.date < end_date,
        )
        .scalar()
        or 0.0
    )

    rows = (
        db.query(
            Transaction.category.label("category"),
            func.coalesce(func.sum(Transaction.amount), 0.0).label("total_amount"),
        )
        .filter(
            Transaction.user_id.in_(user_ids),
            Transaction.type == TransactionType.EXPENSE,
            Transaction.date >= start_date,
            Transaction.date < end_date,
        )
        .group_by(Transaction.category)
        .order_by(func.coalesce(func.sum(Transaction.amount), 0.0).desc())
        .all()
    )

    categories: list[CategoryBreakdownItem] = []
    for r in rows:
        cat_sum = float(r.total_amount or 0.0)
        percentage = round((cat_sum / total_expenses) * 100, 2) if total_expenses > 0 else 0.0
        categories.append(
            CategoryBreakdownItem(
                category=str(r.category),
                total_amount=round(cat_sum, 2),
                percentage=percentage,
            )
        )

    return CategoryBreakdownResponse(total_expenses=float(total_expenses or 0.0), categories=categories)


def get_monthly_summary(
    db: Session,
    user_ids: list[str],
    start_date: datetime,
    end_date: datetime,
) -> MonthlySummaryResponse:
    total_income = (
        db.query(func.coalesce(func.sum(Transaction.amount), 0.0))
        .filter(
            Transaction.user_id.in_(user_ids),
            Transaction.type == TransactionType.INCOME,
            Transaction.date >= start_date,
            Transaction.date < end_date,
        )
        .scalar()
        or 0.0
    )

    total_expense = (
        db.query(func.coalesce(func.sum(Transaction.amount), 0.0))
        .filter(
            Transaction.user_id.in_(user_ids),
            Transaction.type == TransactionType.EXPENSE,
            Transaction.date >= start_date,
            Transaction.date < end_date,
        )
        .scalar()
        or 0.0
    )

    net_savings = round(float(total_income or 0.0) - float(total_expense or 0.0), 2)
    savings_rate_percentage = (
        round((net_savings / float(total_income)) * 100, 2) if float(total_income or 0.0) > 0 else 0.0
    )

    return MonthlySummaryResponse(
        total_income=float(total_income or 0.0),
        total_expense=float(total_expense or 0.0),
        net_savings=net_savings,
        savings_rate_percentage=savings_rate_percentage,
    )
