from domain import Group


class GroupRepository:
    def __init__(self) -> None:
        self._groups: dict[str, Group] = {}

    def save(self, group: Group) -> None:
        self._groups[group.id] = group

    def find_by_id(self, group_id: str) -> Group | None:
        return self._groups.get(group_id)
