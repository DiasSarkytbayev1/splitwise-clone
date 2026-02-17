from decimal import Decimal

from api.app.models.user import User
from api.app.models.expense import Expense
from api.app.models.expense_share import ExpenseShare
from api.app.database import Session


def seed_expense_shares():
    session = Session()

    users = (
        session.query(User)
        .order_by(User.created_at.asc())
        .limit(3)
        .all()
    )

    if len(users) < 3:
        print("Need at least 3 users seeded first.")
        session.close()
        return

    expenses = (
        session.query(Expense)
        .order_by(Expense.date.asc())
        .limit(2)
        .all()
    )

    if len(expenses) < 2:
        print("Need at least 2 expenses seeded first.")
        session.close()
        return

    alice = users[0]
    bob = users[1]
    charlie = users[2]

    dinner = expenses[0]    # Alice paid $90
    groceries = expenses[1] # Bob paid $60

    # ── Dinner ($90 paid by Alice, split equally 3 ways = $30 each) ──────────
    # Bob owes Alice $30
    share1 = ExpenseShare(
        expense_id=dinner.id,
        debtor_id=bob.id,
        creditor_id=alice.id,
        amount_owed=Decimal("30.00"),
        percentage=Decimal("33.33"),
        status="pending",
    )

    # Charlie owes Alice $30
    share2 = ExpenseShare(
        expense_id=dinner.id,
        debtor_id=charlie.id,
        creditor_id=alice.id,
        amount_owed=Decimal("30.00"),
        percentage=Decimal("33.33"),
        status="pending",
    )

    # ── Groceries ($60 paid by Bob, split equally 3 ways = $20 each) ─────────
    # Alice owes Bob $20
    share3 = ExpenseShare(
        expense_id=groceries.id,
        debtor_id=alice.id,
        creditor_id=bob.id,
        amount_owed=Decimal("20.00"),
        percentage=Decimal("33.33"),
        status="pending",
    )

    # Charlie owes Bob $20
    share4 = ExpenseShare(
        expense_id=groceries.id,
        debtor_id=charlie.id,
        creditor_id=bob.id,
        amount_owed=Decimal("20.00"),
        percentage=Decimal("33.33"),
        status="pending",
    )

    session.add_all([share1, share2, share3, share4])
    session.commit()
    session.close()

    print("✅ Expense shares seeded successfully")
