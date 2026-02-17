import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.app.auth import get_db_for_auth
from api.app.database import Base
from api.app.dependencies import get_db
from api.app.main import app
test_client = TestClient(app)




SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class SyncSessionAdapter:
    """Expose async-like methods over a sync SQLAlchemy session."""

    def __init__(self, session):
        self._session = session

    async def execute(self, *args, **kwargs):
        return self._session.execute(*args, **kwargs)

    async def get(self, *args, **kwargs):
        return self._session.get(*args, **kwargs)

    def add(self, *args, **kwargs):
        return self._session.add(*args, **kwargs)

    async def flush(self):
        return self._session.flush()

    async def commit(self):
        return self._session.commit()

    async def refresh(self, instance):
        return self._session.refresh(instance)

    async def delete(self, instance):
        return self._session.delete(instance)


async def override_get_db():
    db = TestingSessionLocal()
    adapter = SyncSessionAdapter(db)
    try:
        yield adapter
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    prev_get_db = app.dependency_overrides.get(get_db)
    prev_get_db_for_auth = app.dependency_overrides.get(get_db_for_auth)
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_db_for_auth] = override_get_db
    yield
    if prev_get_db is None:
        app.dependency_overrides.pop(get_db, None)
    else:
        app.dependency_overrides[get_db] = prev_get_db

    if prev_get_db_for_auth is None:
        app.dependency_overrides.pop(get_db_for_auth, None)
    else:
        app.dependency_overrides[get_db_for_auth] = prev_get_db_for_auth
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    yield test_client


@pytest.fixture
def unique_email():
    def _unique_email(prefix: str = "user"):
        return f"{prefix}_{uuid.uuid4().hex[:8]}@example.com"

    return _unique_email


@pytest.fixture
def register_user(client, unique_email):
    def _register_user(name: str = "Test User", email: str | None = None, password: str = "password123"):
        payload = {
            "name": name,
            "email": email or unique_email("user"),
            "password": password,
        }
        response = client.post("/auth/register", json=payload)
        assert response.status_code == 201
        return response.json()

    return _register_user


@pytest.fixture
def auth_user(register_user):
    user_data = register_user(name="Primary User")
    return {
        "user": user_data["user"],
        "token": user_data["access_token"],
        "headers": {"Authorization": f"Bearer {user_data['access_token']}"},
    }


@pytest.fixture
def second_user(register_user):
    user_data = register_user(name="Secondary User")
    return {
        "user": user_data["user"],
        "token": user_data["access_token"],
        "headers": {"Authorization": f"Bearer {user_data['access_token']}"},
    }


@pytest.fixture
def created_group(client, auth_user):
    response = client.post(
        "/groups",
        json={"name": "Trip to Tokyo", "currency_code": "USD"},
        headers=auth_user["headers"],
    )
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def group_with_two_members(client, auth_user, second_user, created_group):
    group_id = created_group["id"]
    add_response = client.post(
        f"/groups/{group_id}/members",
        json={"user_id": second_user["user"]["id"]},
        headers=auth_user["headers"],
    )
    assert add_response.status_code == 201
    return {
        "group": created_group,
        "owner": auth_user,
        "member": second_user,
    }


@pytest.fixture
def expense_and_debt(client, group_with_two_members):
    group_id = group_with_two_members["group"]["id"]
    owner_id = group_with_two_members["owner"]["user"]["id"]
    member_id = group_with_two_members["member"]["user"]["id"]

    expense_response = client.post(
        f"/groups/{group_id}/expenses",
        headers=group_with_two_members["owner"]["headers"],
        json={
            "description": "Dinner",
            "amount": "60.00",
            "payer_id": owner_id,
            "category": "food",
            "splits": [
                {
                    "debtor_id": member_id,
                    "creditor_id": owner_id,
                    "amount_owed": "30.00",
                    "percentage": "50.00",
                }
            ],
        },
    )
    assert expense_response.status_code == 201
    expense = expense_response.json()

    debts_response = client.get(
        f"/groups/{group_id}/debts",
        headers=group_with_two_members["owner"]["headers"],
    )
    assert debts_response.status_code == 200
    debts = debts_response.json()
    assert len(debts) >= 1

    debt_id = expense["splits"][0]["id"]
    return {
        "group_id": group_id,
        "expense": expense,
        "debt_id": debt_id,
        "owner": group_with_two_members["owner"],
        "member": group_with_two_members["member"],
    }
