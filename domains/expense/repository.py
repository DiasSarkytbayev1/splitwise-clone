from typing import Dict, List, Optional

from domain import Expense


class ExpenseRepository:
    def __init__(self):
        self._expenses: Dict[str, Expense] = {}

    def save(self, expense: Expense) -> None:
        self._expenses[expense.id] = expense

    def find_by_id(self, expense_id: str) -> Optional[Expense]:
        return self._expenses.get(expense_id)

    def find_by_group_id(self, group_id: str) -> List[Expense]:
        return [e for e in self._expenses.values() if e.group_id == group_id]
