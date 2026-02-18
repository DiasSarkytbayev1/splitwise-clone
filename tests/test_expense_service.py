import pytest
from domain import User

from domains.expense.repository import ExpenseRepository
from domains.expense.service import ExpenseService
from domains.group.repository import GroupRepository
from domains.group.service import GroupService


@pytest.fixture
def alice():
    return User(id="1", name="Alice Mikhailovna", email="alice@test.com", password="pass")


@pytest.fixture
def bob():
    return User(id="2", name="Bob The Builder", email="bob@builder.com", password="pass")


@pytest.fixture
def charlie():
    return User(id="3", name="Charlie Kirk", email="charlie@kirk.com", password="pass")


@pytest.fixture
def services():
    expense_repo = ExpenseRepository()
    group_repo = GroupRepository()
    expense_service = ExpenseService(expense_repo, group_repo)
    group_service = GroupService(group_repo, expense_service)
    return expense_service, group_service


@pytest.fixture
def group_with_two(services, alice, bob):
    expense_service, group_service = services
    group = group_service.create_group("Test", "USD", alice)
    group_service.invite_to_group(group.id, bob)
    return group, expense_service, group_service


@pytest.fixture
def group_with_three(group_with_two, charlie):
    group, expense_service, group_service = group_with_two
    group_service.invite_to_group(group.id, charlie)
    return group, expense_service, group_service


def test_split_between_two(group_with_two, alice, bob):
    group, expense_service, _ = group_with_two

    expense_service.create_expense(group.id, 100, payer=alice, debtors={alice, bob})
    debts = expense_service.calculate_debts(group.id)

    assert debts[(bob, alice)] == 50.0
    assert (alice, bob) not in debts


def test_split_between_three(group_with_three, alice, bob, charlie):
    group, expense_service, _ = group_with_three

    expense_service.create_expense(group.id, 90, payer=alice, debtors={alice, bob, charlie})
    debts = expense_service.calculate_debts(group.id)

    assert debts[(bob, alice)] == 30.0
    assert debts[(charlie, alice)] == 30.0
    assert (alice, bob) not in debts


def test_payer_in_debtors_does_not_owe_self(group_with_two, alice, bob):
    group, expense_service, _ = group_with_two

    expense_service.create_expense(group.id, 100, payer=alice, debtors={alice, bob})
    debts = expense_service.calculate_debts(group.id)

    for debtor, payer in debts:
        assert debtor != payer


def test_netting_mutual_debts(group_with_two, alice, bob):
    group, expense_service, _ = group_with_two

    expense_service.create_expense(group.id, 100, payer=alice, debtors={alice, bob})
    expense_service.create_expense(group.id, 120, payer=bob, debtors={alice, bob})

    debts = expense_service.calculate_debts(group.id)
    assert debts[(alice, bob)] == 10.0
    assert (bob, alice) not in debts


def test_settlement_plan_three_people(group_with_three, alice, bob, charlie):
    group, expense_service, _ = group_with_three

    expense_service.create_expense(group.id, 90, payer=alice, debtors={alice, bob, charlie})

    settlements = expense_service.get_settlement_plan(group.id)

    total_to_alice = sum(amount for debtor, payer, amount in settlements if payer == alice)
    assert total_to_alice == 60.0
    assert all(payer == alice for _, payer, _ in settlements)


def test_settle_up_clears_debt(group_with_two, alice, bob):
    group, expense_service, _ = group_with_two

    expense_service.create_expense(group.id, 100, payer=alice, debtors={alice, bob})
    expense_service.settle_up(group.id, payer=bob, payee=alice, amount=50.0)

    debts = expense_service.calculate_debts(group.id)
    assert len(debts) == 0


def test_drop_out_from_expense(group_with_three, alice, bob, charlie):
    group, expense_service, _ = group_with_three

    expense = expense_service.create_expense(
        group.id, 90, payer=alice, debtors={alice, bob, charlie}
    )
    expense_service.drop_out_from_expense(expense.id, charlie)

    debts = expense_service.calculate_debts(group.id)

    assert debts[(bob, alice)] == 45.0
    assert (charlie, alice) not in debts


def test_cannot_leave_group_with_debts(group_with_two, alice, bob):
    group, _, group_service = group_with_two

    group_service._expense_service.create_expense(group.id, 100, payer=alice, debtors={alice, bob})

    with pytest.raises(ValueError, match="unsettled debts"):
        group_service.drop_out_from_group(group.id, bob)
