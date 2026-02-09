from typing import Set
from dataclasses import dataclass, field


@dataclass(frozen=True)
class User:
    id: str
    name: str
    email: str
    password: str


@dataclass
class Expense:
    id: str
    group_id: str
    amount: float
    payer: User
    debtors: Set[User]


@dataclass
class Group:
    id: str
    name: str
    currency: str
    members: Set[User] = field(default_factory=set)
