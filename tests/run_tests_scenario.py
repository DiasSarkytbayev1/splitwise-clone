import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from domain import User, Group, Expense
from domains.group.repository import GroupRepository
from domains.group.service import GroupService
from domains.expense.repository import ExpenseRepository
from domains.expense.service import ExpenseService


def test_create_group():
    print("Test: Create Group")
    
    user_alice = User(id="1", name="Alice", email="alice@test.com", password="pass123")
    
    group_repo = GroupRepository()
    expense_repo = ExpenseRepository()
    expense_service = ExpenseService(expense_repo, group_repo)
    group_service = GroupService(group_repo, expense_service)
    
    group = group_service.create_group("Weekend Trip", "USD", user_alice)
    
    assert group.name == "Weekend Trip", "Group name must be'Weekend Trip'"
    assert group.currency == "USD", "Currency must be 'USD'"
    assert user_alice in group.members, "Alice bust members"
    assert len(group.members) == 1, "Must be one person"
    
    print("PASSED: Group successfully created")
    return True


def test_invite_to_group():
    print("\n Test: Invite to Group")
    
    user_alice = User(id="1", name="Alice", email="alice@test.com", password="pass123")
    user_bob = User(id="2", name="Bob", email="bob@test.com", password="pass456")
    
    group_repo = GroupRepository()
    expense_repo = ExpenseRepository()
    expense_service = ExpenseService(expense_repo, group_repo)
    group_service = GroupService(group_repo, expense_service)
    
    group = group_service.create_group("Weekend Trip", "USD", user_alice)
    updated_group = group_service.invite_to_group(group.id, user_bob)
    
    assert user_bob in updated_group.members, "Bob must be in members"
    assert len(updated_group.members) == 2, "In group must be 2 users"
    
    print("PASSED: User successfully invited")
    return True


def test_create_expense_equal_split():
    print("\n Test: Create Expense with Equal Split")
    
    user_alice = User(id="1", name="Alice", email="alice@test.com", password="pass123")
    user_bob = User(id="2", name="Bob", email="bob@test.com", password="pass456")
    user_charlie = User(id="3", name="Charlie", email="charlie@test.com", password="pass789")
    
    group_repo = GroupRepository()
    expense_repo = ExpenseRepository()
    expense_service = ExpenseService(expense_repo, group_repo)
    group_service = GroupService(group_repo, expense_service)
    
    
    group = group_service.create_group("Pizza Night", "USD", user_alice)
    group_service.invite_to_group(group.id, user_bob)
    group_service.invite_to_group(group.id, user_charlie)
    
    
    expense = expense_service.create_expense(
        group_id=group.id,
        amount=30.0,
        payer=user_alice,
        debtors={user_alice, user_bob, user_charlie}
    )
    
    assert expense.amount == 30.0, "Amount must be 30.0"
    assert expense.payer == user_alice, "Payer must be Alice"
    assert len(expense.debtors) == 3, "Must be 3 debtors"
    
    
    debts = expense_service.calculate_debts(group.id)
    assert debts[(user_bob, user_alice)] == 10.0, "Bob barrow Alice $10"
    assert debts[(user_charlie, user_alice)] == 10.0, "Charlie barrow Alice $10"
    
    print("PASSED: Expense created and debts calculated correctly")
    print(f"   - Bob owes Alice: ${debts[(user_bob, user_alice)]}")
    print(f"   - Charlie owes Alice: ${debts[(user_charlie, user_alice)]}")
    return True


