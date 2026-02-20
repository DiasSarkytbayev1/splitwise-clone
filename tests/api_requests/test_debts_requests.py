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


def test_debts_respects_debt_simplification_toggle(client, auth_user, register_user):
    """Use a 3-person chain (A->B 30, B->C 20) so simplification produces a
    different (fewer-or-equal transactions) result than the raw debts."""

    # ---- set up three users ----
    user_a = auth_user
    user_b_data = register_user(name="User B")
    user_b = {
        "user": user_b_data["user"],
        "headers": {"Authorization": f"Bearer {user_b_data['access_token']}"},
    }
    user_c_data = register_user(name="User C")
    user_c = {
        "user": user_c_data["user"],
        "headers": {"Authorization": f"Bearer {user_c_data['access_token']}"},
    }

    a_id = user_a["user"]["id"]
    b_id = user_b["user"]["id"]
    c_id = user_c["user"]["id"]

    # ---- create group & add members ----
    group_resp = client.post(
        "/groups",
        json={"name": "Simplification Toggle", "currency_code": "USD"},
        headers=user_a["headers"],
    )
    assert group_resp.status_code == 201
    group_id = group_resp.json()["id"]

    for uid in [b_id, c_id]:
        r = client.post(
            f"/groups/{group_id}/members",
            json={"user_id": uid},
            headers=user_a["headers"],
        )
        assert r.status_code == 201

    # Expense 1: A pays 30 for B  →  B owes A 30
    r1 = client.post(
        f"/groups/{group_id}/expenses",
        headers=user_a["headers"],
        json={
            "description": "A pays for B",
            "amount": "30.00",
            "payer_id": a_id,
            "category": "other",
            "splits": [{"debtor_id": b_id, "creditor_id": a_id,
                         "amount_owed": "30.00", "percentage": "100.00"}],
        },
    )
    assert r1.status_code == 201

    # Expense 2: B pays 20 for C  →  C owes B 20
    r2 = client.post(
        f"/groups/{group_id}/expenses",
        headers=user_b["headers"],
        json={
            "description": "B pays for C",
            "amount": "20.00",
            "payer_id": b_id,
            "category": "other",
            "splits": [{"debtor_id": c_id, "creditor_id": b_id,
                         "amount_owed": "20.00", "percentage": "100.00"}],
        },
    )
    assert r2.status_code == 201

    headers = user_a["headers"]

    # ---- normal (unsimplified) debts ----
    response = client.get(f"/groups/{group_id}/debts", headers=headers)
    assert response.status_code == 200
    debts = response.json()
    assert isinstance(debts, list)
    normal_debts = sorted(
        [(d["debtor_id"], d["creditor_id"], float(d["total_owed"])) for d in debts]
    )
    # raw: B->A 30 and C->B 20  (2 transactions)
    assert len(normal_debts) == 2

    # ---- toggle ON ----
    patch = client.patch(
        f"/groups/{group_id}", json={"debt_simplification": True}, headers=headers
    )
    assert patch.status_code == 200
    assert patch.json()["debt_simplification"] is True

    response = client.get(f"/groups/{group_id}/debts", headers=headers)
    assert response.status_code == 200
    debts_simplified = response.json()
    assert isinstance(debts_simplified, list)
    simplified = sorted(
        [(d["debtor_id"], d["creditor_id"], float(d["total_owed"])) for d in debts_simplified]
    )
    # Simplified should have <= same number but different structure
    assert len(simplified) <= len(normal_debts)
    # With a chain A<-B<-C, simplification should collapse B's role:
    # B->A 10, C->A 20  (different from the raw debts)
    assert simplified != normal_debts

    # ---- toggle OFF ----
    patch = client.patch(
        f"/groups/{group_id}", json={"debt_simplification": False}, headers=headers
    )
    assert patch.status_code == 200
    assert patch.json()["debt_simplification"] is False

    response = client.get(f"/groups/{group_id}/debts", headers=headers)
    assert response.status_code == 200
    debts_again = response.json()
    normal_debts2 = sorted(
        [(d["debtor_id"], d["creditor_id"], float(d["total_owed"])) for d in debts_again]
    )
    assert normal_debts2 == normal_debts


