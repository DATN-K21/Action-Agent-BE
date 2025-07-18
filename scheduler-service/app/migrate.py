"""
Database migrations using Alembic.
"""

from alembic import command
from alembic.config import Config
import os
import sys

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def run_migrations():
    """Run database migrations."""
    alembic_cfg = Config(os.path.join(os.path.dirname(__file__), '..', 'alembic.ini'))
    command.upgrade(alembic_cfg, "head")

if __name__ == "__main__":
    run_migrations()
