from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.auth import get_current_user
from api.app.dependencies import get_db
from api.app.models.group import Group
from api.app.models.group_member import GroupMember
from api.app.models.user import User as UserModel
from api.app.schemas.member import AddMemberRequest, InviteCodeResponse, MemberResponse

router = APIRouter(prefix="/groups/{group_id}/members", tags=["Group Members"])


async def _verify_group_exists(db: AsyncSession, group_id: uuid.UUID) -> None:
    """Verify that a group exists, raise 404 if not."""
    group = await db.get(Group, group_id)
    if group is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")


async def _verify_user_in_group(db: AsyncSession, group_id: uuid.UUID, user_id: uuid.UUID) -> None:
    """Verify that a user is a member of the group."""
    result = await db.execute(
        select(GroupMember).where(
            GroupMember.group_id == group_id,
            GroupMember.user_id == user_id,
        )
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="You are not a member of this group"
        )


async def _get_member_with_user(db: AsyncSession, member_id: uuid.UUID) -> dict | None:
    """Return a single member row joined with user info."""
    result = await db.execute(
        select(
            GroupMember.id,
            GroupMember.group_id,
            GroupMember.user_id,
            GroupMember.joined_at,
            UserModel.name.label("user_name"),
            UserModel.email.label("user_email"),
        )
        .join(UserModel, UserModel.id == GroupMember.user_id)
        .where(GroupMember.id == member_id)
    )
    row = result.one_or_none()
    return row._asdict() if row else None


async def _add_member_by_user_id(
    db: AsyncSession, group_id: uuid.UUID, user_id: uuid.UUID
) -> GroupMember:
    """Add a user to a group by their user id."""
    # Check user exists
    user = await db.get(UserModel, user_id)
    if user is None:
        raise ValueError("User not found")

    # Check not already a member
    existing = await db.execute(
        select(GroupMember).where(
            GroupMember.group_id == group_id,
            GroupMember.user_id == user_id,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise ValueError("User is already a member of this group")

    member = GroupMember(group_id=group_id, user_id=user_id)
    db.add(member)
    await db.commit()
    await db.refresh(member)
    return member


@router.get("", response_model=list[MemberResponse])
async def get_members(
    group_id: uuid.UUID,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get list of users in a group. User must be a member to view."""
    await _verify_group_exists(db, group_id)
    await _verify_user_in_group(db, group_id, current_user.id)

    result = await db.execute(
        select(
            GroupMember.id,
            GroupMember.group_id,
            GroupMember.user_id,
            GroupMember.joined_at,
            UserModel.name.label("user_name"),
            UserModel.email.label("user_email"),
        )
        .join(UserModel, UserModel.id == GroupMember.user_id)
        .where(GroupMember.group_id == group_id)
        .order_by(GroupMember.joined_at)
    )
    return [MemberResponse(**row._asdict()) for row in result.all()]


@router.get("/invite", response_model=InviteCodeResponse)
async def get_invite_code(
    group_id: uuid.UUID,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the invite code for a group. User must be a member."""
    await _verify_group_exists(db, group_id)
    await _verify_user_in_group(db, group_id, current_user.id)

    group = await db.get(Group, group_id)
    return InviteCodeResponse(invite_code=group.invite_code)


@router.post("", response_model=MemberResponse, status_code=status.HTTP_201_CREATED)
async def add_member(
    group_id: uuid.UUID,
    body: AddMemberRequest,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a user to a group by userId or email. Requires membership."""
    await _verify_group_exists(db, group_id)
    await _verify_user_in_group(db, group_id, current_user.id)

    if body.user_id is None and body.email is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide either user_id or email",
        )

    try:
        if body.user_id is not None:
            member = await _add_member_by_user_id(db, group_id, body.user_id)
        else:
            # Look up user by email first
            result = await db.execute(select(UserModel).where(UserModel.email == body.email))
            user = result.scalar_one_or_none()
            if user is None:
                raise ValueError("No user found with that email")
            member = await _add_member_by_user_id(db, group_id, user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    # Fetch the member with user info via JOIN for the response
    member_data = await _get_member_with_user(db, member.id)
    return MemberResponse(**member_data)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    group_id: uuid.UUID,
    user_id: uuid.UUID,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a user from the group. Must be a member to remove others."""
    await _verify_group_exists(db, group_id)
    await _verify_user_in_group(db, group_id, current_user.id)

    result = await db.execute(
        select(GroupMember).where(
            GroupMember.group_id == group_id,
            GroupMember.user_id == user_id,
        )
    )
    member = result.scalar_one_or_none()
    if member is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User is not a member of this group"
        )

    await db.delete(member)
    await db.commit()
