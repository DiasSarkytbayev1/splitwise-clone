import os
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from dotenv import load_dotenv

# Load .env files using stable paths (independent of current working directory).
_CURRENT_FILE = Path(__file__).resolve()
_API_DIR = _CURRENT_FILE.parents[1]
_PROJECT_ROOT = _CURRENT_FILE.parents[2]
load_dotenv(_PROJECT_ROOT / ".env")
load_dotenv(_API_DIR / ".env", override=True)


def _strip_query_params(url: str, params_to_strip: list[str]) -> str:
    """Remove specific query parameters from a URL."""
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    for p in params_to_strip:
        qs.pop(p, None)
    new_query = urlencode(qs, doseq=True)
    return urlunparse(parsed._replace(query=new_query))


# Define all your environment variables in one place


class MyVariables:
    # ────────────────────────────────────────────────────────────────────────────
    # Database Configuration
    # ────────────────────────────────────────────────────────────────────────────
    database_url = os.getenv("DATABASE_URL")

    # asyncpg driver for the FastAPI server
    # asyncpg doesn't understand sslmode/channel_binding as URL params,
    # so we strip them and pass ssl=True via connect_args in database.py
    async_database_url = (
        _strip_query_params(
            database_url.replace("postgresql://", "postgresql+asyncpg://", 1),
            ["sslmode", "channel_binding"],
        )
        if database_url
        else None
    )

    # psycopg2 driver for seeds/scripts (keeps sslmode in the URL)
    sync_database_url = (
        database_url.replace("postgresql://", "postgresql+psycopg2://", 1) if database_url else None
    )

    # Database connection settings
    db_echo = os.getenv("DB_ECHO", "false").lower() == "true"
    db_ssl = os.getenv("DB_SSL", "true").lower() == "true"
    _default_ssl_verify = (
        "false" if os.getenv("ENVIRONMENT", "development").lower() == "development" else "true"
    )
    db_ssl_verify = os.getenv("DB_SSL_VERIFY", _default_ssl_verify).lower() == "true"

    # ────────────────────────────────────────────────────────────────────────────
    # JWT Authentication Configuration
    # ────────────────────────────────────────────────────────────────────────────
    jwt_secret_key = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
    jwt_access_token_expire_minutes = int(
        os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "1440")
    )  # 24 hours

    # ────────────────────────────────────────────────────────────────────────────
    # Application Configuration
    # ────────────────────────────────────────────────────────────────────────────
    app_name = os.getenv("APP_NAME", "Expense Splitter API")
    app_version = os.getenv("APP_VERSION", "1.0.0")
    app_description = os.getenv(
        "APP_DESCRIPTION", "A FastAPI backend for splitting expenses among groups of users."
    )

    # Environment (development, staging, production)
    environment = os.getenv("ENVIRONMENT", "development")
    debug = os.getenv("DEBUG", "true").lower() == "true"

    # ────────────────────────────────────────────────────────────────────────────
    # Server Configuration
    # ────────────────────────────────────────────────────────────────────────────
    server_host = os.getenv("SERVER_HOST", "0.0.0.0")
    server_port = int(os.getenv("SERVER_PORT", "8000"))
    server_reload = os.getenv("SERVER_RELOAD", "true").lower() == "true"

    # ────────────────────────────────────────────────────────────────────────────
    # CORS Configuration
    # ────────────────────────────────────────────────────────────────────────────
    # Comma-separated list of allowed origins
    cors_origins = os.getenv("CORS_ORIGINS", "*").split(",")
    cors_credentials = os.getenv("CORS_CREDENTIALS", "true").lower() == "true"
    cors_methods = os.getenv("CORS_METHODS", "*").split(",")
    cors_headers = os.getenv("CORS_HEADERS", "*").split(",")
