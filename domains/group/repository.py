from typing import Dict, Optional

from domain import Group


class GroupRepository:
    def __init__(self):
        self._groups: Dict[str, Group] = {}

    def save(self, group: Group) -> None:
        self._groups[group.id] = group

    def find_by_id(self, group_id: str) -> Optional[Group]:
        return self._groups.get(group_id)
