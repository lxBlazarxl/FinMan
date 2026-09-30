from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class CategoryBreakdownItem(BaseModel):
    category: str
    total_amount: float
    percentage: float


class CategoryBreakdownResponse(BaseModel):
    total_expenses: float
    categories: list[CategoryBreakdownItem]


class MonthlySummaryResponse(BaseModel):
    total_income: float
    total_expense: float
    net_savings: float
    savings_rate_percentage: float
