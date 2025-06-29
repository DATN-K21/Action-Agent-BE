#!/usr/bin/env python3
"""
Standalone script to run Alembic database migrations.
This should be run before starting the FastAPI application.
"""

import sys
from pathlib import Path

from alembic import command
from alembic.config import Config


def main():
    """Run database migrations."""
    print("Starting migration script...")
    try:
        # Get the path to alembic.ini
        script_dir = Path(__file__).parent
        alembic_ini_path = script_dir / "alembic.ini"

        print(f"Looking for alembic.ini at: {alembic_ini_path}")

        if not alembic_ini_path.exists():
            print(f"Error: alembic.ini not found at {alembic_ini_path}")
            sys.exit(1)

        print("Found alembic.ini, creating config...")
        # Create Alembic config
        alembic_cfg = Config(str(alembic_ini_path))

        print("Running database migrations...")
        command.upgrade(alembic_cfg, "head")
        print("Database migrations completed successfully!")

    except Exception as e:
        print(f"Error running migrations: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
