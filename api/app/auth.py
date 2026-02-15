"""JWT authentication utilities."""

from datetime import datetime, timedelta
from typing import Optional
import uuid

from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.variables import MyVariables
from app.database import AsyncSessionLocal
from app.models.user import User

# Security scheme for Swagger UI
security = HTTPBearer()


def create_access_token(user_id: uuid.UUID) -> str:
    """
    Create a JWT access token for a user.

    Args:
        user_id: The user's UUID

    Returns:
        Encoded JWT token string
    """
    expire = datetime.utcnow() + timedelta(minutes=MyVariables.jwt_access_token_expire_minutes)
    to_encode = {
        "sub": str(user_id),
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    encoded_jwt = jwt.encode(
        to_encode,
        MyVariables.jwt_secret_key,
        algorithm=MyVariables.jwt_algorithm
    )
    return encoded_jwt


def decode_access_token(token: str) -> Optional[uuid.UUID]:
    """
    Decode and verify a JWT access token.

    Args:
        token: The JWT token string

    Returns:
        The user's UUID if valid, None otherwise
    """
    try:
        payload = jwt.decode(
            token,
            MyVariables.jwt_secret_key,
            algorithms=[MyVariables.jwt_algorithm]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        return uuid.UUID(user_id)
    except (JWTError, ValueError):
        return None


async def get_db_for_auth():
    """Dependency to provide database session for auth operations."""
    async with AsyncSessionLocal() as session:
        yield session


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db_for_auth)
) -> User:
    """
    Dependency to get the current authenticated user from JWT token.

    Args:
        credentials: HTTP Bearer token from Authorization header
        db: Database session

    Returns:
        The authenticated User object

    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials
    user_id = decode_access_token(token)

    if user_id is None:
        raise credentials_exception

    # Fetch user from database
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    return user
