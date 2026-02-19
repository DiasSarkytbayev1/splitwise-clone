import uuid
from decimal import Decimal

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


class SQLAlchemyExpenseRepository(ExpenseRepository):
    def __init__(self, db):
        super().__init__()
        self.db = db

    async def find_by_group_id(self, group_id):
        import uuid

        from api.app.models.expense import Expense

        if isinstance(group_id, str):
            group_id = uuid.UUID(group_id)
        result = await self.db.execute(select(Expense).where(Expense.group_id == group_id))
        expenses = result.scalars().all()
        return expenses


class SQLAlchemyGroupRepository(GroupRepository):
    def __init__(self, db):
        super().__init__()
        self.db = db

    async def find_by_id(self, group_id):
        from api.app.models.group import Group

        result = await self.db.execute(select(Group).where(Group.id == group_id))
        group = result.scalar_one_or_none()
        return group


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
        from domain import Expense as DomainExpense
        from domain import User as DomainUser

        # 1. Implement User Cache to maintain object identity for the algorithm
        user_cache = {}

        def get_domain_user(user_id: str) -> DomainUser:
            if user_id not in user_cache:
                user_cache[user_id] = DomainUser(id=user_id, name=None, email=None, password=None)
            return user_cache[user_id]

        # 2. Fetch pending shares directly instead of trusting total expense amounts.
        shares_result = await db.execute(
            select(ExpenseShare)
            .join(Expense, ExpenseShare.expense_id == Expense.id)
            .where(Expense.group_id == group_id, ExpenseShare.status == "pending")
        )
        shares = shares_result.scalars().all()

        domain_expenses = []
        for share in shares:
            # Treat each pending share as a virtual 1-to-1 expense.
            # This ensures the algorithm uses the exact `amount_owed`.
            payer = get_domain_user(str(share.creditor_id))
            debtor = get_domain_user(str(share.debtor_id))

            domain_expenses.append(
                DomainExpense(
                    id=str(share.id),
                    group_id=str(group_id),
                    amount=float(share.amount_owed),
                    payer=payer,
                    debtors={debtor},
                )
            )

        settlements = ExpenseService._get_settlements(domain_expenses)
        return [
            DebtSummaryResponse(
                debtor_id=getattr(debtor, "id", debtor),
                creditor_id=getattr(creditor, "id", creditor),
                total_owed=Decimal(str(amount)),
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
        # Net out mutual debts between each pair
        raw_debts = {}
        for row in result.all():
            key = (str(row.debtor_id), str(row.creditor_id))
            raw_debts[key] = float(row.total_owed)
        # Netting logic
        net_debts = {}
        processed = set()
        for (debtor, creditor), amount in raw_debts.items():
            if (creditor, debtor) in processed:
                continue  # already processed reverse
            reverse_amount = raw_debts.get((creditor, debtor), 0)
            net = amount - reverse_amount
            if net > 0:
                net_debts[(debtor, creditor)] = net
            elif net < 0:
                net_debts[(creditor, debtor)] = -net
            # else net == 0: skip
            processed.add((debtor, creditor))
            processed.add((creditor, debtor))
        return [
            DebtSummaryResponse(
                debtor_id=debtor,
                creditor_id=creditor,
                total_owed=amount,
            )
            for (debtor, creditor), amount in net_debts.items()
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
