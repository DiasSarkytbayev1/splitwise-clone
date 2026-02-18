#!/usr/bin/env python3
"""
Environment Variables Validation Script

This script checks if all required environment variables are properly configured.
Run this before starting the application to catch configuration issues early.

Usage:
    python check_env.py
"""

import os
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

# Load .env file
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Color codes for terminal output
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"


def check_variable(name, required=True, validate_func=None):
    """Check if an environment variable is set and optionally validate it."""
    value = os.getenv(name)

    if value is None:
        if required:
            print(f"{RED}✗{RESET} {name}: {RED}NOT SET (REQUIRED){RESET}")
            return False
        else:
            print(f"{YELLOW}⚠{RESET} {name}: {YELLOW}Not set (optional, using default){RESET}")
            return True

    # Validate the value if a validation function is provided
    if validate_func:
        is_valid, message = validate_func(value)
        if not is_valid:
            print(f"{RED}✗{RESET} {name}: {RED}{message}{RESET}")
            return False

    # Mask sensitive values
    if "SECRET" in name or "PASSWORD" in name or "KEY" in name:
        display_value = value[:10] + "..." if len(value) > 10 else "***"
    else:
        display_value = value

    print(f"{GREEN}✓{RESET} {name}: {display_value}")
    return True


def validate_database_url(value):
    """Validate database URL format."""
    if not value.startswith("postgresql://"):
        return False, "Must start with 'postgresql://'"
    if "@" not in value or "/" not in value.split("@")[-1]:
        return False, "Invalid format (should be postgresql://user:pass@host:port/dbname)"
    return True, ""


def validate_jwt_secret(value):
    """Validate JWT secret key."""
    if value == "your-secret-key-change-in-production":
        return False, "Using default secret key! Generate a secure one with: openssl rand -hex 32"
    if len(value) < 32:
        return False, "Secret key is too short (should be at least 32 characters)"
    return True, ""


def validate_port(value):
    """Validate port number."""
    try:
        port = int(value)
        if port < 1 or port > 65535:
            return False, "Port must be between 1 and 65535"
        return True, ""
    except ValueError:
        return False, "Port must be a number"


def validate_boolean(value):
    """Validate boolean value."""
    if value.lower() not in ["true", "false"]:
        return False, "Must be 'true' or 'false'"
    return True, ""


def main():
    """Main validation function."""
    print(f"\n{BLUE}{'=' * 70}{RESET}")
    print(f"{BLUE}Environment Variables Validation{RESET}")
    print(f"{BLUE}{'=' * 70}{RESET}\n")

    # Check if .env file exists
    if not env_path.exists():
        print(f"{RED}✗ .env file not found at {env_path}{RESET}")
        print(f"{YELLOW}ℹ  Copy .env.example to .env and configure it:{RESET}")
        print("   cp .env.example .env\n")
        return False

    print(f"{GREEN}✓{RESET} .env file found at {env_path}\n")

    print(f"{BLUE}Required Variables:{RESET}")
    print(f"{BLUE}{'-' * 70}{RESET}")

    all_valid = True

    # Required variables
    all_valid &= check_variable("DATABASE_URL", required=True, validate_func=validate_database_url)
    all_valid &= check_variable("JWT_SECRET_KEY", required=True, validate_func=validate_jwt_secret)

    print(f"\n{BLUE}Optional Variables (with defaults):{RESET}")
    print(f"{BLUE}{'-' * 70}{RESET}")

    # Optional variables
    check_variable("JWT_ALGORITHM", required=False)
    check_variable("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", required=False)
    check_variable("DB_SSL", required=False, validate_func=validate_boolean)
    check_variable("DB_ECHO", required=False, validate_func=validate_boolean)
    check_variable("APP_NAME", required=False)
    check_variable("APP_VERSION", required=False)
    check_variable("ENVIRONMENT", required=False)
    check_variable("DEBUG", required=False, validate_func=validate_boolean)
    check_variable("SERVER_HOST", required=False)
    check_variable("SERVER_PORT", required=False, validate_func=validate_port)
    check_variable("SERVER_RELOAD", required=False, validate_func=validate_boolean)
    check_variable("CORS_ORIGINS", required=False)
    check_variable("CORS_CREDENTIALS", required=False, validate_func=validate_boolean)
    check_variable("CORS_METHODS", required=False)
    check_variable("CORS_HEADERS", required=False)

    print(f"\n{BLUE}{'=' * 70}{RESET}")

    if all_valid:
        print(f"{GREEN}✓ All required environment variables are properly configured!{RESET}\n")

        # Additional recommendations
        debug = os.getenv("DEBUG", "true").lower() == "true"
        environment = os.getenv("ENVIRONMENT", "development")

        if environment == "production" and debug:
            print(f"{YELLOW}⚠  Warning: DEBUG=true in production environment{RESET}")

        cors_origins = os.getenv("CORS_ORIGINS", "*")
        if environment == "production" and cors_origins == "*":
            print(f"{YELLOW}⚠  Warning: CORS_ORIGINS=* in production (security risk){RESET}")

        return True
    else:
        print(f"{RED}✗ Some required environment variables are missing or invalid{RESET}")
        print(f"{YELLOW}ℹ  Please update your .env file and try again{RESET}\n")
        return False


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Interrupted by user{RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{RED}Error: {e}{RESET}")
        sys.exit(1)
