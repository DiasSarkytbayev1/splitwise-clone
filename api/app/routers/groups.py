import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.models.group import Group
from app.models.group_member import GroupMember
from app.schemas.group import GroupCreateRequest, GroupResponse

router = APIRouter(prefix="/groups", tags=["Groups"])


@router.get("/list-groups", response_model=list[GroupResponse])
async def list_groups(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """List all groups a user belongs to."""
    result = await db.execute(
        select(Group)
        .join(GroupMember, GroupMember.group_id == Group.id)
        .where(GroupMember.user_id == user_id)
        .order_by(Group.created_at.desc())
    )
    return list(result.scalars().all())


@router.post("/create-group", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_new_group(
    body: GroupCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a new group. The creator is automatically added as a member."""
    group = Group(
        name=body.name,
        type=body.type,
        currency_code=body.currency_code,
        cover_image=body.cover_image,
        created_by=body.user_id,
    )
    db.add(group)
    await db.flush()  # populate group.id and invite_code

    # Auto-add creator as the first member
    db.add(GroupMember(group_id=group.id, user_id=body.user_id))

    await db.commit()
    await db.refresh(group)
    return group


@router.get("/code/{code}", response_model=GroupResponse)
async def get_by_invite_code(
    code: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a group by its invite code."""
    result = await db.execute(select(Group).where(Group.invite_code == code))
    group = result.scalar_one_or_none()
    if group is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    return group


@router.get("/{group_id}", response_model=GroupResponse)
async def get_group(
    group_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get metadata for a specific group."""
    result = await db.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    if group is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    return group
