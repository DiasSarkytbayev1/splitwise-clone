import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
import pytest
from domain import User
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


class TestDineAndDash:

    def test_cannot_drop_out_with_unsettled_debt(
        self, group_service, expense_service, user_alice, user_bob, user_charlie
    ):

        group = group_service.create_group("Dinner Group", "USD", user_alice)
        group_service.invite_to_group(group.id, user_bob)
        group_service.invite_to_group(group.id, user_charlie)
        
       
        expense_service.create_expense(
            group_id=group.id,
            amount=120.0,
            payer=user_alice,
            debtors={user_alice, user_bob, user_charlie}
        )
        
       
        with pytest.raises(ValueError, match="has unsettled debts"):
            group_service.drop_out_from_group(group.id, user_bob)
    
    def test_can_drop_out_after_settling_debt(
        self, group_service, expense_service, user_alice, user_bob, user_charlie
    ):

        group = group_service.create_group("Dinner Group", "USD", user_alice)
        group_service.invite_to_group(group.id, user_bob)
        group_service.invite_to_group(group.id, user_charlie)
        
        expense_service.create_expense(
            group_id=group.id,
            amount=120.0,
            payer=user_alice,
            debtors={user_alice, user_bob, user_charlie}
        )
        
     
        expense_service.settle_up(
            group_id=group.id,
            payer=user_bob,
            payee=user_alice,
            amount=40.0
        )
        
        
        updated_group = group_service.drop_out_from_group(group.id, user_bob)
        assert user_bob not in updated_group.members


class TestSoloSurvivor:

    def test_last_person_in_group_can_add_expense(
        self, group_service, expense_service, user_alice
    ):

        group = group_service.create_group("Solo Trip", "USD", user_alice)
        
        expense = expense_service.create_expense(
            group_id=group.id,
            amount=10.0,
            payer=user_alice,
            debtors={user_alice}
        )
        
        assert expense.amount == 10.0
        
        debts = expense_service.calculate_debts(group.id)
        assert len(debts) == 0  # Нет долгов, так как Alice платит сама себе


class TestDropOutFromExpense:

    def test_drop_out_from_expense_success(
        self, group_service, expense_service, user_alice, user_bob, user_charlie
    ):

        group = group_service.create_group("Test Group", "USD", user_alice)
        group_service.invite_to_group(group.id, user_bob)
        group_service.invite_to_group(group.id, user_charlie)
        
        expense = expense_service.create_expense(
            group_id=group.id,
            amount=90.0,
            payer=user_alice,
            debtors={user_alice, user_bob, user_charlie}
        )
        
        
        updated_expense = expense_service.drop_out_from_expense(expense.id, user_charlie)
        
        assert user_charlie not in updated_expense.debtors
        assert len(updated_expense.debtors) == 2
    
    def test_cannot_remove_last_debtor(
        self, group_service, expense_service, user_alice, user_bob
    ):
        group = group_service.create_group("Test Group", "USD", user_alice)
        group_service.invite_to_group(group.id, user_bob)
        
        expense = expense_service.create_expense(
            group_id=group.id,
            amount=50.0,
            payer=user_alice,
            debtors={user_bob}
        )
        
        with pytest.raises(ValueError, match="Cannot remove the last debtor"):
            expense_service.drop_out_from_expense(expense.id, user_bob)
    
    def test_drop_out_from_nonexistent_expense(
        self, expense_service, user_bob
    ):
 
        with pytest.raises(ValueError, match="Expense with id 'fake-expense-id' not found"):
            expense_service.drop_out_from_expense("fake-expense-id", user_bob)


class TestLateJoiner:

    def test_late_joiner_not_in_old_expenses(
        self, group_service, expense_service, user_alice, user_bob, user_charlie, user_dave
    ):

        group = group_service.create_group("Dinner", "USD", user_alice)
        group_service.invite_to_group(group.id, user_bob)
        group_service.invite_to_group(group.id, user_charlie)
        group_service.invite_to_group(group.id, user_dave)
        
    
        expense = expense_service.create_expense(
            group_id=group.id,
            amount=100.0,
            payer=user_alice,
            debtors={user_alice, user_bob, user_charlie, user_dave}
        )
        
    
        new_user = User(id="5", name="Eve", email="eve@test.com", password="pass111")
        group_service.invite_to_group(group.id, new_user)
        
        assert new_user not in expense.debtors
        
        new_expense = expense_service.create_expense(
            group_id=group.id,
            amount=50.0,
            payer=user_bob,
            debtors=None  
        )
        
        assert new_user in new_expense.debtors


class TestMultipleExpensesComplexScenario:
    
    def test_complex_scenario_weekend_trip(
        self, group_service, expense_service, user_alice, user_bob, user_charlie
    ):

        group = group_service.create_group("Weekend Trip", "USD", user_alice)
        group_service.invite_to_group(group.id, user_bob)
        group_service.invite_to_group(group.id, user_charlie)
        

        expense_service.create_expense(
            group_id=group.id,
            amount=300.0,
            payer=user_alice,
            debtors={user_alice, user_bob, user_charlie}
        )
        
        expense_service.create_expense(
            group_id=group.id,
            amount=60.0,
            payer=user_bob,
            debtors={user_alice, user_bob, user_charlie}
        )
        

        expense_service.create_expense(
            group_id=group.id,
            amount=90.0,
            payer=user_charlie,
            debtors={user_alice, user_bob, user_charlie}
        )
        

        expense_service.create_expense(
            group_id=group.id,
            amount=150.0,
            payer=user_alice,
            debtors={user_alice, user_bob}
        )
        

        debts = expense_service.calculate_debts(group.id)
        

        assert len(debts) > 0
        

        plan = expense_service.get_settlement_plan(group.id)
        assert len(plan) > 0


class TestZeroAmountEdgeCases:

    
    def test_very_small_amounts_handling(
        self, group_service, expense_service, user_alice, user_bob
    ):

        group = group_service.create_group("Test", "USD", user_alice)
        group_service.invite_to_group(group.id, user_bob)
        

        expense_service.create_expense(
            group_id=group.id,
            amount=0.01,
            payer=user_alice,
            debtors={user_alice, user_bob}
        )
        
        debts = expense_service.calculate_debts(group.id)
        

        assert (user_bob, user_alice) in debts or len(debts) == 0
