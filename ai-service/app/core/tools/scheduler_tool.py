"""
Scheduler Tool for AI Service

This tool provides scheduling capabilities by communicating with the scheduler-service.
It allows creating, managing, and monitoring scheduled tasks that will automatically
execute AI prompts based on specified schedules.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import httpx
from langchain.tools import StructuredTool
from pydantic import BaseModel, Field

from app.core import logging
from app.core.settings import env_settings

logger = logging.get_logger(__name__)

# Scheduler service URL - configured from environment settings
SCHEDULER_SERVICE_URL = env_settings.SCHEDULER_SERVICE_URL


class CreateJobInput(BaseModel):
    """Input schema for creating a scheduled job."""
    name: str = Field(..., description="Name of the job")
    description: Optional[str] = Field(None, description="Description of the job")
    job_type: str = Field("recurring", description="Type of job: 'one_time' or 'recurring'")
    cron_expression: Optional[str] = Field(None, description="Cron expression for recurring jobs (e.g., '0 9 * * *' for 9 AM daily)")
    prompt: str = Field(..., description="The prompt to send to AI service when job executes")
    team_id: str = Field(..., description="Team ID that will process the prompt")
    assistant_id: str = Field(..., description="Assistant ID that will process the prompt")
    job_config: Optional[Dict[str, Any]] = Field(None, description="Additional job configuration")
    max_retries: int = Field(3, description="Maximum number of retries")
    timeout_seconds: int = Field(300, description="Job timeout in seconds")
    timezone: str = Field("UTC", description="Timezone for the schedule")
    is_active: bool = Field(True, description="Whether the job should be active")


class GetJobsInput(BaseModel):
    """Input schema for retrieving jobs."""
    status: Optional[str] = Field(None, description="Filter by job status: 'pending', 'running', 'completed', 'failed', 'paused'")
    job_type: Optional[str] = Field(None, description="Filter by job type: 'one_time' or 'recurring'")
    assistant_id: Optional[str] = Field(None, description="Filter by assistant ID")
    team_id: Optional[str] = Field(None, description="Filter by team ID")
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
    team_id: Optional[str] = Field(None, description="New team ID")
    assistant_id: Optional[str] = Field(None, description="New assistant ID")
    job_config: Optional[Dict[str, Any]] = Field(None, description="New job configuration")
    max_retries: Optional[int] = Field(None, description="New maximum number of retries")
    timeout_seconds: Optional[int] = Field(None, description="New timeout in seconds")
    timezone: Optional[str] = Field(None, description="New timezone")
    is_active: Optional[bool] = Field(None, description="Whether the job should be active")


class ValidateCronInput(BaseModel):
    """Input schema for validating cron expressions."""
    cron_expression: str = Field(..., description="Cron expression to validate")
    timezone: str = Field("UTC", description="Timezone for validation")


async def _make_scheduler_request(
    method: str,
    endpoint: str,
    data: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
    user_id: str = "system"
) -> Dict[str, Any]:
    """Make HTTP request to scheduler service."""
    url = f"{SCHEDULER_SERVICE_URL}/api/v1/jobs{endpoint}"
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-User-ID": user_id  # Add user ID to headers for context
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            if method.upper() == "GET":
                # Add user_id to params for filtering user's jobs
                if params is None:
                    params = {}
                params["user_id"] = user_id
                response = await client.get(url, headers=headers, params=params)
            elif method.upper() == "POST":
                # Add user context to job creation
                if data and not endpoint.startswith("/validate-cron"):
                    data["created_by"] = user_id
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


async def create_scheduled_job(user_id: str = "system", **kwargs) -> str:
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
            "team_id": job_data.team_id,
            "assistant_id": job_data.assistant_id,
            "job_config": job_data.job_config,
            "max_retries": job_data.max_retries,
            "timeout_seconds": job_data.timeout_seconds,
            "timezone": job_data.timezone,
            "is_active": job_data.is_active
        }
        
        result = await _make_scheduler_request("POST", "", data=payload, user_id=user_id)
        
        if "error" in result:
            return json.dumps({
                "success": False,
                "error": result["error"]
            }, indent=2)
        
        return json.dumps({
            "success": True,
            "message": "Job created successfully",
            "job": result
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error creating scheduled job: {str(e)}")
        return json.dumps({
            "success": False,
            "error": f"Failed to create job: {str(e)}"
        }, indent=2)


async def get_scheduled_jobs(user_id: str = "system", **kwargs) -> str:
    """
    Retrieve a list of scheduled jobs with optional filtering.
    
    This function fetches jobs from the scheduler service with optional
    filters for status, type, assistant_id, team_id, and pagination.
    """
    try:
        input_data = GetJobsInput(**kwargs)
        
        params = {
            "skip": input_data.skip,
            "limit": input_data.limit
        }
        
        if input_data.status:
            params["status"] = input_data.status
        if input_data.job_type:
            params["job_type"] = input_data.job_type
        if input_data.assistant_id:
            params["assistant_id"] = input_data.assistant_id
        if input_data.team_id:
            params["team_id"] = input_data.team_id
        
        result = await _make_scheduler_request("GET", "", params=params, user_id=user_id)
        
        if "error" in result:
            return json.dumps({
                "success": False,
                "error": result["error"]
            }, indent=2)
        
        return json.dumps({
            "success": True,
            "jobs": result
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error retrieving scheduled jobs: {str(e)}")
        return json.dumps({
            "success": False,
            "error": f"Failed to retrieve jobs: {str(e)}"
        }, indent=2)


async def get_job_details(user_id: str = "system", **kwargs) -> str:
    """
    Get detailed information about a specific job.
    
    This function retrieves detailed information about a job including
    its configuration, status, and execution history.
    """
    try:
        input_data = JobControlInput(**kwargs)
        
        result = await _make_scheduler_request("GET", f"/{input_data.job_id}", user_id=user_id)
        
        if "error" in result:
            return json.dumps({
                "success": False,
                "error": result["error"]
            }, indent=2)
        
        return json.dumps({
            "success": True,
            "job": result
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error getting job details: {str(e)}")
        return json.dumps({
            "success": False,
            "error": f"Failed to get job details: {str(e)}"
        }, indent=2)


async def update_scheduled_job(user_id: str = "system", **kwargs) -> str:
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
        if input_data.team_id is not None:
            payload["team_id"] = input_data.team_id
        if input_data.assistant_id is not None:
            payload["assistant_id"] = input_data.assistant_id
        if input_data.job_config is not None:
            payload["job_config"] = input_data.job_config
        if input_data.max_retries is not None:
            payload["max_retries"] = input_data.max_retries
        if input_data.timeout_seconds is not None:
            payload["timeout_seconds"] = input_data.timeout_seconds
        if input_data.timezone is not None:
            payload["timezone"] = input_data.timezone
        if input_data.is_active is not None:
            payload["is_active"] = input_data.is_active
        
        if not payload:
            return json.dumps({
                "success": False,
                "error": "No fields to update"
            }, indent=2)
        
        result = await _make_scheduler_request("PUT", f"/{input_data.job_id}", data=payload, user_id=user_id)
        
        if "error" in result:
            return json.dumps({
                "success": False,
                "error": result["error"]
            }, indent=2)
        
        return json.dumps({
            "success": True,
            "message": "Job updated successfully",
            "job": result
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error updating scheduled job: {str(e)}")
        return json.dumps({
            "success": False,
            "error": f"Failed to update job: {str(e)}"
        }, indent=2)


async def delete_scheduled_job(user_id: str = "system", **kwargs) -> str:
    """
    Delete a scheduled job.
    
    This function removes a job from the scheduler, stopping all future executions.
    """
    try:
        input_data = JobControlInput(**kwargs)
        
        result = await _make_scheduler_request("DELETE", f"/{input_data.job_id}", user_id=user_id)
        
        if "error" in result:
            return json.dumps({
                "success": False,
                "error": result["error"]
            }, indent=2)
        
        return json.dumps({
            "success": True,
            "message": "Job deleted successfully"
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error deleting scheduled job: {str(e)}")
        return json.dumps({
            "success": False,
            "error": f"Failed to delete job: {str(e)}"
        }, indent=2)


async def run_job_now(user_id: str = "system", **kwargs) -> str:
    """
    Trigger immediate execution of a scheduled job.
    
    This function manually triggers a job to run immediately,
    regardless of its schedule.
    """
    try:
        input_data = JobControlInput(**kwargs)
        
        result = await _make_scheduler_request("POST", f"/{input_data.job_id}/run", user_id=user_id)
        
        if "error" in result:
            return json.dumps({
                "success": False,
                "error": result["error"]
            }, indent=2)
        
        return json.dumps({
            "success": True,
            "message": "Job execution triggered successfully",
            "result": result
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error running job: {str(e)}")
        return json.dumps({
            "success": False,
            "error": f"Failed to run job: {str(e)}"
        }, indent=2)


async def pause_scheduled_job(user_id: str = "system", **kwargs) -> str:
    """
    Pause a scheduled job.
    
    This function pauses a job, preventing it from executing
    until it is resumed.
    """
    try:
        input_data = JobControlInput(**kwargs)
        
        result = await _make_scheduler_request("POST", f"/{input_data.job_id}/pause", user_id=user_id)
        
        if "error" in result:
            return json.dumps({
                "success": False,
                "error": result["error"]
            }, indent=2)
        
        return json.dumps({
            "success": True,
            "message": "Job paused successfully"
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error pausing job: {str(e)}")
        return json.dumps({
            "success": False,
            "error": f"Failed to pause job: {str(e)}"
        }, indent=2)


async def resume_scheduled_job(user_id: str = "system", **kwargs) -> str:
    """
    Resume a paused scheduled job.
    
    This function resumes a previously paused job,
    allowing it to execute according to its schedule.
    """
    try:
        input_data = JobControlInput(**kwargs)
        
        result = await _make_scheduler_request("POST", f"/{input_data.job_id}/resume", user_id=user_id)
        
        if "error" in result:
            return json.dumps({
                "success": False,
                "error": result["error"]
            }, indent=2)
        
        return json.dumps({
            "success": True,
            "message": "Job resumed successfully"
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error resuming job: {str(e)}")
        return json.dumps({
            "success": False,
            "error": f"Failed to resume job: {str(e)}"
        }, indent=2)


async def get_job_executions(user_id: str = "system", **kwargs) -> str:
    """
    Get execution history for a specific job.
    
    This function retrieves the execution history of a job,
    including success/failure status and execution details.
    """
    try:
        input_data = JobControlInput(**kwargs)
        
        result = await _make_scheduler_request("GET", f"/{input_data.job_id}/executions", user_id=user_id)
        
        if "error" in result:
            return json.dumps({
                "success": False,
                "error": result["error"]
            }, indent=2)
        
        return json.dumps({
            "success": True,
            "executions": result
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error getting job executions: {str(e)}")
        return json.dumps({
            "success": False,
            "error": f"Failed to get job executions: {str(e)}"
        }, indent=2)


async def validate_cron_expression(user_id: str = "system", **kwargs) -> str:
    """
    Validate a cron expression and get next run times.
    
    This function validates a cron expression and returns
    information about when it would execute.
    """
    try:
        input_data = ValidateCronInput(**kwargs)
        
        payload = {
            "cron_expression": input_data.cron_expression,
            "timezone": input_data.timezone
        }
        
        result = await _make_scheduler_request("POST", "/validate-cron", data=payload, user_id=user_id)
        
        if "error" in result:
            return json.dumps({
                "success": False,
                "error": result["error"]
            }, indent=2)
        
        return json.dumps({
            "success": True,
            "validation": result
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error validating cron expression: {str(e)}")
        return json.dumps({
            "success": False,
            "error": f"Failed to validate cron expression: {str(e)}"
        }, indent=2)


def create_scheduler_tools(user_id: str, timezone: str = "UTC", team_id: Optional[str] = None, assistant_id: Optional[str] = None):
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
        # Set default team_id if provided and not in kwargs
        if team_id and "team_id" not in kwargs:
            kwargs["team_id"] = team_id
        
        # Set default timezone if not provided
        if "timezone" not in kwargs:
            kwargs["timezone"] = timezone
            
        return await create_scheduled_job(user_id=user_id, **kwargs)
    
    async def get_jobs_with_context(**kwargs) -> str:
        """Get scheduled jobs with user context."""
        return await get_scheduled_jobs(user_id=user_id, **kwargs)
    
    async def get_job_details_with_context(**kwargs) -> str:
        """Get job details with user context."""
        return await get_job_details(user_id=user_id, **kwargs)
    
    async def update_job_with_context(**kwargs) -> str:
        """Update scheduled job with user context."""
        return await update_scheduled_job(user_id=user_id, **kwargs)
    
    async def delete_job_with_context(**kwargs) -> str:
        """Delete scheduled job with user context."""
        return await delete_scheduled_job(user_id=user_id, **kwargs)
    
    async def run_job_with_context(**kwargs) -> str:
        """Run job now with user context."""
        return await run_job_now(user_id=user_id, **kwargs)
    
    async def pause_job_with_context(**kwargs) -> str:
        """Pause job with user context."""
        return await pause_scheduled_job(user_id=user_id, **kwargs)
    
    async def resume_job_with_context(**kwargs) -> str:
        """Resume job with user context."""
        return await resume_scheduled_job(user_id=user_id, **kwargs)
    
    async def get_executions_with_context(**kwargs) -> str:
        """Get job executions with user context."""
        return await get_job_executions(user_id=user_id, **kwargs)
    
    async def validate_cron_with_context(**kwargs) -> str:
        """Validate cron expression with user context."""
        # Set default timezone if not provided
        if "timezone" not in kwargs:
            kwargs["timezone"] = timezone
        return await validate_cron_expression(user_id=user_id, **kwargs)
    
    # Create the tools with context
    tools = {
        "create_job": StructuredTool.from_function(
            func=create_job_with_context,
            name="Create Scheduled Job",
            description=f"Create a new scheduled job for user {user_id} that will automatically execute AI prompts at specified times. "
                       "Use cron expressions for recurring jobs (e.g., '0 9 * * *' for 9 AM daily, '0 */2 * * *' for every 2 hours). "
                       f"Jobs will be created in {timezone} timezone. "
                       + (f"Default team: {team_id}. " if team_id else ""),
            args_schema=CreateJobInput,
            return_direct=False,
        ),
        
        "get_jobs": StructuredTool.from_function(
            func=get_jobs_with_context,
            name="Get Scheduled Jobs",
            description=f"Retrieve scheduled jobs for user {user_id} with optional filtering by status, type, assistant_id, team_id, and pagination. "
                       "Useful for monitoring and managing existing scheduled tasks.",
            args_schema=GetJobsInput,
            return_direct=False,
        ),
        
        "get_job_details": StructuredTool.from_function(
            func=get_job_details_with_context,
            name="Get Job Details",
            description=f"Get detailed information about a specific scheduled job for user {user_id} including configuration, "
                       "status, execution history, and schedule information.",
            args_schema=JobControlInput,
            return_direct=False,
        ),
        
        "update_job": StructuredTool.from_function(
            func=update_job_with_context,
            name="Update Scheduled Job",
            description=f"Update an existing scheduled job for user {user_id}. Can modify name, description, "
                       "schedule (cron expression), prompt, or active status.",
            args_schema=UpdateJobInput,
            return_direct=False,
        ),
        
        "delete_job": StructuredTool.from_function(
            func=delete_job_with_context,
            name="Delete Scheduled Job",
            description=f"Delete a scheduled job for user {user_id} permanently. This will stop all future executions of the job.",
            args_schema=JobControlInput,
            return_direct=False,
        ),
        
        "run_job": StructuredTool.from_function(
            func=run_job_with_context,
            name="Run Job Now",
            description=f"Trigger immediate execution of a scheduled job for user {user_id}, regardless of its normal schedule. "
                       "Useful for testing jobs or running them on-demand.",
            args_schema=JobControlInput,
            return_direct=False,
        ),
        
        "pause_job": StructuredTool.from_function(
            func=pause_job_with_context,
            name="Pause Scheduled Job",
            description=f"Pause a scheduled job for user {user_id} to prevent it from executing until resumed. "
                       "The job configuration is preserved and can be resumed later.",
            args_schema=JobControlInput,
            return_direct=False,
        ),
        
        "resume_job": StructuredTool.from_function(
            func=resume_job_with_context,
            name="Resume Scheduled Job",
            description=f"Resume a previously paused scheduled job for user {user_id}, allowing it to execute according to its schedule again.",
            args_schema=JobControlInput,
            return_direct=False,
        ),
        
        "get_executions": StructuredTool.from_function(
            func=get_executions_with_context,
            name="Get Job Executions",
            description=f"Get the execution history for a specific job for user {user_id}, including success/failure status, "
                       "execution times, and any error messages.",
            args_schema=JobControlInput,
            return_direct=False,
        ),
        
        "validate_cron": StructuredTool.from_function(
            func=validate_cron_with_context,
            name="Validate Cron Expression",
            description=f"Validate a cron expression for user {user_id} in {timezone} timezone and see when it would execute. "
                       "Returns validation status and next execution times. "
                       "Helpful for testing cron expressions before creating jobs.",
            args_schema=ValidateCronInput,
            return_direct=False,
        )
    }
    
    return tools


# Legacy tools for backward compatibility (deprecated)
# These will be removed in future versions
def _get_legacy_tools():
    """Get legacy tools for backward compatibility."""
    legacy_tools = create_scheduler_tools(user_id="system", timezone="UTC")
    return {
        "create_job_tool": legacy_tools["create_job"],
        "get_jobs_tool": legacy_tools["get_jobs"],
        "get_job_details_tool": legacy_tools["get_job_details"],
        "update_job_tool": legacy_tools["update_job"],
        "delete_job_tool": legacy_tools["delete_job"],
        "run_job_tool": legacy_tools["run_job"],
        "pause_job_tool": legacy_tools["pause_job"],
        "resume_job_tool": legacy_tools["resume_job"],
        "get_executions_tool": legacy_tools["get_executions"],
        "validate_cron_tool": legacy_tools["validate_cron"]
    }

# Create legacy tools for backward compatibility
_legacy = _get_legacy_tools()
create_job_tool = _legacy["create_job_tool"]
get_jobs_tool = _legacy["get_jobs_tool"]
get_job_details_tool = _legacy["get_job_details_tool"]
update_job_tool = _legacy["update_job_tool"]
delete_job_tool = _legacy["delete_job_tool"]
run_job_tool = _legacy["run_job_tool"]
pause_job_tool = _legacy["pause_job_tool"]
resume_job_tool = _legacy["resume_job_tool"]
get_executions_tool = _legacy["get_executions_tool"]
validate_cron_tool = _legacy["validate_cron_tool"]


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
