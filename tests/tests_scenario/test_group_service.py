import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
import pytest
from domain import User, Group
from domains.group.repository import GroupRepository
from domains.group.service import GroupService
from domains.expense.repository import ExpenseRepository
from domains.expense.service import ExpenseService


@pytest.fixture
def user_alice():
    return User(id="1", name="Alice", email="alice@test.com", password="pass123")


@pytest.fixture
def user_bob():
    return User(id="2", name="Bob", email="bob@test.com", password="pass456")


@pytest.fixture
def user_charlie():
    return User(id="3", name="Charlie", email="charlie@test.com", password="pass789")


@pytest.fixture
def group_repo():
    return GroupRepository()


@pytest.fixture
def expense_repo():
    return ExpenseRepository()


@pytest.fixture
def expense_service(expense_repo, group_repo):
    return ExpenseService(expense_repo, group_repo)


@pytest.fixture
def group_service(group_repo, expense_service):
    return GroupService(group_repo, expense_service)


class TestGroupCreation:
    def test_create_group_basic(self, group_service, user_alice):
        group = group_service.create_group("Weekend Trip", "USD", user_alice)
        
        assert group.name == "Weekend Trip"
        assert group.currency == "USD"
        assert user_alice in group.members
        assert len(group.members) == 1
        assert group.id is not None
    
    def test_create_multiple_groups(self, group_service, user_alice):
        group1 = group_service.create_group("Trip 1", "USD", user_alice)
        group2 = group_service.create_group("Trip 2", "EUR", user_alice)
        
        assert group1.id != group2.id
        assert group1.name == "Trip 1"
        assert group2.name == "Trip 2"


class TestInviteToGroup:
    def test_invite_user_to_group(self, group_service, user_alice, user_bob):
        group = group_service.create_group("Weekend Trip", "USD", user_alice)
        updated_group = group_service.invite_to_group(group.id, user_bob)
        
        assert user_bob in updated_group.members
        assert user_alice in updated_group.members
        assert len(updated_group.members) == 2
    
    def test_invite_multiple_users(self, group_service, user_alice, user_bob, user_charlie):
        group = group_service.create_group("Group Event", "USD", user_alice)
        group_service.invite_to_group(group.id, user_bob)
        updated_group = group_service.invite_to_group(group.id, user_charlie)
        
        assert len(updated_group.members) == 3
        assert user_alice in updated_group.members
        assert user_bob in updated_group.members
        assert user_charlie in updated_group.members
    
    def test_invite_to_nonexistent_group_raises_error(self, group_service, user_bob):
        with pytest.raises(ValueError, match="Group with id 'fake-id' not found"):
            group_service.invite_to_group("fake-id", user_bob)


class TestDropOutFromGroup:
    def test_drop_out_with_zero_balance(self, group_service, user_alice, user_bob):
        group = group_service.create_group("Weekend Trip", "USD", user_alice)
        group_service.invite_to_group(group.id, user_bob)
        
        updated_group = group_service.drop_out_from_group(group.id, user_bob)
        
        assert user_bob not in updated_group.members
        assert user_alice in updated_group.members
        assert len(updated_group.members) == 1
    
    def test_drop_out_from_nonexistent_group_raises_error(self, group_service, user_bob):
        with pytest.raises(ValueError, match="Group with id 'fake-id' not found"):
            group_service.drop_out_from_group("fake-id", user_bob)


class TestEdgeCases:
    def test_invite_same_user_twice(self, group_service, user_alice, user_bob):
        group = group_service.create_group("Test Group", "USD", user_alice)
        group_service.invite_to_group(group.id, user_bob)
        updated_group = group_service.invite_to_group(group.id, user_bob)
        
        assert len(updated_group.members) == 2  # Alice + Bob (один раз)
