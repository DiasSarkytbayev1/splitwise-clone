import uuid


def test_create_group_returns_group_payload(client, auth_user):
    response = client.post(
        "/groups",
        json={"name": "Weekend Trip", "currency_code": "USD"},
        headers=auth_user["headers"],
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Weekend Trip"
    assert data["currency_code"] == "USD"
    assert "id" in data
    assert "invite_code" in data
    assert data["created_by"] == auth_user["user"]["id"]


def test_list_groups_returns_created_group(client, auth_user, created_group):
    response = client.get("/groups", headers=auth_user["headers"])

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(group["id"] == created_group["id"] for group in data)


def test_list_groups_requires_auth(client):
    response = client.get("/groups")
    assert response.status_code == 403


def test_get_group_by_id_returns_group(client, auth_user, created_group):
    group_id = created_group["id"]
    response = client.get(f"/groups/{group_id}", headers=auth_user["headers"])

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == group_id
    assert data["name"] == created_group["name"]


def test_get_group_by_invite_code_returns_group(client, auth_user, created_group):
    response = client.get(f"/groups/{created_group['invite_code']}", headers=auth_user["headers"])

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == created_group["id"]


def test_get_group_not_found_returns_404(client, auth_user):
    response = client.get(f"/groups/{uuid.uuid4()}", headers=auth_user["headers"])

    assert response.status_code == 404
    assert response.json()["detail"] == "Group not found"


def test_group_response_includes_debt_simplification(client, auth_user):
    response = client.post(
        "/groups",
        json={"name": "Test Group", "currency_code": "USD"},
        headers=auth_user["headers"],
    )
    assert response.status_code == 201
    group = response.json()
    assert "debt_simplification" in group
    assert group["debt_simplification"] is False

    # Now fetch by id
    response = client.get(f"/groups/{group['id']}", headers=auth_user["headers"])
    assert response.status_code == 200
    group2 = response.json()
    assert group2["debt_simplification"] is False


def test_patch_group_toggle_debt_simplification(client, auth_user, created_group):
    group_id = created_group["id"]
    # Toggle on
    response = client.patch(
        f"/groups/{group_id}",
        json={"debt_simplification": True},
        headers=auth_user["headers"],
    )
    assert response.status_code == 200
    data = response.json()
    assert data["debt_simplification"] is True

    # Toggle off
    response = client.patch(
        f"/groups/{group_id}",
        json={"debt_simplification": False},
        headers=auth_user["headers"],
    )
    assert response.status_code == 200
    data = response.json()
    assert data["debt_simplification"] is False
