import uuid


def test_list_debts_returns_summary_rows(client, expense_and_debt):
    response = client.get(
        f"/groups/{expense_and_debt['group_id']}/debts",
        headers=expense_and_debt["owner"]["headers"],
    )

    assert response.status_code == 200
    debts = response.json()
    assert isinstance(debts, list)
    assert len(debts) >= 1
    assert "debtor_id" in debts[0]
    assert "creditor_id" in debts[0]
    assert "total_owed" in debts[0]


def test_settle_debt_marks_debt_settled(client, expense_and_debt):
    response = client.post(
        f"/groups/{expense_and_debt['group_id']}/debts/{expense_and_debt['debt_id']}/settle",
        headers=expense_and_debt["owner"]["headers"],
    )

    assert response.status_code == 200
    data = response.json()
    assert data["settled_count"] == 1
    assert "settled successfully" in data["message"]


def test_settle_debt_twice_returns_400(client, expense_and_debt):
    first = client.post(
        f"/groups/{expense_and_debt['group_id']}/debts/{expense_and_debt['debt_id']}/settle",
        headers=expense_and_debt["owner"]["headers"],
    )
    second = client.post(
        f"/groups/{expense_and_debt['group_id']}/debts/{expense_and_debt['debt_id']}/settle",
        headers=expense_and_debt["owner"]["headers"],
    )

    assert first.status_code == 200
    assert second.status_code == 400
    assert second.json()["detail"] == "Debt is already settled"


def test_settle_debt_not_found_returns_404(client, expense_and_debt):
    response = client.post(
        f"/groups/{expense_and_debt['group_id']}/debts/{uuid.uuid4()}/settle",
        headers=expense_and_debt["owner"]["headers"],
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Debt not found in this group"