def test_circular_debts_cancel_out_with_simplification(client, auth_user, register_user):
    """A->B(10), B->C(10), C->A(10) with debt_simplification ON returns empty debt list."""
    # Create three users
    user_a = auth_user
    user_b_data = register_user(name="User B")
    user_b = {
        "user": user_b_data["user"],
        "token": user_b_data["access_token"],
        "headers": {"Authorization": f"Bearer {user_b_data['access_token']}"},
    }
    user_c_data = register_user(name="User C")
    user_c = {
        "user": user_c_data["user"],
        "token": user_c_data["access_token"],
        "headers": {"Authorization": f"Bearer {user_c_data['access_token']}"},
    }

    user_a_id = user_a["user"]["id"]
    user_b_id = user_b["user"]["id"]
    user_c_id = user_c["user"]["id"]

    # Create group with debt_simplification enabled
    group_resp = client.post(
        "/groups",
        json={"name": "Circular Test", "currency_code": "USD"},
        headers=user_a["headers"],
    )
    assert group_resp.status_code == 201
    group_id = group_resp.json()["id"]

    # Enable debt simplification
    patch_resp = client.patch(
        f"/groups/{group_id}",
        json={"debt_simplification": True},
        headers=user_a["headers"],
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["debt_simplification"] is True

    # Add members B and C
    add_b = client.post(
        f"/groups/{group_id}/members",
        json={"user_id": user_b_id},
        headers=user_a["headers"],
    )
    assert add_b.status_code == 201

    add_c = client.post(
        f"/groups/{group_id}/members",
        json={"user_id": user_c_id},
        headers=user_a["headers"],
    )
    assert add_c.status_code == 201

    # Expense 1: A pays 10, B owes A 10  (A->B debt)
    resp1 = client.post(
        f"/groups/{group_id}/expenses",
        headers=user_a["headers"],
        json={
            "description": "A pays for B",
            "amount": "10.00",
            "payer_id": user_a_id,
            "category": "other",
            "splits": [
                {
                    "debtor_id": user_b_id,
                    "creditor_id": user_a_id,
                    "amount_owed": "10.00",
                    "percentage": "100.00",
                }
            ],
        },
    )
    assert resp1.status_code == 201

    # Expense 2: B pays 10, C owes B 10  (B->C debt)
    resp2 = client.post(
        f"/groups/{group_id}/expenses",
        headers=user_b["headers"],
        json={
            "description": "B pays for C",
            "amount": "10.00",
            "payer_id": user_b_id,
            "category": "other",
            "splits": [
                {
                    "debtor_id": user_c_id,
                    "creditor_id": user_b_id,
                    "amount_owed": "10.00",
                    "percentage": "100.00",
                }
            ],
        },
    )
    assert resp2.status_code == 201

    # Expense 3: C pays 10, A owes C 10  (C->A debt)
    resp3 = client.post(
        f"/groups/{group_id}/expenses",
        headers=user_c["headers"],
        json={
            "description": "C pays for A",
            "amount": "10.00",
            "payer_id": user_c_id,
            "category": "other",
            "splits": [
                {
                    "debtor_id": user_a_id,
                    "creditor_id": user_c_id,
                    "amount_owed": "10.00",
                    "percentage": "100.00",
                }
            ],
        },
    )
    assert resp3.status_code == 201

    # Fetch debts – circular debts should cancel out completely
    debts_resp = client.get(
        f"/groups/{group_id}/debts",
        headers=user_a["headers"],
    )
    assert debts_resp.status_code == 200
    debts = debts_resp.json()
    assert debts == [], f"Circular debts A->B(10), B->C(10), C->A(10) should cancel out, got: {debts}"


