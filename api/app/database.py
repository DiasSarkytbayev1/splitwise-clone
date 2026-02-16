from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.variables import MyVariables

# Async engine connected to PostgreSQL via asyncpg
# ssl=True is needed for Neon and other cloud databases (asyncpg doesn't read sslmode from the URL)
connect_args = {"ssl": MyVariables.db_ssl} if MyVariables.db_ssl else {}
engine = create_async_engine(
    MyVariables.async_database_url,
    echo=MyVariables.db_echo,
    connect_args=connect_args,
)

# Session factory producing AsyncSession instances
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Sync engine and session for seeds/scripts
sync_engine = create_engine(MyVariables.sync_database_url, echo=MyVariables.db_echo)
Session = sessionmaker(bind=sync_engine)


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass
