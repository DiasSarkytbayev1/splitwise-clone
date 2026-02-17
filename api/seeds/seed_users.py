from api.app.models.user import User
from api.app.database import Session
from api.app.routers.auth import hash_password


def seed_users():
    session = Session()

    user1 = User(
        name="Alice Johnson",
        email="alice@example.com",
        password_hash=hash_password("password123"),
    )

    user2 = User(
        name="Bob Smith",
        email="bob@example.com",
        password_hash=hash_password("password123"),
    )

    user3 = User(
        name="Charlie Brown",
        email="charlie@example.com",
        password_hash=hash_password("password123"),
    )

    session.add_all([user1, user2, user3])
    session.commit()
    session.close()

    print("✅ Users seeded successfully")
