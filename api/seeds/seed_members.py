from app.models.user import User
from app.models.group import Group
from app.models.group_member import GroupMember
from app.database import Session


def seed_members():
    session = Session()

    users = (
        session.query(User)
        .order_by(User.created_at.asc())
        .limit(3)
        .all()
    )

    if len(users) < 3:
        print("Need at least 3 users seeded first.")
        session.close()
        return

    group = (
        session.query(Group)
        .order_by(Group.created_at.asc())
        .first()
    )

    if group is None:
        print("Need at least one group seeded first.")
        session.close()
        return

    member1 = GroupMember(
        group_id=group.id,
        user_id=users[0].id,
    )

    member2 = GroupMember(
        group_id=group.id,
        user_id=users[1].id,
    )

    member3 = GroupMember(
        group_id=group.id,
        user_id=users[2].id,
    )

    session.add_all([member1, member2, member3])
    session.commit()
    session.close()

    print("✅ Group members seeded successfully")
