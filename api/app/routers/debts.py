import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.models.expense import Expense
from app.models.expense_share import ExpenseShare
from app.schemas.debt import DebtSummaryResponse, SettleRequest, SettleResponse

router = APIRouter(prefix="/groups/{group_id}/debts", tags=["Debts"])


@router.get("/list-debts", response_model=list[DebtSummaryResponse])
async def list_debts(
    group_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """List all pending debts in a group (aggregated by debtor/creditor)."""
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


@router.post("/settle-debt", response_model=SettleResponse)
async def settle_group_debt(
    group_id: uuid.UUID,
    body: SettleRequest,
    db: AsyncSession = Depends(get_db),
):
    """Settle all pending shares between a debtor and creditor in a group."""
    # Find all pending shares for this debtor→creditor pair within the group
    result = await db.execute(
        select(ExpenseShare)
        .join(Expense, ExpenseShare.expense_id == Expense.id)
        .where(
            Expense.group_id == group_id,
            ExpenseShare.debtor_id == body.debtor_id,
            ExpenseShare.creditor_id == body.creditor_id,
            ExpenseShare.status == "pending",
        )
    )
    shares = result.scalars().all()

    if not shares:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No pending debts found for this pair")

    for share in shares:
        share.status = "settled"

    await db.commit()

    return SettleResponse(settled_count=len(shares), message=f"Settled {len(shares)} expense share(s)")
