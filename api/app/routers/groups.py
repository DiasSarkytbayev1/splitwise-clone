import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
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
    group = Group(
        name=body.name,
        type=body.type,
        currency_code=body.currency_code,
        cover_image=body.cover_image,
        created_by=current_user.id,
    )
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
