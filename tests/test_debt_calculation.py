import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pytest
from domain import User

from domains.expense.repository import ExpenseRepository
from domains.expense.service import ExpenseService
from domains.group.repository import GroupRepository
from domains.group.service import GroupService


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


@pytest.fixture
def group_with_users(group_service, user_alice, user_bob, user_charlie):
    group = group_service.create_group("Test Group", "USD", user_alice)
    group_service.invite_to_group(group.id, user_bob)
    group_service.invite_to_group(group.id, user_charlie)
    return group


class TestDebtCalculation:
    def test_calculate_debts_single_expense(
        self, expense_service, group_with_users, user_alice, user_bob, user_charlie
    ):

        expense_service.create_expense(
            group_id=group_with_users.id,
            amount=30.0,
            payer=user_alice,
            debtors={user_alice, user_bob, user_charlie},
        )

        debts = expense_service.calculate_debts(group_with_users.id)

        assert debts[(user_bob, user_alice)] == 10.0
        assert debts[(user_charlie, user_alice)] == 10.0
        assert len(debts) == 2

    def test_calculate_debts_multiple_expenses(
        self, expense_service, group_with_users, user_alice, user_bob, user_charlie
    ):

        expense_service.create_expense(
            group_id=group_with_users.id,
            amount=30.0,
            payer=user_alice,
            debtors={user_alice, user_bob, user_charlie},
        )

        expense_service.create_expense(
            group_id=group_with_users.id,
            amount=60.0,
            payer=user_bob,
            debtors={user_alice, user_bob, user_charlie},
        )

        expense_service.create_expense(
            group_id=group_with_users.id,
            amount=15.0,
            payer=user_charlie,
            debtors={user_alice, user_bob, user_charlie},
        )

        debts = expense_service.calculate_debts(group_with_users.id)

        assert (user_alice, user_bob) in debts or (user_bob, user_alice) in debts

    def test_calculate_debts_with_netting(
        self, expense_service, group_with_users, user_alice, user_bob
    ):

        expense_service.create_expense(
            group_id=group_with_users.id,
            amount=30.0,
            payer=user_alice,
            debtors={user_alice, user_bob},
        )

        expense_service.create_expense(
            group_id=group_with_users.id,
            amount=10.0,
            payer=user_bob,
            debtors={user_alice, user_bob},
        )

        debts = expense_service.calculate_debts(group_with_users.id)

        assert debts[(user_bob, user_alice)] == 10.0


class TestSettlement:
    def test_settle_up_full_debt(
        self, expense_service, group_with_users, user_alice, user_bob, user_charlie
    ):

        expense_service.create_expense(
            group_id=group_with_users.id,
            amount=60.0,
            payer=user_alice,
            debtors={user_alice, user_bob, user_charlie},
        )

        settlement = expense_service.settle_up(
            group_id=group_with_users.id, payer=user_bob, payee=user_alice, amount=20.0
        )

        assert settlement.amount == 20.0
        assert settlement.payer == user_bob
        assert user_alice in settlement.debtors

        debts = expense_service.calculate_debts(group_with_users.id)
        assert (user_bob, user_alice) not in debts

        assert debts[(user_charlie, user_alice)] == 20.0

    def test_settle_up_partial_debt(
        self, expense_service, group_with_users, user_alice, user_bob, user_charlie
    ):

        expense_service.create_expense(
            group_id=group_with_users.id,
            amount=60.0,
            payer=user_alice,
            debtors={user_alice, user_bob, user_charlie},
        )

        expense_service.settle_up(
            group_id=group_with_users.id, payer=user_bob, payee=user_alice, amount=10.0
        )

        debts = expense_service.calculate_debts(group_with_users.id)

        assert debts[(user_bob, user_alice)] == 10.0

    def test_settle_up_no_debt_raises_error(
        self, expense_service, group_with_users, user_alice, user_bob
    ):

        with pytest.raises(ValueError, match="does not owe"):
            expense_service.settle_up(
                group_id=group_with_users.id, payer=user_bob, payee=user_alice, amount=20.0
            )

    def test_settle_up_exceeds_debt_raises_error(
        self, expense_service, group_with_users, user_alice, user_bob, user_charlie
    ):

        expense_service.create_expense(
            group_id=group_with_users.id,
            amount=30.0,
            payer=user_alice,
            debtors={user_alice, user_bob, user_charlie},
        )

        with pytest.raises(ValueError, match="exceeds debt"):
            expense_service.settle_up(
                group_id=group_with_users.id, payer=user_bob, payee=user_alice, amount=50.0
            )


class TestSettlementPlan:
    def test_get_settlement_plan_simple(
        self, expense_service, group_with_users, user_alice, user_bob, user_charlie
    ):

        expense_service.create_expense(
            group_id=group_with_users.id,
            amount=60.0,
            payer=user_alice,
            debtors={user_alice, user_bob, user_charlie},
        )

        plan = expense_service.get_settlement_plan(group_with_users.id)

        assert len(plan) == 2
        assert (user_bob, user_alice, 20.0) in plan
        assert (user_charlie, user_alice, 20.0) in plan

    def test_circular_debt_simplification(
        self, expense_service, group_with_users, user_alice, user_bob, user_charlie
    ):

        expense_service.create_expense(
            group_id=group_with_users.id, amount=10.0, payer=user_alice, debtors={user_bob}
        )

        expense_service.create_expense(
            group_id=group_with_users.id, amount=10.0, payer=user_bob, debtors={user_charlie}
        )

        expense_service.create_expense(
            group_id=group_with_users.id, amount=10.0, payer=user_charlie, debtors={user_alice}
        )

        plan = expense_service.get_settlement_plan(group_with_users.id)
        assert len(plan) == 0
