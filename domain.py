from typing import Set, List
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


@dataclass(frozen=True)
class Settlement:
    payer: User
    payee: User
    amount: float


@dataclass
class SettlementPlan:
    group_id: str
    settlements: List[Settlement] = field(default_factory=list)
