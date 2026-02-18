"""
Test script that calls every API endpoint on http://localhost:8000
and prints the responses.

Usage:  python test.py
"""

import json

import requests

BASE = "http://127.0.0.1:8000"
TIMEOUT = 5  # seconds per request


def pretty(label, resp):
    """Print a labelled response."""
    print(f"\n{'=' * 60}")
    print(f"  {label}")
    print(f"  {resp.request.method} {resp.url}")
    print(f"  Status: {resp.status_code}")
    print(f"{'=' * 60}")
    try:
        print(json.dumps(resp.json(), indent=2, default=str))
    except Exception:
        print(resp.text)


# ── 1. Health Check ──────────────────────────────────────────────────────────


def test_health():
    resp = requests.get(f"{BASE}/", timeout=TIMEOUT)
    pretty("Health Check", resp)
    return resp.json()


# ── 2. Auth ──────────────────────────────────────────────────────────────────


def test_register(name, email, password):
    resp = requests.post(
        f"{BASE}/auth/register",
        json={
            "name": name,
            "email": email,
            "password": password,
        },
        timeout=TIMEOUT,
    )
    pretty(f"Register ({email})", resp)
    return resp.json()


def test_login(email, password):
    resp = requests.post(
        f"{BASE}/auth/login",
        json={
            "email": email,
            "password": password,
        },
        timeout=TIMEOUT,
    )
    pretty(f"Login ({email})", resp)
    return resp.json()


# ── 3. Groups ────────────────────────────────────────────────────────────────


def test_create_group(user_id, name):
    resp = requests.post(
        f"{BASE}/groups",
        json={
            "name": name,
            "user_id": user_id,
        },
        timeout=TIMEOUT,
    )
    pretty(f"Create Group ({name})", resp)
    return resp.json()


def test_list_groups(user_id):
    resp = requests.get(f"{BASE}/groups", params={"user_id": user_id}, timeout=TIMEOUT)
    pretty(f"List Groups (user={user_id[:8]}...)", resp)
    return resp.json()


def test_get_group(group_id):
    resp = requests.get(f"{BASE}/groups/{group_id}", timeout=TIMEOUT)
    pretty(f"Get Group ({group_id})", resp)
    return resp.json()


def test_get_group_by_code(code):
    resp = requests.get(f"{BASE}/groups/code/{code}", timeout=TIMEOUT)
    pretty(f"Get Group By Invite Code ({code})", resp)
    return resp.json()


# ── 4. Members ───────────────────────────────────────────────────────────────


def test_get_members(group_id):
    resp = requests.get(f"{BASE}/groups/{group_id}/members", timeout=TIMEOUT)
    pretty(f"List Members (group={group_id})", resp)
    return resp.json()


def test_get_invite_code(group_id):
    resp = requests.get(f"{BASE}/groups/{group_id}/members/invite", timeout=TIMEOUT)
    pretty(f"Get Invite Code (group={group_id})", resp)
    return resp.json()


def test_add_member(group_id, user_id):
    resp = requests.post(
        f"{BASE}/groups/{group_id}/members",
        json={
            "user_id": user_id,
        },
        timeout=TIMEOUT,
    )
    pretty(f"Add Member (user={user_id[:8]}...)", resp)
    return resp.json()


def test_remove_member(group_id, user_id):
    resp = requests.delete(f"{BASE}/groups/{group_id}/members/{user_id}", timeout=TIMEOUT)
    pretty(f"Remove Member (user={user_id[:8]}...)", resp)
    return resp.status_code


# ── 5. Expenses ──────────────────────────────────────────────────────────────


def test_list_expenses(group_id):
    resp = requests.get(f"{BASE}/groups/{group_id}/expenses", timeout=TIMEOUT)
    pretty(f"List Expenses (group={group_id})", resp)
    return resp.json()


def test_create_expense(group_id, payer_id, description, amount, shares, category=None):
    resp = requests.post(
        f"{BASE}/groups/{group_id}/expenses/create",
        json={
            "description": description,
            "amount": str(amount),
            "payer_id": payer_id,
            "shares": shares,
            "category": category,
        },
        timeout=TIMEOUT,
    )
    pretty(f"Create Expense ({description})", resp)
    return resp.json()


def test_get_expense(expense_id):
    resp = requests.get(f"{BASE}/expenses/{expense_id}", timeout=TIMEOUT)
    pretty(f"Get Expense ({expense_id})", resp)
    return resp.json()


# ── 6. Debts ─────────────────────────────────────────────────────────────────


def test_list_debts(group_id):
    resp = requests.get(f"{BASE}/groups/{group_id}/debts", timeout=TIMEOUT)
    pretty(f"List Debts (group={group_id})", resp)
    return resp.json()


def test_settle_debt(group_id, debtor_id, creditor_id):
    resp = requests.post(
        f"{BASE}/groups/{group_id}/debts/settle",
        json={
            "debtor_id": debtor_id,
            "creditor_id": creditor_id,
        },
        timeout=TIMEOUT,
    )
    pretty(f"Settle Debt ({debtor_id[:8]}... -> {creditor_id[:8]}...)", resp)
    return resp.json()


# ── Run all tests ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n🚀 Starting API tests against", BASE)

    # Health
    test_health()

    # # Register two users
    #     user_a = test_register("Test Alice", "test_alice@example.com", "pass1234")
    #     user_b = test_register("Test Bob", "test_bob@example.com", "pass1234")
    #     uid_a = user_a["id"]
    #     uid_b = user_b["id"]
    #
    #     # Login
    #     test_login("test_alice@example.com", "pass1234")
    #
    #     # Create group (Alice creates)
    #     group = test_create_group(uid_a, "Test Trip")
    #     gid = group["id"]
    #     invite_code = group["invite_code"]
    #
    #     # List groups for Alice
    #     test_list_groups(uid_a)
    #
    #     # Get group by id
    test_get_group(1)
    #
    #     # Get group by invite code
    #     test_get_group_by_code(invite_code)
    #
    #     # Members — list (Alice is already in)
    #     test_get_members(gid)
    #
    #     # Members — get invite code
    #     test_get_invite_code(gid)
    #
    #     # Members — add Bob
    #     test_add_member(gid, uid_b)
    #
    #     # Members — list again (should show both)
    #     test_get_members(gid)
    #
    #     # Create expense — Alice paid $60 dinner, Bob owes $30
    #     expense = test_create_expense(
    #         group_id=gid,
    #         payer_id=uid_a,
    #         description="Dinner",
    #         amount=60,
    #         shares=[{
    #             "debtor_id": uid_b,
    #             "creditor_id": uid_a,
    #             "amount_owed": "30.00",
    #             "percentage": "50.00",
    #         }],
    #         category="food",
    #     )
    #     eid = expense["id"]
    #
    #     # List expenses
    #     test_list_expenses(gid)
    #
    #     # Get single expense
    #     test_get_expense(eid)
    #
    #     # Debts — list
    #     test_list_debts(gid)
    #
    #     # Debts — settle
    #     test_settle_debt(gid, uid_b, uid_a)
    #
    #     # Debts — list again (should be empty now)
    #     test_list_debts(gid)
    #
    #     # Cleanup — remove Bob from group
    #     test_remove_member(gid, uid_b)

    print("\n✅ All tests completed!")
