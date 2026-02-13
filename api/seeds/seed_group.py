from app.models.user import User
from app.models.group import Group
from app.database import Session


def seed_group():
    session = Session()

    # Get the first user to be the group creator
    creator = (
        session.query(User)
        .order_by(User.created_at.asc())
        .first()
    )

    if creator is None:
        print("Need at least one user seeded first.")
        session.close()
        return

    group = Group(
        name="Apartment Roommates",
        type="home",
        currency_code="USD",
        created_by=creator.id,
    )

    session.add(group)
    session.commit()
    session.close()

    print("✅ Group seeded successfully")
