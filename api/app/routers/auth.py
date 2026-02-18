import inspect

from fastapi import APIRouter, Depends, HTTPException, status
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.auth import create_access_token, get_current_user
from api.app.dependencies import get_db
from api.app.models.group_member import GroupMember
from api.app.models.user import User
from api.app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    RegisterRequest,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Password hashing context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def _maybe_await(value):
    """Support both async and sync SQLAlchemy sessions."""
    if inspect.isawaitable(value):
        return await value
    return value


def hash_password(plain: str) -> str:
    """Hash a plaintext password with bcrypt."""
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return pwd_context.verify(plain, hashed)


async def _maybe_join_group(db: AsyncSession, user_id, group_id) -> None:
    """If an invite group id is provided, add the user to that group."""
    if group_id is None:
        return
    # Check if already a member
    existing = await _maybe_await(
        db.execute(
            select(GroupMember).where(
                GroupMember.group_id == group_id,
                GroupMember.user_id == user_id,
            )
        )
    )
    if existing.scalar_one_or_none() is None:
        db.add(GroupMember(group_id=group_id, user_id=user_id))


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user account and return JWT access token."""
    # Check for duplicate email
    result = await _maybe_await(db.execute(select(User).where(User.email == body.email)))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )

    user = User(
        name=body.name,
        email=body.email,
        password_hash=hash_password(body.password),
    )
    db.add(user)
    await _maybe_await(db.flush())  # populate user.id

    # Auto-join group if invite id provided
    await _maybe_join_group(db, user.id, body.invite_group_id)

    await _maybe_await(db.commit())
    await _maybe_await(db.refresh(user))

    # Generate JWT token
    access_token = create_access_token(user.id)

    return AuthResponse(access_token=access_token, user=UserResponse.model_validate(user))


@router.post("/login", response_model=AuthResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Log in with email and password and return JWT access token."""
    result = await _maybe_await(db.execute(select(User).where(User.email == body.email)))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Auto-join group if invite id provided
    await _maybe_join_group(db, user.id, body.invite_group_id)
    await _maybe_await(db.commit())

    # Generate JWT token
    access_token = create_access_token(user.id)

    return AuthResponse(access_token=access_token, user=UserResponse.model_validate(user))


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get the current authenticated user's profile."""
    return UserResponse.model_validate(current_user)
