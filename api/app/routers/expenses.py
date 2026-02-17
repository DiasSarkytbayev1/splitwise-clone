from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.dependencies import get_db
from api.app.auth import get_current_user
from api.app.models.user import User
from api.app.models.group import Group
from api.app.models.group_member import GroupMember
from api.app.models.expense import Expense
from api.app.models.expense_share import ExpenseShare
from api.app.schemas.expense import (
    ExpenseCreateRequest,
    ExpenseResponse,
    ExpenseListResponse,
)

router = APIRouter(tags=["Expenses"])


async def _verify_group_membership(db: AsyncSession, group_id: uuid.UUID, user_id: uuid.UUID) -> None:
    """Verify that a user is a member of the group."""
    result = await db.execute(
        select(GroupMember).where(
            GroupMember.group_id == group_id,
            GroupMember.user_id == user_id,
        )
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this group"
        )


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
            "splits": [
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

@router.get("/groups/{group_id}/expenses", response_model=ExpenseListResponse)
async def list_expenses(
    group_id: uuid.UUID,
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all expenses for a group (paginated, DESC by date)."""
    # Verify user is a member
    await _verify_group_membership(db, group_id, current_user.id)

    # Get total count
    count_result = await db.execute(
        select(func.count()).select_from(Expense).where(Expense.group_id == group_id)
    )
    total = count_result.scalar()

    # Get paginated expenses
    offset = (page - 1) * limit
    result = await db.execute(
        select(Expense)
        .where(Expense.group_id == group_id)
        .order_by(Expense.date.desc())
        .offset(offset)
        .limit(limit)
    )
    expenses = list(result.scalars().all())

    # Attach shares
    items = await _attach_shares(db, expenses)

    return ExpenseListResponse(
        expenses=[ExpenseResponse(**e) for e in items],
        total=total,
        page=page,
        limit=limit,
        total_pages=(total + limit - 1) // limit if total > 0 else 0,
    )


@router.post("/groups/{group_id}/expenses", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
async def create_expense(
    group_id: uuid.UUID,
    body: ExpenseCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new expense or settlement. Settlements use category='settlement'."""
    # Verify user is a member
    await _verify_group_membership(db, group_id, current_user.id)

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

    # Create split entries
    for split in body.splits:
        db.add(
            ExpenseShare(
                expense_id=expense.id,
                debtor_id=split.debtor_id,
                creditor_id=split.creditor_id,
                amount_owed=split.amount_owed,
                percentage=split.percentage,
            )
        )

    await db.commit()
    await db.refresh(expense)

    # Return with splits attached
    items = await _attach_shares(db, [expense])
    return ExpenseResponse(**items[0])


# ── Single expense route (not group-scoped) ──────────────────────────────────

@router.get("/expenses/{id}", response_model=ExpenseResponse)
async def get_expense(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get details of a single expense."""
    result = await db.execute(
        select(Expense).where(Expense.id == id)
    )
    expense = result.scalar_one_or_none()
    if expense is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found"
        )

    # Verify user is a member of the group
    await _verify_group_membership(db, expense.group_id, current_user.id)

    items = await _attach_shares(db, [expense])
    return ExpenseResponse(**items[0])
