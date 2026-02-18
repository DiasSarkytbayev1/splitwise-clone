from domain import Expense


class ExpenseRepository:
    def __init__(self) -> None:
        self._expenses: dict[str, Expense] = {}

    def save(self, expense: Expense) -> None:
        self._expenses[expense.id] = expense

    def find_by_id(self, expense_id: str) -> Expense | None:
        return self._expenses.get(expense_id)

    def find_by_group_id(self, group_id: str) -> list[Expense]:
        return [e for e in self._expenses.values() if e.group_id == group_id]
