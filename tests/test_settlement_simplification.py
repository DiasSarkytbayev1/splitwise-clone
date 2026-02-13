import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from domain import User, Group, Expense

import pytest
from domain import User, Settlement, SettlementPlan
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


def balances_are_zero_after_plan(plan, raw_debts):
    net = {}
    for (debtor, creditor), amount in raw_debts.items():
        net[debtor] = net.get(debtor, 0.0) - amount
        net[creditor] = net.get(creditor, 0.0) + amount
    for debtor, creditor, amount in plan:
        net[debtor] = net.get(debtor, 0.0) + amount
        net[creditor] = net.get(creditor, 0.0) - amount
    return all(abs(v) < 0.01 for v in net.values())

class TestCircularDebt:

    def test_three_way_circular_cancels_to_zero(
        self, group_service, expense_service, user_alice, user_bob, user_charlie
    ):
        group = group_service.create_group("Trip", "USD", user_alice)
        group_service.invite_to_group(group.id, user_bob)
        group_service.invite_to_group(group.id, user_charlie)

        expense_service.create_expense(group.id, 10.0, user_alice,   {user_bob})
        expense_service.create_expense(group.id, 10.0, user_bob,     {user_charlie})
        expense_service.create_expense(group.id, 10.0, user_charlie, {user_alice})

        plan = expense_service.get_settlement_plan(group.id)
        assert plan == [], f"Circular debts must cancel to zero, got: {plan}"

    def test_four_way_circular_cancels_to_zero(
        self, group_service, expense_service, user_alice, user_bob, user_charlie, user_dave
    ):
        group = group_service.create_group("Trip", "USD", user_alice)
        for u in [user_bob, user_charlie, user_dave]:
            group_service.invite_to_group(group.id, u)

        expense_service.create_expense(group.id, 10.0, user_alice,   {user_bob})
        expense_service.create_expense(group.id, 10.0, user_bob,     {user_charlie})
        expense_service.create_expense(group.id, 10.0, user_charlie, {user_dave})
        expense_service.create_expense(group.id, 10.0, user_dave,    {user_alice})

        plan = expense_service.get_settlement_plan(group.id)
        assert plan == [], f"4-way circular must cancel: {plan}"

    def test_partial_circular_reduces_to_one_transaction(
        self, group_service, expense_service, user_alice, user_bob, user_charlie
    ):
        group = group_service.create_group("Trip", "USD", user_alice)
        group_service.invite_to_group(group.id, user_bob)
        group_service.invite_to_group(group.id, user_charlie)

        expense_service.create_expense(group.id, 20.0, user_bob,     {user_alice})
        expense_service.create_expense(group.id, 10.0, user_charlie, {user_bob})
        expense_service.create_expense(group.id, 10.0, user_alice,   {user_charlie})

        plan = expense_service.get_settlement_plan(group.id)
        assert len(plan) == 1, f"Expected 1 transaction, got: {plan}"


# ---------------------------------------------------------------------------
# 2. Chain debt → simplifies to direct payment
# ---------------------------------------------------------------------------

class TestChainDebt:

    def test_chain_a_owes_b_owes_c_simplifies_to_a_pays_c(
        self, group_service, expense_service, user_alice, user_bob, user_charlie
    ):
        group = group_service.create_group("Trip", "USD", user_alice)
        group_service.invite_to_group(group.id, user_bob)
        group_service.invite_to_group(group.id, user_charlie)

        expense_service.create_expense(group.id, 15.0, user_bob,     {user_alice})
        expense_service.create_expense(group.id, 15.0, user_charlie, {user_bob})

        plan = expense_service.get_settlement_plan(group.id)

        assert len(plan) == 1, f"Chain must collapse to 1 tx: {plan}"
        debtor, creditor, amount = plan[0]
        assert debtor == user_alice
        assert creditor == user_charlie
        assert abs(amount - 15.0) < 0.01


# ---------------------------------------------------------------------------
# 3. Minimum number of transactions
# ---------------------------------------------------------------------------

class TestMinimumTransactions:

    def test_plan_never_exceeds_n_minus_one_transactions(
        self, group_service, expense_service, user_alice, user_bob, user_charlie
    ):
        group = group_service.create_group("Trip", "USD", user_alice)
        group_service.invite_to_group(group.id, user_bob)
        group_service.invite_to_group(group.id, user_charlie)

        expense_service.create_expense(group.id, 300.0, user_alice,   {user_alice, user_bob, user_charlie})
        expense_service.create_expense(group.id, 60.0,  user_bob,     {user_alice, user_bob, user_charlie})
        expense_service.create_expense(group.id, 90.0,  user_charlie, {user_alice, user_bob, user_charlie})

        plan = expense_service.get_settlement_plan(group.id)
        assert len(plan) <= 2, f"3 members need at most 2 transactions, got {len(plan)}: {plan}"

    def test_plan_fully_settles_all_debts(
        self, group_service, expense_service, user_alice, user_bob, user_charlie, user_dave
    ):
        group = group_service.create_group("Trip", "USD", user_alice)
        for u in [user_bob, user_charlie, user_dave]:
            group_service.invite_to_group(group.id, u)

        expense_service.create_expense(group.id, 400.0, user_alice,   {user_alice, user_bob, user_charlie, user_dave})
        expense_service.create_expense(group.id, 80.0,  user_bob,     {user_alice, user_bob, user_charlie, user_dave})
        expense_service.create_expense(group.id, 120.0, user_charlie, {user_alice, user_bob})

        raw_debts = expense_service.calculate_debts(group.id)
        plan = expense_service.get_settlement_plan(group.id)

        assert balances_are_zero_after_plan(plan, raw_debts)

    def test_no_self_payments_in_plan(
        self, group_service, expense_service, user_alice, user_bob, user_charlie
    ):
        group = group_service.create_group("Trip", "USD", user_alice)
        group_service.invite_to_group(group.id, user_bob)
        group_service.invite_to_group(group.id, user_charlie)

        expense_service.create_expense(group.id, 90.0, user_alice, {user_alice, user_bob, user_charlie})

        plan = expense_service.get_settlement_plan(group.id)
        for debtor, creditor, _ in plan:
            assert debtor != creditor

    def test_all_amounts_are_positive(
        self, group_service, expense_service, user_alice, user_bob, user_charlie
    ):
        group = group_service.create_group("Trip", "USD", user_alice)
        group_service.invite_to_group(group.id, user_bob)
        group_service.invite_to_group(group.id, user_charlie)

        expense_service.create_expense(group.id, 60.0, user_alice, {user_alice, user_bob, user_charlie})

        plan = expense_service.get_settlement_plan(group.id)
        for _, _, amount in plan:
            assert amount > 0



class TestAlreadySettled:

    def test_empty_group_has_empty_plan(
        self, group_service, expense_service, user_alice, user_bob
    ):
        group = group_service.create_group("Trip", "USD", user_alice)
        group_service.invite_to_group(group.id, user_bob)

        plan = expense_service.get_settlement_plan(group.id)
        assert plan == []

    def test_mutual_equal_expenses_cancel(
        self, group_service, expense_service, user_alice, user_bob
    ):
    
        group = group_service.create_group("Trip", "USD", user_alice)
        group_service.invite_to_group(group.id, user_bob)

        expense_service.create_expense(group.id, 50.0, user_alice, {user_bob})
        expense_service.create_expense(group.id, 50.0, user_bob,   {user_alice})

        plan = expense_service.get_settlement_plan(group.id)
        assert plan == []