"""
Scheduler Tool for AI Service

This tool provides scheduling capabilities by communicating with the scheduler-service.
It allows creating, managing, and monitoring scheduled tasks that will automatically
execute AI prompts based on specified schedules.
"""

import json
from typing import Any, Dict, Optional

import httpx
from langchain.tools import StructuredTool
from pydantic import BaseModel, Field

from app.core import logging
from app.core.enums import SchedulerType
from app.core.settings import env_settings

logger = logging.get_logger(__name__)

# Scheduler service URL - configured from environment settings
SCHEDULER_SERVICE_URL = env_settings.SCHEDULER_SERVICE_URL


class CreateJobInput(BaseModel):
    """Input schema for creating a scheduled job."""
    name: str = Field(..., description="Name of the job")
    description: Optional[str] = Field(None, description="Description of the job")
    job_type: SchedulerType = Field(SchedulerType.RECURRING, description="Type of job: 'one_time' or 'recurring'")
    cron_expression: Optional[str] = Field(
        None,
        description="Cron expression for recurring jobs (e.g., '0 9 * * *' for 9 AM daily). Required for recurring jobs, optional for one_time jobs.",
    )
    prompt: str = Field(..., description="The prompt to send to AI service when job executes")
    job_config: Optional[Dict[str, Any]] = Field(None, description="Additional job configuration")
    max_retries: int = Field(3, description="Maximum number of retries")
    timeout_seconds: int = Field(300, description="Job timeout in seconds")
    is_active: bool = Field(True, description="Whether the job should be active")


class GetJobsInput(BaseModel):
    """Input schema for retrieving jobs."""
    status: Optional[str] = Field(None, description="Filter by job status: 'pending', 'running', 'completed', 'failed', 'paused'")
    job_type: Optional[str] = Field(None, description="Filter by job type: 'one_time' or 'recurring'")
    limit: int = Field(10, description="Maximum number of jobs to return")
    skip: int = Field(0, description="Number of jobs to skip for pagination")


class JobControlInput(BaseModel):
    """Input schema for job control operations."""
    job_id: str = Field(..., description="ID of the job to control")


class UpdateJobInput(BaseModel):
    """Input schema for updating a job."""
    job_id: str = Field(..., description="ID of the job to update")
    name: Optional[str] = Field(None, description="New name for the job")
    description: Optional[str] = Field(None, description="New description for the job") 
    cron_expression: Optional[str] = Field(None, description="New cron expression")
    prompt: Optional[str] = Field(None, description="New prompt to execute")
    job_config: Optional[Dict[str, Any]] = Field(None, description="New job configuration")
    max_retries: Optional[int] = Field(None, description="New maximum number of retries")
    timeout_seconds: Optional[int] = Field(None, description="New timeout in seconds")
    is_active: Optional[bool] = Field(None, description="Whether the job should be active")


class ValidateCronInput(BaseModel):
    """Input schema for validating cron expressions."""
    cron_expression: str = Field(..., description="Cron expression to validate")
    timezone: str = Field("UTC", description="Timezone for validation")


