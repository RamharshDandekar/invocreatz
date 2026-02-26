"""Alembic database migration management."""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from memory.postgres_client import init_db


async def migrate():
    """Run database migrations (create all tables)."""
    print("Running database migrations...")
    await init_db()
    print("Migrations complete.")


if __name__ == "__main__":
    asyncio.run(migrate())
