import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest
from domain import User, Expense
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
def user_dave():
    return User(id="4", name="Dave", email="dave@test.com", password="pass000")


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


@pytest.fixture
def group_with_three_users(group_service, user_alice, user_bob, user_charlie):
    group = group_service.create_group("Pizza Night", "USD", user_alice)
    group_service.invite_to_group(group.id, user_bob)
    group_service.invite_to_group(group.id, user_charlie)
    return group


class TestExpenseCreation:
    def test_create_expense_equal_split(
        self, expense_service, group_with_three_users, user_alice, user_bob, user_charlie
    ):
        expense = expense_service.create_expense(
            group_id=group_with_three_users.id,
            amount=30.0,
            payer=user_alice,
            debtors={user_alice, user_bob, user_charlie}
        )
        
        assert expense.amount == 30.0
        assert expense.payer == user_alice
        assert len(expense.debtors) == 3
        
        # Проверяем расчет долгов
        debts = expense_service.calculate_debts(group_with_three_users.id)
        assert debts[(user_bob, user_alice)] == 10.0
        assert debts[(user_charlie, user_alice)] == 10.0
    
    def test_create_expense_auto_split_all_members(
        self, expense_service, group_with_three_users, user_alice
    ):

        expense = expense_service.create_expense(
            group_id=group_with_three_users.id,
            amount=60.0,
            payer=user_alice,
            debtors=None  # Автоматически все члены
        )
        
        assert len(expense.debtors) == 3
    
    def test_create_expense_in_nonexistent_group_raises_error(
        self, expense_service, user_alice
    ):

        with pytest.raises(ValueError, match="Group with id 'fake-group-id' not found"):
            expense_service.create_expense(
                group_id="fake-group-id",
                amount=50.0,
                payer=user_alice
            )


class TestCustomSplit:

    def test_custom_split_excluded_member(
        self, expense_service, group_service, user_alice, user_bob, user_charlie, user_dave
    ):
        group = group_service.create_group("Beer Night", "USD", user_alice)
        group_service.invite_to_group(group.id, user_bob)
        group_service.invite_to_group(group.id, user_charlie)
        group_service.invite_to_group(group.id, user_dave)
        
        # Alice платит $90, но Dave не пьет - исключаем его
        expense = expense_service.create_expense(
            group_id=group.id,
            amount=90.0,
            payer=user_alice,
            debtors={user_alice, user_bob, user_charlie}  # Dave исключен
        )
        
        assert user_dave not in expense.debtors
        assert len(expense.debtors) == 3
        
        debts = expense_service.calculate_debts(group.id)
        assert debts[(user_bob, user_alice)] == 30.0
        assert debts[(user_charlie, user_alice)] == 30.0
    
    def test_custom_split_only_two_people(
        self, expense_service, group_with_three_users, user_alice, user_bob
    ):
        expense = expense_service.create_expense(
            group_id=group_with_three_users.id,
            amount=100.0,
            payer=user_alice,
            debtors={user_alice, user_bob}  # Только Alice и Bob
        )
        
        assert len(expense.debtors) == 2
        
        debts = expense_service.calculate_debts(group_with_three_users.id)
        assert debts[(user_bob, user_alice)] == 50.0


class TestValidation:

    def test_create_expense_with_non_member_debtor_raises_error(
        self, expense_service, group_with_three_users, user_alice, user_dave
    ):
        with pytest.raises(ValueError, match="All debtors must be group members"):
            expense_service.create_expense(
                group_id=group_with_three_users.id,
                amount=50.0,
                payer=user_alice,
                debtors={user_alice, user_dave}  # Dave не в группе
            )
    
    def test_create_expense_with_empty_debtors_raises_error(
        self, expense_service, group_with_three_users, user_alice
    ):
        with pytest.raises(ValueError, match="No debtors"):
            expense_service.create_expense(
                group_id=group_with_three_users.id,
                amount=50.0,
                payer=user_alice,
                debtors=set()  # Пустой set
            )


class TestPennyRounding:
    def test_split_with_rounding(
        self, expense_service, group_with_three_users, user_alice, user_bob, user_charlie
    ):

        expense = expense_service.create_expense(
            group_id=group_with_three_users.id,
            amount=10.0,
            payer=user_alice,
            debtors={user_alice, user_bob, user_charlie}
        )
        

        debts = expense_service.calculate_debts(group_with_three_users.id)
        

        assert abs(debts[(user_bob, user_alice)] - 3.33) < 0.01
        assert abs(debts[(user_charlie, user_alice)] - 3.33) < 0.01