def test_settle_up():

    print("\n Test: Settle Up")
    
    user_alice = User(id="1", name="Alice", email="alice@test.com", password="pass123")
    user_bob = User(id="2", name="Bob", email="bob@test.com", password="pass456")
    
    group_repo = GroupRepository()
    expense_repo = ExpenseRepository()
    expense_service = ExpenseService(expense_repo, group_repo)
    group_service = GroupService(group_repo, expense_service)
    
    
    group = group_service.create_group("Test Group", "USD", user_alice)
    group_service.invite_to_group(group.id, user_bob)
    
    
    expense_service.create_expense(
        group_id=group.id,
        amount=60.0,
        payer=user_alice,
        debtors={user_alice, user_bob}
    )
    
    
    debts_before = expense_service.calculate_debts(group.id)
    print(f"   Before settlement: Bob owes Alice ${debts_before[(user_bob, user_alice)]}")
    
    
    settlement = expense_service.settle_up(
        group_id=group.id,
        payer=user_bob,
        payee=user_alice,
        amount=30.0
    )
    
    assert settlement.amount == 30.0, "Settlement amount must be 30.0"
    
   
    debts_after = expense_service.calculate_debts(group.id)
    assert (user_bob, user_alice) not in debts_after, "Bob is not barrow Alice"
    
    print("PASSED: Debt successfully settled")
    print(f"   After settlement: Bob's debt cleared")
    return True


def test_cannot_drop_out_with_debt():
    print("\n Test: Cannot Drop Out with Unsettled Debt")
    
    user_alice = User(id="1", name="Alice", email="alice@test.com", password="pass123")
    user_bob = User(id="2", name="Bob", email="bob@test.com", password="pass456")
    
    group_repo = GroupRepository()
    expense_repo = ExpenseRepository()
    expense_service = ExpenseService(expense_repo, group_repo)
    group_service = GroupService(group_repo, expense_service)
    
    
    group = group_service.create_group("Test Group", "USD", user_alice)
    group_service.invite_to_group(group.id, user_bob)
    
    
    expense_service.create_expense(
        group_id=group.id,
        amount=100.0,
        payer=user_alice,
        debtors={user_alice, user_bob}
    )
    
    
    try:
        group_service.drop_out_from_group(group.id, user_bob)
        print("FAILED: Should have raised ValueError")
        return False
    except ValueError as e:
        if "unsettled debts" in str(e):
            print(" PASSED: Correctly prevented drop out with debts")
            print(f"   Error message: {e}")
            return True
        else:
            print(f" FAILED: Wrong error message: {e}")
            return False


def test_circular_debt_simplification():
    print("\n Test: Circular Debt Simplification")
    
    user_alice = User(id="1", name="Alice", email="alice@test.com", password="pass123")
    user_bob = User(id="2", name="Bob", email="bob@test.com", password="pass456")
    user_charlie = User(id="3", name="Charlie", email="charlie@test.com", password="pass789")
    
    group_repo = GroupRepository()
    expense_repo = ExpenseRepository()
    expense_service = ExpenseService(expense_repo, group_repo)
    group_service = GroupService(group_repo, expense_service)
    
    
    group = group_service.create_group("Test Group", "USD", user_alice)
    group_service.invite_to_group(group.id, user_bob)
    group_service.invite_to_group(group.id, user_charlie)
    
    expense_service.create_expense(
        group_id=group.id,
        amount=10.0,
        payer=user_alice,
        debtors={user_bob}
    )
    
    
    expense_service.create_expense(
        group_id=group.id,
        amount=10.0,
        payer=user_bob,
        debtors={user_charlie}
    )
    
    
    expense_service.create_expense(
        group_id=group.id,
        amount=10.0,
        payer=user_charlie,
        debtors={user_alice}
    )
    
    
    debts = expense_service.calculate_debts(group.id)
    
    if len(debts) == 0:
        print(" PASSED: Circular debts correctly simplified to zero")
        return True
    else:
        print(f" FAILED: Expected 0 debts, got {len(debts)}")
        print(f"   Debts: {debts}")
        return False


def run_all_tests():
    print("=" * 60)
    print(" Running Splitwise Clone Test Suite")
    print("=" * 60)
    
    tests = [
        test_create_group,
        test_invite_to_group,
        test_create_expense_equal_split,
        test_settle_up,
        test_cannot_drop_out_with_debt,
        test_circular_debt_simplification,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f" FAILED with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print(f" Test Results: {sum(results)}/{len(results)} passed")
    print("=" * 60)
    
    if all(results):
        print("All tests passed!")
    else:
        print("Some tests failed")
    
    return all(results)


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
