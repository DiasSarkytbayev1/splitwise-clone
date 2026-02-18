import ssl

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from api.app.variables import MyVariables

# Validate required DB configuration early so startup errors are actionable.
if not MyVariables.async_database_url or not MyVariables.sync_database_url:
    raise RuntimeError(
        "DATABASE_URL is not configured. Set it in your .env file (project root), "
        "for example: postgresql://user:password@host:5432/dbname"
    )

# Async engine connected to PostgreSQL via asyncpg
# asyncpg doesn't understand sslmode in URL params, so TLS is configured via connect_args.
#
# By default, certificate verification remains enabled (db_ssl_verify=true).
# For local/dev environments where trust store configuration is missing, you can
# set DB_SSL_VERIFY=false to allow encrypted connections without certificate checks.
if MyVariables.db_ssl:
    if MyVariables.db_ssl_verify:
        connect_args = {"ssl": ssl.create_default_context()}
    else:
        insecure_context = ssl.create_default_context()
        insecure_context.check_hostname = False
        insecure_context.verify_mode = ssl.CERT_NONE
        connect_args = {"ssl": insecure_context}
else:
    connect_args = {}
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
