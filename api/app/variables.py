

import os
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
from dotenv import load_dotenv

# Load .env file only once
load_dotenv()


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

    database_url = os.getenv("DATABASE_URL")

    # asyncpg driver for the FastAPI server
    # asyncpg doesn't understand sslmode/channel_binding as URL params,
    # so we strip them and pass ssl=True via connect_args in database.py
    async_database_url = _strip_query_params(
        database_url.replace("postgresql://", "postgresql+asyncpg://", 1),
        ["sslmode", "channel_binding"],
    ) if database_url else None

    # psycopg2 driver for seeds/scripts (keeps sslmode in the URL)
    sync_database_url = database_url.replace("postgresql://", "postgresql+psycopg2://", 1) \
        if database_url else None

