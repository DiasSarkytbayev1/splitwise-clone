import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.auth import get_current_user
from api.app.dependencies import get_db
from api.app.models.expense import Expense
from api.app.models.expense_share import ExpenseShare
from api.app.models.group import Group
from api.app.models.group_member import GroupMember
from api.app.models.user import User
from api.app.schemas.debt import DebtSummaryResponse, SettleResponse
from domains.expense.repository import ExpenseRepository
from domains.expense.service import ExpenseService
from domains.group.repository import GroupRepository

router = APIRouter(prefix="/groups/{group_id}/debts", tags=["Debts"])


async def _verify_group_membership(
    db: AsyncSession, group_id: uuid.UUID, user_id: uuid.UUID
) -> None:
    """Verify that a user is a member of the group."""
    result = await db.execute(
        select(GroupMember).where(
            GroupMember.group_id == group_id,
            GroupMember.user_id == user_id,
        )
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="You are not a member of this group"
        )


@router.get("", response_model=list[DebtSummaryResponse])
async def list_debts(
    group_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all pending debts in a group (aggregated by debtor/creditor)."""
    # Verify user is a member
    await _verify_group_membership(db, group_id, current_user.id)

    # Fetch group to check debt_simplification
    group_result = await db.execute(select(Group).where(Group.id == group_id))
    group = group_result.scalar_one_or_none()
    if group is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")

    if group.debt_simplification:
        # Use settlement plan logic
        expense_repo = ExpenseRepository(db)
        group_repo = GroupRepository(db)
        expense_service = ExpenseService(expense_repo, group_repo)
        settlements = await expense_service.get_settlement_plan(group_id)
        # settlements: list[tuple[User, User, float]]
        return [
            DebtSummaryResponse(
                debtor_id=debtor.id,
                creditor_id=creditor.id,
                total_owed=amount,
            )
            for debtor, creditor, amount in settlements
        ]
    else:
        result = await db.execute(
            select(
                ExpenseShare.debtor_id,
                ExpenseShare.creditor_id,
                func.sum(ExpenseShare.amount_owed).label("total_owed"),
            )
            .join(Expense, ExpenseShare.expense_id == Expense.id)
            .where(Expense.group_id == group_id, ExpenseShare.status == "pending")
            .group_by(ExpenseShare.debtor_id, ExpenseShare.creditor_id)
        )
        return [
            DebtSummaryResponse(
                debtor_id=row.debtor_id,
                creditor_id=row.creditor_id,
                total_owed=row.total_owed,
            )
            for row in result.all()
        ]


@router.post("/{debt_id}/settle", response_model=SettleResponse)
async def settle_debt(
    group_id: uuid.UUID,
    debt_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Settle a specific debt (expense share) by marking it as settled."""
    # Verify user is a member
    await _verify_group_membership(db, group_id, current_user.id)

    # Find the specific expense share
    result = await db.execute(
        select(ExpenseShare)
        .join(Expense, ExpenseShare.expense_id == Expense.id)
        .where(
            ExpenseShare.id == debt_id,
            Expense.group_id == group_id,
        )
    )
    debt = result.scalar_one_or_none()

    if debt is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Debt not found in this group"
        )

    if debt.status == "settled":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Debt is already settled"
        )

    # Mark as settled
    debt.status = "settled"
    await db.commit()

    return SettleResponse(
        settled_count=1, message=f"Debt of {debt.amount_owed} settled successfully"
    )
