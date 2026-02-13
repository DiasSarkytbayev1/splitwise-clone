from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.models.group import Group
from app.models.group_member import GroupMember
from app.models.user import User
from app.schemas.member import AddMemberRequest, InviteCodeResponse, MemberResponse

router = APIRouter(prefix="/groups/{group_id}/members", tags=["Group Members"])


async def _get_member_with_user(db: AsyncSession, member_id: uuid.UUID) -> dict | None:
    """Return a single member row joined with user info."""
    result = await db.execute(
        select(
            GroupMember.id,
            GroupMember.group_id,
            GroupMember.user_id,
            GroupMember.joined_at,
            User.name.label("user_name"),
            User.email.label("user_email"),
        )
        .join(User, User.id == GroupMember.user_id)
        .where(GroupMember.id == member_id)
    )
    row = result.one_or_none()
    return row._asdict() if row else None


async def _add_member_by_user_id(
    db: AsyncSession, group_id: uuid.UUID, user_id: uuid.UUID
) -> GroupMember:
    """Add a user to a group by their user id."""
    # Check user exists
    user = await db.get(User, user_id)
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


@router.get("/list-members", response_model=list[MemberResponse])
async def get_members(
    group_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get list of users in a group."""
    result = await db.execute(
        select(
            GroupMember.id,
            GroupMember.group_id,
            GroupMember.user_id,
            GroupMember.joined_at,
            User.name.label("user_name"),
            User.email.label("user_email"),
        )
        .join(User, User.id == GroupMember.user_id)
        .where(GroupMember.group_id == group_id)
        .order_by(GroupMember.joined_at)
    )
    return [MemberResponse(**row._asdict()) for row in result.all()]


@router.get("/invite-code", response_model=InviteCodeResponse)
async def get_group_invite_code(
    group_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get the invite code for a group."""
    group = await db.get(Group, group_id)
    if group is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    return InviteCodeResponse(invite_code=group.invite_code)


@router.post("/add-member", response_model=MemberResponse, status_code=status.HTTP_201_CREATED)
async def add_member(
    group_id: uuid.UUID,
    body: AddMemberRequest,
    db: AsyncSession = Depends(get_db),
):
    """Add a user to a group by userId or email."""
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
            result = await db.execute(select(User).where(User.email == body.email))
            user = result.scalar_one_or_none()
            if user is None:
                raise ValueError("No user found with that email")
            member = await _add_member_by_user_id(db, group_id, user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Fetch the member with user info via JOIN for the response
    member_data = await _get_member_with_user(db, member.id)
    return MemberResponse(**member_data)


@router.delete("/remove-member/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_member(
    group_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Remove a user from the group."""
    result = await db.execute(
        select(GroupMember).where(
            GroupMember.group_id == group_id,
            GroupMember.user_id == user_id,
        )
    )
    member = result.scalar_one_or_none()
    if member is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is not a member of this group")

    await db.delete(member)
    await db.commit()
