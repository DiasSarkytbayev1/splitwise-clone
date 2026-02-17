import uuid


def test_get_members_returns_group_members(client, group_with_two_members):
    group_id = group_with_two_members["group"]["id"]
    response = client.get(
        f"/groups/{group_id}/members",
        headers=group_with_two_members["owner"]["headers"],
    )

    assert response.status_code == 200
    members = response.json()
    assert isinstance(members, list)
    assert len(members) >= 2
    assert all("user_id" in member for member in members)
    assert all("user_email" in member for member in members)


def test_get_invite_code_returns_code(client, created_group, auth_user):
    response = client.get(
        f"/groups/{created_group['id']}/members/invite",
        headers=auth_user["headers"],
    )

    assert response.status_code == 200
    data = response.json()
    assert data["invite_code"] == created_group["invite_code"]


def test_add_member_requires_user_id_or_email(client, created_group, auth_user):
    response = client.post(
        f"/groups/{created_group['id']}/members",
        json={},
        headers=auth_user["headers"],
    )

    assert response.status_code == 400
    assert "Provide either user_id or email" in response.json()["detail"]


def test_add_member_by_user_id_returns_member_row(client, created_group, auth_user, second_user):
    response = client.post(
        f"/groups/{created_group['id']}/members",
        json={"user_id": second_user["user"]["id"]},
        headers=auth_user["headers"],
    )

    assert response.status_code == 201
    data = response.json()
    assert data["group_id"] == created_group["id"]
    assert data["user_id"] == second_user["user"]["id"]
    assert data["user_email"] == second_user["user"]["email"]


def test_remove_member_returns_204(client, group_with_two_members):
    group_id = group_with_two_members["group"]["id"]
    member_user_id = group_with_two_members["member"]["user"]["id"]

    response = client.delete(
        f"/groups/{group_id}/members/{member_user_id}",
        headers=group_with_two_members["owner"]["headers"],
    )

    assert response.status_code == 204


def test_get_members_for_nonexistent_group_returns_404(client, auth_user):
    response = client.get(
        f"/groups/{uuid.uuid4()}/members",
        headers=auth_user["headers"],
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Group not found"
