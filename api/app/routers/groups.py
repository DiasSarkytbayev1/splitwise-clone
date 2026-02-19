import uuid

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.auth import get_current_user
from api.app.dependencies import get_db
from api.app.models.group import Group
from api.app.models.group_member import GroupMember
from api.app.models.user import User
from api.app.schemas.group import GroupCreateRequest, GroupResponse

router = APIRouter(prefix="/groups", tags=["Groups"])


@router.get("", response_model=list[GroupResponse])
async def list_groups(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all groups the current user belongs to."""
    result = await db.execute(
        select(Group)
        .join(GroupMember, GroupMember.group_id == Group.id)
        .where(GroupMember.user_id == current_user.id)
        .order_by(Group.created_at.desc())
    )
    return list(result.scalars().all())


@router.post("", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    body: GroupCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new group. The creator is automatically added as a member."""
    group = Group()
    group.name = body.name
    group.type = body.type
    group.currency_code = body.currency_code
    group.cover_image = body.cover_image
    group.created_by = current_user.id
    db.add(group)
    await db.flush()  # populate group.id and invite_code

    # Auto-add creator as the first member
    db.add(GroupMember(group_id=group.id, user_id=current_user.id))

    await db.commit()
    await db.refresh(group)
    return group


@router.get("/{code}", response_model=GroupResponse)
async def get_group_by_code(
    code: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get group by invite code or group ID."""
    # Try to parse as UUID first (for GET /groups/:id)
    try:
        group_id = uuid.UUID(code)
        result = await db.execute(select(Group).where(Group.id == group_id))
    except ValueError:
        # Not a UUID, treat as invite code (for GET /groups/:code)
        result = await db.execute(select(Group).where(Group.invite_code == code))

    group = result.scalar_one_or_none()
    if group is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    return group


@router.patch("/{code}", response_model=GroupResponse)
async def update_group_by_code(
    code: str,
    debt_simplification: bool = Body(..., embed=True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update group by invite code or group ID (toggle debt_simplification)."""
    # Try to parse as UUID first (for PATCH /groups/:id)
    try:
        group_id = uuid.UUID(code)
        result = await db.execute(select(Group).where(Group.id == group_id))
    except ValueError:
        # Not a UUID, treat as invite code (for PATCH /groups/:code)
        result = await db.execute(select(Group).where(Group.invite_code == code))

    group = result.scalar_one_or_none()
    if group is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")

    # Only allow group members to update
    member_result = await db.execute(
        select(GroupMember).where(
            GroupMember.group_id == group.id,
            GroupMember.user_id == current_user.id,
        )
    )
    if member_result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="You are not a member of this group"
        )

    await db.execute(
        update(Group).where(Group.id == group.id).values(debt_simplification=debt_simplification)
    )
    await db.commit()
    await db.refresh(group)
    return group
