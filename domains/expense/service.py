import uuid
from typing import Dict, List, Optional, Set, Tuple

from domain import User, Expense
from domains.expense.repository import ExpenseRepository
from domains.group.repository import GroupRepository


class ExpenseService:
    def __init__(self, expense_repo: ExpenseRepository, group_repo: GroupRepository):
        self._expense_repo = expense_repo
        self._group_repo = group_repo

    def create_expense(
        self,
        group_id: str,
        amount: float,
        payer: User,
        debtors: Optional[Set[User]] = None,
    ) -> Expense:
        group = self._get_group_or_raise(group_id)

        if debtors is None:
            debtors = set(group.members)

        if not debtors.issubset(group.members):
            raise ValueError("All debtors must be group members.")

        if not debtors:
            raise ValueError("No debtors. Nobody needs to return money then?")

        expense = Expense(
            id=str(uuid.uuid4()),
            group_id=group_id,
            amount=amount,
            payer=payer,
            debtors=debtors,
        )
        self._expense_repo.save(expense)
        return expense

    def calculate_debts(self, group_id: str) -> Dict[Tuple[User, User], float]:
        self._get_group_or_raise(group_id)
        expenses = self._expense_repo.find_by_group_id(group_id)
        return self._calculate_debt_matrix(expenses)

    def get_settlement_plan(self, group_id: str) -> List[Tuple[User, User, float]]:
        self._get_group_or_raise(group_id)
        expenses = self._expense_repo.find_by_group_id(group_id)
        return self._get_settlements(expenses)

    def settle_up(
        self, group_id: str, payer: User, payee: User, amount: float
    ) -> Expense:
        self._get_group_or_raise(group_id)
        expenses = self._expense_repo.find_by_group_id(group_id)
        debt_matrix = self._calculate_debt_matrix(expenses)

        current_debt = debt_matrix.get((payer, payee), 0.0)

        if current_debt < 0.005:
            raise ValueError(f"'{payer.name}' does not owe '{payee.name}' anything.")

        if amount > current_debt + 0.005:
            raise ValueError(
                f"Settlement amount {amount} exceeds debt of {current_debt}."
            )

        settlement = Expense(
            id=str(uuid.uuid4()),
            group_id=group_id,
            amount=amount,
            payer=payer,
            debtors={payee},
        )
        self._expense_repo.save(settlement)
        return settlement

    def drop_out_from_expense(self, expense_id: str, user: User) -> Expense:
        expense = self._expense_repo.find_by_id(expense_id)
        if expense is None:
            raise ValueError(f"Expense with id '{expense_id}' not found.")
        remaining = expense.debtors - {user}
        if not remaining:
            raise ValueError("Cannot remove the last debtor from an expense.")
        expense.debtors = remaining
        self._expense_repo.save(expense)
        return expense

    def _get_group_or_raise(self, group_id: str):
        group = self._group_repo.find_by_id(group_id)
        if group is None:
            raise ValueError(f"Group with id '{group_id}' not found.")
        return group

    @staticmethod
    def _calculate_debt_matrix(
        expenses: List[Expense],
    ) -> Dict[Tuple[User, User], float]:
        raw_debts: Dict[Tuple[User, User], float] = {}

        for expense in expenses:
            share = expense.amount / len(expense.debtors)
            for debtor in expense.debtors:
                if debtor == expense.payer:
                    continue
                key = (debtor, expense.payer)
                raw_debts[key] = raw_debts.get(key, 0.0) + share

        netted: Dict[Tuple[User, User], float] = {}
        processed: set = set()

        for (debtor, creditor), amount in raw_debts.items():
            pair = frozenset({debtor, creditor})
            if pair in processed:
                continue
            processed.add(pair)

            reverse_amount = raw_debts.get((creditor, debtor), 0.0)
            net = amount - reverse_amount

            if net > 0:
                netted[(debtor, creditor)] = round(net, 2)
            elif net < 0:
                netted[(creditor, debtor)] = round(-net, 2)

        return netted

    @staticmethod
    def _get_settlements(expenses: List[Expense]) -> List[Tuple[User, User, float]]:
        debt_matrix = ExpenseService._calculate_debt_matrix(expenses)
        balances: Dict[User, float] = {}

        for (debtor, creditor), amount in debt_matrix.items():
            balances[debtor] = balances.get(debtor, 0.0) - amount
            balances[creditor] = balances.get(creditor, 0.0) + amount

        debtors_list = []
        creditors_list = []
        for user, balance in balances.items():
            if balance < -0.005:
                debtors_list.append([user, -balance])
            elif balance > 0.005:
                creditors_list.append([user, balance])

        debtors_list.sort(key=lambda x: x[1], reverse=True)
        creditors_list.sort(key=lambda x: x[1], reverse=True)

        settlements = []
        i, j = 0, 0
        while i < len(debtors_list) and j < len(creditors_list):
            debtor, debt_amount = debtors_list[i]
            creditor, credit_amount = creditors_list[j]

            transfer = round(min(debt_amount, credit_amount), 2)
            if transfer > 0:
                settlements.append((debtor, creditor, transfer))

            debtors_list[i][1] = round(debt_amount - transfer, 2)
            creditors_list[j][1] = round(credit_amount - transfer, 2)

            if debtors_list[i][1] < 0.005:
                i += 1
            if creditors_list[j][1] < 0.005:
                j += 1

        return settlements
