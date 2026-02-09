from typing import Set, List, Dict, Tuple
from dataclasses import dataclass, field


@dataclass
class User:
    name: str

    @staticmethod
    def create(name: str) -> "User":
        return User(name=name)


@dataclass
class Expense:
    amount: float
    payer: User
    debtors: Set[User]

    @staticmethod
    def create(amount: float, payer: User, debtors: Set[User]) -> "Expense":
        if not len(debtors):
            raise ValueError("No debtors. Nobody needs to return money then?")
        return Expense(amount=amount, payer=payer, debtors=debtors)


@dataclass
class Group:
    id: str
    name: str
    currency: str
    members: Set[User] = field(default_factory=set)
    expenses: List[Expense] = field(default_factory=list)

    def add_member(self, user: User):
        self.members.add(user)

    def remove_member(self, user: User):
        self.members.remove(user)

    def add_expense(self, expense: Expense):
        if not expense.debtors.issubset(self.members):
            raise ValueError("All debtors must be group members.")
        self.expenses.append(expense)

    def calculate_debt_matrix(self) -> Dict[Tuple[User, User], float]:
        raise NotImplementedError()

    def settle_up(self) -> List[Tuple[User, User, float]]:
        raise NotImplementedError()
