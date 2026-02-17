import uuid


def test_create_expense_returns_expense_with_splits(client, group_with_two_members):
    group_id = group_with_two_members["group"]["id"]
    owner_id = group_with_two_members["owner"]["user"]["id"]
    member_id = group_with_two_members["member"]["user"]["id"]

    response = client.post(
        f"/groups/{group_id}/expenses",
        headers=group_with_two_members["owner"]["headers"],
        json={
            "description": "Lunch",
            "amount": "40.00",
            "payer_id": owner_id,
            "category": "food",
            "splits": [
                {
                    "debtor_id": member_id,
                    "creditor_id": owner_id,
                    "amount_owed": "20.00",
                    "percentage": "50.00",
                }
            ],
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["group_id"] == group_id
    assert data["description"] == "Lunch"
    assert "id" in data
    assert len(data["splits"]) == 1
    assert data["splits"][0]["debtor_id"] == member_id


def test_list_expenses_returns_paginated_payload(client, expense_and_debt):
    response = client.get(
        f"/groups/{expense_and_debt['group_id']}/expenses",
        headers=expense_and_debt["owner"]["headers"],
    )

    assert response.status_code == 200
    data = response.json()
    assert "expenses" in data
    assert "total" in data
    assert "page" in data
    assert "limit" in data
    assert len(data["expenses"]) >= 1
    assert "id" in data["expenses"][0]


def test_list_expenses_for_non_member_returns_403(client, expense_and_debt, register_user):
    outsider = register_user(name="Outsider User")
    headers = {"Authorization": f"Bearer {outsider['access_token']}"}
    response = client.get(f"/groups/{expense_and_debt['group_id']}/expenses", headers=headers)

    assert response.status_code == 403
    assert response.json()["detail"] == "You are not a member of this group"


def test_get_expense_returns_single_expense_details(client, expense_and_debt):
    expense_id = expense_and_debt["expense"]["id"]
    response = client.get(
        f"/expenses/{expense_id}",
        headers=expense_and_debt["owner"]["headers"],
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == expense_id
    assert data["group_id"] == expense_and_debt["group_id"]
    assert "splits" in data


def test_get_expense_not_found_returns_404(client, auth_user):
    response = client.get(f"/expenses/{uuid.uuid4()}", headers=auth_user["headers"])

    assert response.status_code == 404
    assert response.json()["detail"] == "Expense not found"
