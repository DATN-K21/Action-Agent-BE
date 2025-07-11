"""
Test script for Scheduler Tool

This script demonstrates how to use the scheduler tool and verifies
that it's properly integrated into the AI service.
"""

import asyncio
import json
from app.core.tools.scheduler.scheduler_tool import (
    create_scheduled_job,
    get_scheduled_jobs,
    validate_cron_expression,
)


async def test_scheduler_tool():
    """Test the scheduler tool functions."""
    print("Testing Scheduler Tool Integration...")
    
    # Test 1: Validate cron expression
    print("\n1. Testing cron validation...")
    result = await validate_cron_expression(
        cron_expression="0 9 * * *",
        timezone="UTC"
    )
    print(f"Cron validation result: {result}")
    
    # Test 2: Create a job (this will likely fail if scheduler service is not running)
    print("\n2. Testing job creation...")
    result = await create_scheduled_job(
        name="Test Daily Report",
        description="A test job that generates daily reports",
        job_type="recurring",
        cron_expression="0 9 * * *",
        prompt="Generate a daily summary report for the team",
        team_id="test-team-123",
        timezone="UTC",
        is_active=True
    )
    print(f"Job creation result: {result}")
    
    # Test 3: Get jobs
    print("\n3. Testing job retrieval...")
    result = await get_scheduled_jobs(
        limit=5,
        skip=0
    )
    print(f"Jobs retrieval result: {result}")
    
    print("\nScheduler tool tests completed!")


if __name__ == "__main__":
    asyncio.run(test_scheduler_tool())
