import uuid

from domain import Group, User
from domains.group.repository import GroupRepository
from domains.expense.service import ExpenseService


class GroupService:
    def __init__(self, group_repo: GroupRepository, expense_service: ExpenseService):
        self._repo = group_repo
        self._expense_service = expense_service

    def create_group(self, name: str, currency: str, creator: User) -> Group:
        group_id = str(uuid.uuid4())
        group = Group(id=group_id, name=name, currency=currency)
        group.members.add(creator)
        self._repo.save(group)
        return group

    def invite_to_group(self, group_id: str, user: User) -> Group:
        group = self._get_group_or_raise(group_id)
        group.members.add(user)
        self._repo.save(group)
        return group

    def drop_out_from_group(self, group_id: str, user: User) -> Group:
        group = self._get_group_or_raise(group_id)

        debts = self._expense_service.calculate_debts(group_id)
        for (debtor, creditor), amount in debts.items():
            if (debtor == user or creditor == user) and amount > 0.005:
                raise ValueError(f"User '{user.name}' has unsettled debts.")

        group.members.remove(user)
        self._repo.save(group)
        return group

    def _get_group_or_raise(self, group_id: str) -> Group:
        group = self._repo.find_by_id(group_id)
        if group is None:
            raise ValueError(f"Group with id '{group_id}' not found.")
        return group
