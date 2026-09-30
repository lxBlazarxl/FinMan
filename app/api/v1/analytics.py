from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.services.analytics_service import (
    get_category_breakdown,
    get_month_date_range,
    get_monthly_summary,
)

from app.schemas.analytics import (
    CategoryBreakdownResponse,
    MonthlySummaryResponse,
)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


def _get_target_user_ids(
    *,
    db: Session,
    current_user: User,
    scope: str,
) -> list[str]:
    if scope == "household":
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Admin access required for household scope")
        ids = db.query(User.id).filter(User.household_id == current_user.household_id).all()
        return [i[0] for i in ids]

    if scope == "personal":
        return [current_user.id]

    raise HTTPException(status_code=400, detail="Invalid scope")


@router.get("/category-breakdown", response_model=CategoryBreakdownResponse)
def category_breakdown(
    year: Optional[int] = None,
    month: Optional[int] = None,
    scope: str = Query(default="personal"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CategoryBreakdownResponse:
    start_date, end_date = get_month_date_range(year=year, month=month)
    target_user_ids = _get_target_user_ids(db=db, current_user=current_user, scope=scope)
    return get_category_breakdown(db, target_user_ids, start_date, end_date)


@router.get("/monthly-summary", response_model=MonthlySummaryResponse)
def monthly_summary(
    year: Optional[int] = None,
    month: Optional[int] = None,
    scope: str = Query(default="personal"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MonthlySummaryResponse:
    start_date, end_date = get_month_date_range(year=year, month=month)
    target_user_ids = _get_target_user_ids(db=db, current_user=current_user, scope=scope)
    return get_monthly_summary(db, target_user_ids, start_date, end_date)
