"""
Run all seeds in order.

Usage:
    python -m seeds.run_all
"""

import sys
from pathlib import Path

# Ensure the project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import Base, sync_engine
from seeds.seed_users import seed_users
from seeds.seed_group import seed_group
from seeds.seed_members import seed_members
from seeds.seed_expenses import seed_expenses
from seeds.seed_expense_shares import seed_expense_shares

# Import all models so Base.metadata knows about them
import app.models  # noqa: F401


if __name__ == "__main__":
    # Create all tables if they don't exist
    Base.metadata.create_all(sync_engine)
    print("✅ Tables created")

    seed_users()
    seed_group()
    seed_members()
    seed_expenses()
    seed_expense_shares()

    print("\n🎉 All seeds completed!")
