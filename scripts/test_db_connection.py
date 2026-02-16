#!/usr/bin/env python3
"""
Database Connection Test Script

This script tests the PostgreSQL database connection using the settings from .env
Run this to verify your database is properly configured.

Usage:
    python3 scripts/test_db_connection.py
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "api"))

try:
    from dotenv import load_dotenv
    import asyncio
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine
except ImportError as e:
    print(f"❌ Missing dependencies: {e}")
    print(f"💡 Install them with: cd api && pip install -r requirements.txt")
    sys.exit(1)

# Color codes
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"


def print_header(text):
    """Print a formatted header."""
    print(f"\n{BLUE}{'=' * 70}{RESET}")
    print(f"{BLUE}{text}{RESET}")
    print(f"{BLUE}{'=' * 70}{RESET}\n")


def print_success(text):
    """Print success message."""
    print(f"{GREEN}✓{RESET} {text}")


def print_error(text):
    """Print error message."""
    print(f"{RED}✗{RESET} {text}")


def print_info(text):
    """Print info message."""
    print(f"{YELLOW}ℹ{RESET} {text}")


async def test_connection():
    """Test the database connection."""
    print_header("PostgreSQL Connection Test")

    # Load environment variables
    env_path = Path(__file__).parent.parent / ".env"
    if not env_path.exists():
        print_error(f".env file not found at {env_path}")
        print_info("Copy .env.example to .env and configure it")
        return False

    load_dotenv(env_path)
    print_success(f".env file loaded from {env_path}")

    # Get database URL
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print_error("DATABASE_URL not set in .env file")
        return False

    # Parse and display connection info (mask password)
    try:
        from urllib.parse import urlparse
        parsed = urlparse(database_url)
        masked_password = parsed.password[:3] + "***" if parsed.password else "None"
        print_info(f"Host: {parsed.hostname}")
        print_info(f"Port: {parsed.port or 5432}")
        print_info(f"Database: {parsed.path[1:]}")
        print_info(f"User: {parsed.username}")
        print_info(f"Password: {masked_password}")
    except Exception as e:
        print_error(f"Failed to parse DATABASE_URL: {e}")
        return False

    # Convert to async URL
    async_url = database_url.replace("postgresql://", "postgresql+asyncpg://")

    # Strip query params that asyncpg doesn't understand
    from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
    parsed = urlparse(async_url)
    qs = parse_qs(parsed.query)
    qs.pop("sslmode", None)
    qs.pop("channel_binding", None)
    new_query = urlencode(qs, doseq=True)
    async_url = urlunparse(parsed._replace(query=new_query))

    # Determine SSL setting
    db_ssl = os.getenv("DB_SSL", "true").lower() == "true"
    connect_args = {"ssl": db_ssl} if db_ssl else {}

    print(f"\n{BLUE}Testing connection...{RESET}\n")

    try:
        # Create engine
        engine = create_async_engine(
            async_url,
            echo=False,
            connect_args=connect_args,
        )

        # Test connection
        async with engine.begin() as conn:
            # Test basic query
            result = await conn.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            assert row[0] == 1
            print_success("Successfully connected to database")

            # Get PostgreSQL version
            result = await conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print_success(f"PostgreSQL version: {version.split(',')[0]}")

            # Get current database
            result = await conn.execute(text("SELECT current_database()"))
            current_db = result.fetchone()[0]
            print_success(f"Current database: {current_db}")

            # Get current user
            result = await conn.execute(text("SELECT current_user"))
            current_user = result.fetchone()[0]
            print_success(f"Current user: {current_user}")

            # Check if we can create tables (test privileges)
            try:
                await conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS _connection_test (
                        id SERIAL PRIMARY KEY,
                        test_value VARCHAR(50)
                    )
                """))
                print_success("Can create tables (privileges OK)")

                # Clean up test table
                await conn.execute(text("DROP TABLE IF EXISTS _connection_test"))
                print_success("Can drop tables (privileges OK)")

            except Exception as e:
                print_error(f"Cannot create tables: {e}")
                print_info("You may need to grant additional privileges")

        await engine.dispose()

        print(f"\n{GREEN}{'=' * 70}{RESET}")
        print(f"{GREEN}✓ All connection tests passed!{RESET}")
        print(f"{GREEN}{'=' * 70}{RESET}\n")

        print_info("You can now start the application:")
        print(f"  {BLUE}cd api && python3 -m app.main{RESET}\n")

        return True

    except Exception as e:
        print(f"\n{RED}{'=' * 70}{RESET}")
        print_error(f"Connection failed: {e}")
        print(f"{RED}{'=' * 70}{RESET}\n")

        print(f"{YELLOW}Troubleshooting steps:{RESET}")
        print(f"  1. Verify PostgreSQL is running: {BLUE}sudo service postgresql status{RESET}")
        print(f"  2. Check DATABASE_URL in .env file")
        print(f"  3. Test with psql: {BLUE}psql -h localhost -U your_user -d your_db{RESET}")
        print(f"  4. Check PostgreSQL logs: {BLUE}sudo tail -f /var/log/postgresql/*.log{RESET}")
        print(f"  5. See POSTGRES_SETUP_WSL.md for more help\n")

        return False


def main():
    """Main function."""
    try:
        success = asyncio.run(test_connection())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Interrupted by user{RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{RED}Unexpected error: {e}{RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
