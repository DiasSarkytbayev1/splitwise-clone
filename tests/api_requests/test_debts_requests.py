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


def test_debts_respects_debt_simplification_toggle(client, expense_and_debt):
    group_id = expense_and_debt["group_id"]
    headers = expense_and_debt["owner"]["headers"]

    # Ensure default is not simplified
    response = client.get(f"/groups/{group_id}/debts", headers=headers)
    assert response.status_code == 200
    debts = response.json()
    assert isinstance(debts, list)
    # Save for comparison
    normal_debts = [tuple((d["debtor_id"], d["creditor_id"], float(d["total_owed"]))) for d in debts]

    # Toggle on debt_simplification
    patch = client.patch(f"/groups/{group_id}", json={"debt_simplification": True}, headers=headers)
    assert patch.status_code == 200
    assert patch.json()["debt_simplification"] is True

    # Now debts should be simplified
    response = client.get(f"/groups/{group_id}/debts", headers=headers)
    assert response.status_code == 200
    debts_simplified = response.json()
    assert isinstance(debts_simplified, list)
    simplified = [tuple((d["debtor_id"], d["creditor_id"], float(d["total_owed"]))) for d in debts_simplified]
    # Should be different if simplification is meaningful
    assert simplified != normal_debts or len(simplified) == 0

    # Toggle off again
    patch = client.patch(f"/groups/{group_id}", json={"debt_simplification": False}, headers=headers)
    assert patch.status_code == 200
    assert patch.json()["debt_simplification"] is False

    # Should match original
    response = client.get(f"/groups/{group_id}/debts", headers=headers)
    assert response.status_code == 200
    debts_again = response.json()
    normal_debts2 = [tuple((d["debtor_id"], d["creditor_id"], float(d["total_owed"]))) for d in debts_again]
    assert normal_debts2 == normal_debts
