from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.models.expense import Expense
from app.models.expense_share import ExpenseShare
from app.schemas.expense import (
    ExpenseCreateRequest,
    ExpenseResponse,
)

router = APIRouter(tags=["Expenses"])


async def _attach_shares(db: AsyncSession, expenses: list[Expense]) -> list[dict]:
    """Fetch shares for a list of expenses and return dicts with shares attached."""
    if not expenses:
        return []

    expense_ids = [e.id for e in expenses]
    shares_result = await db.execute(
        select(ExpenseShare).where(ExpenseShare.expense_id.in_(expense_ids))
    )
    all_shares = shares_result.scalars().all()

    # Group shares by expense_id
    shares_by_expense: dict[uuid.UUID, list] = {}
    for s in all_shares:
        shares_by_expense.setdefault(s.expense_id, []).append(s)

    result = []
    for e in expenses:
        result.append({
            "id": e.id,
            "group_id": e.group_id,
            "payer_id": e.payer_id,
            "description": e.description,
            "amount": e.amount,
            "category": e.category,
            "date": e.date,
            "created_at": e.created_at,
            "shares": [
                {
                    "id": s.id,
                    "debtor_id": s.debtor_id,
                    "creditor_id": s.creditor_id,
                    "amount_owed": s.amount_owed,
                    "percentage": s.percentage,
                    "status": s.status,
                }
                for s in shares_by_expense.get(e.id, [])
            ],
        })
    return result


# ── Group-scoped expense routes ──────────────────────────────────────────────

@router.get("/groups/{group_id}/list-expenses", response_model=list[ExpenseResponse])
async def get_expenses(
    group_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """List all expenses for a group (DESC by date)."""
    result = await db.execute(
        select(Expense)
        .where(Expense.group_id == group_id)
        .order_by(Expense.date.desc())
    )
    expenses = list(result.scalars().all())

    # Attach shares via a second query
    items = await _attach_shares(db, expenses)

    return [ExpenseResponse(**e) for e in items]


@router.post("/groups/{group_id}/create-expense", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
async def create_new_expense(
    group_id: uuid.UUID,
    body: ExpenseCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a new expense with shares."""
    expense = Expense(
        group_id=group_id,
        payer_id=body.payer_id,
        description=body.description,
        amount=body.amount,
        category=body.category,
        date=body.date or datetime.now(timezone.utc),
    )
    db.add(expense)
    await db.flush()  # populate expense.id

    # Create share entries
    for share in body.shares:
        db.add(
            ExpenseShare(
                expense_id=expense.id,
                debtor_id=share.debtor_id,
                creditor_id=share.creditor_id,
                amount_owed=share.amount_owed,
                percentage=share.percentage,
            )
        )

    await db.commit()
    await db.refresh(expense)

    # Return with shares attached
    items = await _attach_shares(db, [expense])
    return ExpenseResponse(**items[0])


# ── Single expense route (not group-scoped) ──────────────────────────────────

@router.get("/get-expense/{expense_id}", response_model=ExpenseResponse)
async def get_single_expense(
    expense_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get details of a single expense."""
    result = await db.execute(
        select(Expense).where(Expense.id == expense_id)
    )
    expense = result.scalar_one_or_none()
    if expense is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")

    items = await _attach_shares(db, [expense])
    return ExpenseResponse(**items[0])
