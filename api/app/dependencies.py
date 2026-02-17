from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from api.app.database import AsyncSessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session and ensure it is closed afterwards."""
    async with AsyncSessionLocal() as session:
        yield session
