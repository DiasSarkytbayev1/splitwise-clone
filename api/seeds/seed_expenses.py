import datetime

from api.app.database import Session
from api.app.models.expense import Expense
from api.app.models.group import Group
from api.app.models.user import User


def seed_expenses():
    session = Session()

    users = session.query(User).order_by(User.created_at.asc()).limit(3).all()

    if len(users) < 3:
        print("Need at least 3 users seeded first.")
        session.close()
        return

    group = session.query(Group).order_by(Group.created_at.asc()).first()

    if group is None:
        print("Need at least one group seeded first.")
        session.close()
        return

    alice = users[0]
    bob = users[1]

    now = datetime.datetime.now(datetime.UTC)

    # Expense 1 — Alice paid for dinner ($90), split among all 3
    expense1 = Expense(
        group_id=group.id,
        payer_id=alice.id,
        description="Dinner at restaurant",
        amount=90.00,
        category="food",
        date=now - datetime.timedelta(days=2),
    )

    # Expense 2 — Bob paid for groceries ($60), split among all 3
    expense2 = Expense(
        group_id=group.id,
        payer_id=bob.id,
        description="Weekly groceries",
        amount=60.00,
        category="groceries",
        date=now - datetime.timedelta(days=1),
    )

    session.add_all([expense1, expense2])
    session.commit()
    session.close()

    print("✅ Expenses seeded successfully")