async def _make_scheduler_request(
    method: str,
    endpoint: str,
    user_id: str,
    user_role: str,
    user_timezone: str,
    data: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Make HTTP request to scheduler service."""
    url = f"{SCHEDULER_SERVICE_URL}/api/v1/job{endpoint}"
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-User-ID": user_id,
        "X-User-Role": user_role,
        "X-User-Timezone": user_timezone,
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            if method.upper() == "GET":
                response = await client.get(url, headers=headers, params=params)
            elif method.upper() == "POST":
                response = await client.post(url, headers=headers, json=data, params=params)
            elif method.upper() == "PUT":
                response = await client.put(url, headers=headers, json=data, params=params)
            elif method.upper() == "DELETE":
                response = await client.delete(url, headers=headers, params=params)
            else:
                return {"error": f"Unsupported HTTP method: {method}"}
            response.raise_for_status()
            return response.json()
            
    except httpx.TimeoutException:
        logger.error(f"Timeout when calling scheduler service: {url}")
        return {"error": "Request to scheduler service timed out"}
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error when calling scheduler service: {e.response.status_code} - {e.response.text}")
        return {"error": f"HTTP {e.response.status_code}: {e.response.text}"}
    except Exception as e:
        logger.error(f"Error calling scheduler service: {str(e)}")
        return {"error": f"Failed to communicate with scheduler service: {str(e)}"}


async def create_scheduled_job(
    user_id: str,
    user_role: str,
    user_timezone: str,
    team_id: str,
    assistant_id: str,
    **kwargs,
) -> str:
    """
    Create a new scheduled job that will automatically execute AI prompts.
    
    This function creates a job in the scheduler service that will send prompts
    to the specified team at the scheduled times.
    """
    try:
        job_data = CreateJobInput(**kwargs)
        
        # Validate cron expression for recurring jobs
        if job_data.job_type == "recurring" and not job_data.cron_expression:
            return json.dumps({
                "success": False,
                "error": "Cron expression is required for recurring jobs"
            }, indent=2)

        # Prepare job payload
        payload = {
            "name": job_data.name,
            "description": job_data.description,
            "job_type": job_data.job_type,
            "cron_expression": job_data.cron_expression,
            "prompt": job_data.prompt,
            "team_id": team_id,
            "assistant_id": assistant_id,
            "job_config": job_data.job_config,
            "max_retries": job_data.max_retries,
            "timeout_seconds": job_data.timeout_seconds,
            "is_active": job_data.is_active,
        }

        result = await _make_scheduler_request(
            "POST",
            "/create",
            user_id=user_id,
            user_role=user_role,
            user_timezone=user_timezone,
            data=payload,
        )

        if "error" in result:
            return json.dumps({"success": False, "error": result["error"]}, indent=2)

        return json.dumps({"success": True, "message": "Job created successfully", "job": result}, indent=2)

    except Exception as e:
        logger.error(f"Error creating scheduled job: {str(e)}")
        return json.dumps({"success": False, "error": f"Failed to create job: {str(e)}"}, indent=2)


async def get_scheduled_jobs(
    user_id: str,
    user_role: str,
    user_timezone: str,
    team_id: str,
    assistant_id: str,
    **kwargs,
) -> str:
    """
    Retrieve a list of scheduled jobs with optional filtering.

    This function fetches jobs from the scheduler service with optional
    filters for status, type, assistant_id, team_id, and pagination.
    """
    try:
        input_data = GetJobsInput(**kwargs)

        params: Dict[str, Any] = {"skip": input_data.skip, "limit": input_data.limit}

        if input_data.status:
            params["status"] = input_data.status
        if input_data.job_type:
            params["job_type"] = input_data.job_type
        if assistant_id:
            params["assistant_id"] = assistant_id
        if team_id:
            params["team_id"] = team_id

        result = await _make_scheduler_request(
            "GET",
            "/get-jobs",
            user_id=user_id,
            user_role=user_role,
            user_timezone=user_timezone,
            params=params,
        )

        if "error" in result:
            return json.dumps({"success": False, "error": result["error"]}, indent=2)

        return json.dumps({"success": True, "jobs": result}, indent=2)

    except Exception as e:
        logger.error(f"Error retrieving scheduled jobs: {str(e)}")
        return json.dumps({"success": False, "error": f"Failed to retrieve jobs: {str(e)}"}, indent=2)


async def get_job_details(
    user_id: str,
    user_role: str,
    user_timezone: str,
    **kwargs,
) -> str:
    """
    Get detailed information about a specific job.

    This function retrieves detailed information about a job including
    its configuration, status, and execution history.
    """
    try:
        input_data = JobControlInput(**kwargs)

        result = await _make_scheduler_request(
            "GET",
            f"/{input_data.job_id}",
            user_id=user_id,
            user_role=user_role,
            user_timezone=user_timezone,
        )

        if "error" in result:
            return json.dumps({"success": False, "error": result["error"]}, indent=2)

        return json.dumps({"success": True, "job": result}, indent=2)

    except Exception as e:
        logger.error(f"Error getting job details: {str(e)}")
        return json.dumps({"success": False, "error": f"Failed to get job details: {str(e)}"}, indent=2)


async def update_scheduled_job(
    user_id: str,
    user_role: str,
    user_timezone: str,
    team_id: str,
    assistant_id: str,
    **kwargs,
) -> str:
    """
    Update an existing scheduled job.

    This function allows updating job configuration including schedule,
    prompt, and other settings.
    """
    try:
        input_data = UpdateJobInput(**kwargs)

        # Prepare update payload with only non-None values
        payload = {}
        if input_data.name is not None:
            payload["name"] = input_data.name
        if input_data.description is not None:
            payload["description"] = input_data.description
        if input_data.cron_expression is not None:
            payload["cron_expression"] = input_data.cron_expression
        if input_data.prompt is not None:
            payload["prompt"] = input_data.prompt
        if team_id is not None:
            payload["team_id"] = team_id
        if assistant_id is not None:
            payload["assistant_id"] = assistant_id
        if input_data.job_config is not None:
            payload["job_config"] = input_data.job_config
        if input_data.max_retries is not None:
            payload["max_retries"] = input_data.max_retries
        if input_data.timeout_seconds is not None:
            payload["timeout_seconds"] = input_data.timeout_seconds
        if input_data.is_active is not None:
            payload["is_active"] = input_data.is_active

        if not payload:
            return json.dumps({"success": False, "error": "No fields to update"}, indent=2)

        result = await _make_scheduler_request(
            "PUT",
            f"/{input_data.job_id}/update",
            user_id=user_id,
            user_role=user_role,
            user_timezone=user_timezone,
            data=payload,
        )

        if "error" in result:
            return json.dumps({"success": False, "error": result["error"]}, indent=2)

        return json.dumps({"success": True, "message": "Job updated successfully", "job": result}, indent=2)

    except Exception as e:
        logger.error(f"Error updating scheduled job: {str(e)}")
        return json.dumps({"success": False, "error": f"Failed to update job: {str(e)}"}, indent=2)


async def delete_scheduled_job(
    user_id: str,
    user_role: str,
    user_timezone: str,
    **kwargs,
) -> str:
    """
    Delete a scheduled job.

    This function removes a job from the scheduler, stopping all future executions.
    """
    try:
        input_data = JobControlInput(**kwargs)

        result = await _make_scheduler_request(
            "DELETE",
            f"/{input_data.job_id}/remove",
            user_id=user_id,
            user_role=user_role,
            user_timezone=user_timezone,
        )

        if "error" in result:
            return json.dumps({"success": False, "error": result["error"]}, indent=2)

        return json.dumps({"success": True, "message": "Job deleted successfully"}, indent=2)

    except Exception as e:
        logger.error(f"Error deleting scheduled job: {str(e)}")
        return json.dumps({"success": False, "error": f"Failed to delete job: {str(e)}"}, indent=2)


def create_scheduler_tools(
    user_id: str,
    user_role: str,
    timezone: str,
    team_id: str,
    assistant_id: str,
):
    """
    Factory function to create scheduler tools with user context.

    Args:
        user_id: The ID of the user creating/managing jobs
        timezone: User's timezone for scheduling (default: UTC)
        team_id: Default team ID for job creation (optional)
        assistant_id: Default assistant ID for job creation (optional)

    Returns:
        Dictionary containing all scheduler tools with proper context
    """

    async def create_job_with_context(**kwargs) -> str:
        """Create a scheduled job with user context."""
        return await create_scheduled_job(
            user_id=user_id,
            user_role=user_role,
            user_timezone=timezone,
            team_id=team_id,
            assistant_id=assistant_id,
            **kwargs,
        )

    async def get_jobs_with_context(**kwargs) -> str:
        """Get scheduled jobs with user context."""
        return await get_scheduled_jobs(
            user_id=user_id,
            user_role=user_role,
            user_timezone=timezone,
            team_id=team_id,
            assistant_id=assistant_id,
            **kwargs,
        )

    async def get_job_details_with_context(**kwargs) -> str:
        """Get job details with user context."""
        return await get_job_details(
            user_id=user_id,
            user_role=user_role,
            user_timezone=timezone,
            **kwargs,
        )

    async def update_job_with_context(**kwargs) -> str:
        """Update scheduled job with user context."""
        return await update_scheduled_job(
            user_id=user_id,
            user_role=user_role,
            user_timezone=timezone,
            team_id=team_id,
            assistant_id=assistant_id,
            **kwargs,
        )

    async def delete_job_with_context(**kwargs) -> str:
        """Delete scheduled job with user context."""
        return await delete_scheduled_job(
            user_id=user_id,
            user_role=user_role,
            user_timezone=timezone,
            **kwargs,
        )

    # Create the tools with context
    tools = {
        "create_job": StructuredTool.from_function(
            func=create_job_with_context,
            name="Create Scheduled Job",
            description=f"Create a new scheduled job for user {user_id} that will automatically execute AI prompts at specified times. "
            "Supports both one-time and recurring jobs. Use cron expressions for recurring jobs (e.g., '0 9 * * *' for 9 AM daily, "
            "'0 */2 * * *' for every 2 hours, '0 0 * * 1' for every Monday at midnight). "
            f"Jobs will be created in {timezone} timezone and can be configured with retries and timeouts. "
            + (f"Default team: {team_id}. " if team_id else ""),
            args_schema=CreateJobInput,
            return_direct=False,
        ),
        "get_jobs": StructuredTool.from_function(
            func=get_jobs_with_context,
            name="Get Scheduled Jobs",
            description=f"Retrieve a list of scheduled jobs for user {user_id} with comprehensive filtering options. "
            "Filter by job status (pending, running, completed, failed, paused), job type (one_time, recurring), "
            "assistant_id, team_id, and supports pagination with limit/skip parameters. "
            "Essential for monitoring, managing, and auditing existing scheduled tasks and their execution status.",
            args_schema=GetJobsInput,
            return_direct=False,
        ),
        "get_job_details": StructuredTool.from_function(
            func=get_job_details_with_context,
            name="Get Job Details",
            description=f"Get comprehensive detailed information about a specific scheduled job for user {user_id}. "
            "Returns complete job configuration including name, description, schedule settings, prompt content, "
            "current status, execution history, retry configuration, timeout settings, and associated team/assistant information. "
            "Essential for debugging, monitoring, and analyzing individual job performance.",
            args_schema=JobControlInput,
            return_direct=False,
        ),
        "update_job": StructuredTool.from_function(
            func=update_job_with_context,
            name="Update Scheduled Job",
            description=f"Update an existing scheduled job for user {user_id} with flexible modification options. "
            "Can modify job name, description, schedule (cron expression), prompt content, active status, "
            "retry configuration, timeout settings, and job configuration parameters. "
            "Allows partial updates - only specified fields will be changed, leaving others unchanged. "
            "Essential for maintaining and optimizing scheduled job performance.",
            args_schema=UpdateJobInput,
            return_direct=False,
        ),
        "delete_job": StructuredTool.from_function(
            func=delete_job_with_context,
            name="Delete Scheduled Job",
            description=f"Permanently delete a scheduled job for user {user_id} and stop all future executions. "
            "This action is irreversible and will immediately cancel any pending executions of the job. "
            "Use with caution as deleted jobs cannot be recovered. Consider pausing the job first if temporary "
            "suspension is needed instead of permanent deletion.",
            args_schema=JobControlInput,
            return_direct=False,
        ),
    }

    return tools


# Usage Example:
"""
Example of how to use the factory function:

# Create scheduler tools for a specific user
user_tools = create_scheduler_tools(
    user_id="user123",
    timezone="America/New_York", 
    team_id="team456"
)

# Access individual tools
create_tool = user_tools["create_job"]
get_jobs_tool = user_tools["get_jobs"]
delete_tool = user_tools["delete_job"]

# Or get all tools as a list
all_tools = list(user_tools.values())

# Use in LangChain agent
from langchain.agents import create_openai_tools_agent
agent = create_openai_tools_agent(
    llm=your_llm,
    tools=all_tools,
    prompt=your_prompt
)
"""
