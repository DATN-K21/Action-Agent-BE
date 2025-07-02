#!/usr/bin/env python3
"""
Debug Celery worker script for development and debugging purposes.
This script starts a Celery worker with debugging configuration.
"""

import argparse
import os
import sys
from pathlib import Path


def setup_environment():
    """Setup environment and Python path."""
    # Add the project root to Python path
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))

    # Set environment variables for debugging
    os.environ.setdefault("DEBUG_CELERY", "1")
    os.environ.setdefault("CELERY_DEBUG", "1")


def debug_celery_worker():
    """Start Celery worker in debug mode with enhanced logging."""
    from app.core import logging
    from app.core.celery_app import celery_app
    from app.core.settings import env_settings

    logger = logging.get_logger(__name__)

    logger.info("Starting Celery worker in debug mode...")
    logger.info(f"Broker URL: {env_settings.CELERY_BROKER_URL}")
    logger.info(f"Result Backend: {env_settings.CELERY_RESULT_BACKEND}")

    # Test if we can import tasks
    try:
        import app.jobs.tasks  # noqa: F401

        logger.info("Successfully imported tasks module")
    except Exception as e:
        logger.error(f"Failed to import tasks: {e}")
        return

    # Print available tasks
    logger.info(f"Registered tasks: {list(celery_app.tasks.keys())}")

    # Start worker with debug options
    celery_app.worker_main(
        [
            "worker",
            "--loglevel=debug",
            "--concurrency=1",
            "--pool=solo",  # Use solo pool for easier debugging
            "--queues=main-queue",
            "--hostname=debug-worker@%h",
            "--without-gossip",
            "--without-mingle",
            "--without-heartbeat",
        ]
    )


if __name__ == "__main__":
    setup_environment()

    parser = argparse.ArgumentParser(description="Debug Celery worker")
    parser.add_argument(
        "--mode",
        choices=["worker", "test", "inspect"],
        default="worker",
        help="Debug mode: worker (start worker), test (test tasks), inspect (show config)",
    )

    args = parser.parse_args()

    from app.core import logging

    logger = logging.get_logger(__name__)
    logger.info(f"Starting Celery debug in mode: {args.mode}")

    if args.mode == "worker":
        debug_celery_worker()
