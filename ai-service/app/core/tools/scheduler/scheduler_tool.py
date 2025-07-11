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
    timezone: str = Field("UTC", description="Timezone for the schedule")
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
        "Accept": "application/json"
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            if method.upper() == "GET":
                response = await client.get(url, headers=headers, params=params)
            elif method.upper() == "POST":
                if endpoint.startswith("/") and "created_by" not in (params or {}):
                    # Add created_by parameter for job creation
                    if params is None:
                        params = {}
                    params["created_by"] = user_id
                response = await client.post(url, headers=headers, json=data, params=params)
            elif method.upper() == "PUT":
                response = await client.put(url, headers=headers, json=data)
            elif method.upper() == "DELETE":
                response = await client.delete(url, headers=headers)
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


async def create_scheduled_job(**kwargs) -> str:
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
            "timezone": job_data.timezone,
            "is_active": job_data.is_active,
            "ai_service_endpoint": "/api/v1/team/stream"  # Default endpoint for team streaming
        }
        
        result = await _make_scheduler_request("POST", "", data=payload)
        
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


async def get_scheduled_jobs(**kwargs) -> str:
    """
    Retrieve a list of scheduled jobs with optional filtering.
    
    This function fetches jobs from the scheduler service with optional
    filters for status, type, and pagination.
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
        
        result = await _make_scheduler_request("GET", "", params=params)
        
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


async def get_job_details(**kwargs) -> str:
    """
    Get detailed information about a specific job.
    
    This function retrieves detailed information about a job including
    its configuration, status, and execution history.
    """
    try:
        input_data = JobControlInput(**kwargs)
        
        result = await _make_scheduler_request("GET", f"/{input_data.job_id}")
        
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


async def update_scheduled_job(**kwargs) -> str:
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
        if input_data.is_active is not None:
            payload["is_active"] = input_data.is_active
        
        if not payload:
            return json.dumps({
                "success": False,
                "error": "No fields to update"
            }, indent=2)
        
        result = await _make_scheduler_request("PUT", f"/{input_data.job_id}", data=payload)
        
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


async def delete_scheduled_job(**kwargs) -> str:
    """
    Delete a scheduled job.
    
    This function removes a job from the scheduler, stopping all future executions.
    """
    try:
        input_data = JobControlInput(**kwargs)
        
        result = await _make_scheduler_request("DELETE", f"/{input_data.job_id}")
        
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


async def run_job_now(**kwargs) -> str:
    """
    Trigger immediate execution of a scheduled job.
    
    This function manually triggers a job to run immediately,
    regardless of its schedule.
    """
    try:
        input_data = JobControlInput(**kwargs)
        
        result = await _make_scheduler_request("POST", f"/{input_data.job_id}/run")
        
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


async def pause_scheduled_job(**kwargs) -> str:
    """
    Pause a scheduled job.
    
    This function pauses a job, preventing it from executing
    until it is resumed.
    """
    try:
        input_data = JobControlInput(**kwargs)
        
        result = await _make_scheduler_request("POST", f"/{input_data.job_id}/pause")
        
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


async def resume_scheduled_job(**kwargs) -> str:
    """
    Resume a paused scheduled job.
    
    This function resumes a previously paused job,
    allowing it to execute according to its schedule.
    """
    try:
        input_data = JobControlInput(**kwargs)
        
        result = await _make_scheduler_request("POST", f"/{input_data.job_id}/resume")
        
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


async def get_job_executions(**kwargs) -> str:
    """
    Get execution history for a specific job.
    
    This function retrieves the execution history of a job,
    including success/failure status and execution details.
    """
    try:
        input_data = JobControlInput(**kwargs)
        
        result = await _make_scheduler_request("GET", f"/{input_data.job_id}/executions")
        
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


async def validate_cron_expression(**kwargs) -> str:
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
        
        result = await _make_scheduler_request("POST", "/validate-cron", data=payload)
        
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


# Create the scheduler tools
create_job_tool = StructuredTool.from_function(
    func=create_scheduled_job,
    name="Create Scheduled Job",
    description="Create a new scheduled job that will automatically execute AI prompts at specified times. "
                "Use cron expressions for recurring jobs (e.g., '0 9 * * *' for 9 AM daily, '0 */2 * * *' for every 2 hours). "
                "Jobs will send prompts to the specified team for processing.",
    args_schema=CreateJobInput,
    return_direct=False,
)

get_jobs_tool = StructuredTool.from_function(
    func=get_scheduled_jobs,
    name="Get Scheduled Jobs",
    description="Retrieve a list of scheduled jobs with optional filtering by status, type, and pagination. "
                "Useful for monitoring and managing existing scheduled tasks.",
    args_schema=GetJobsInput,
    return_direct=False,
)

get_job_details_tool = StructuredTool.from_function(
    func=get_job_details,
    name="Get Job Details",
    description="Get detailed information about a specific scheduled job including its configuration, "
                "status, execution history, and schedule information.",
    args_schema=JobControlInput,
    return_direct=False,
)

update_job_tool = StructuredTool.from_function(
    func=update_scheduled_job,
    name="Update Scheduled Job",
    description="Update an existing scheduled job's configuration including name, description, "
                "schedule (cron expression), prompt, or active status.",
    args_schema=UpdateJobInput,
    return_direct=False,
)

delete_job_tool = StructuredTool.from_function(
    func=delete_scheduled_job,
    name="Delete Scheduled Job",
    description="Delete a scheduled job permanently. This will stop all future executions of the job.",
    args_schema=JobControlInput,
    return_direct=False,
)

run_job_tool = StructuredTool.from_function(
    func=run_job_now,
    name="Run Job Now",
    description="Trigger immediate execution of a scheduled job, regardless of its normal schedule. "
                "Useful for testing jobs or running them on-demand.",
    args_schema=JobControlInput,
    return_direct=False,
)

pause_job_tool = StructuredTool.from_function(
    func=pause_scheduled_job,
    name="Pause Scheduled Job",
    description="Pause a scheduled job to prevent it from executing until resumed. "
                "The job configuration is preserved and can be resumed later.",
    args_schema=JobControlInput,
    return_direct=False,
)

resume_job_tool = StructuredTool.from_function(
    func=resume_scheduled_job,
    name="Resume Scheduled Job",
    description="Resume a previously paused scheduled job, allowing it to execute according to its schedule again.",
    args_schema=JobControlInput,
    return_direct=False,
)

get_executions_tool = StructuredTool.from_function(
    func=get_job_executions,
    name="Get Job Executions",
    description="Get the execution history for a specific job, including success/failure status, "
                "execution times, and any error messages.",
    args_schema=JobControlInput,
    return_direct=False,
)

validate_cron_tool = StructuredTool.from_function(
    func=validate_cron_expression,
    name="Validate Cron Expression",
    description="Validate a cron expression and see when it would execute. "
                "Returns validation status and next execution times. "
                "Helpful for testing cron expressions before creating jobs.",
    args_schema=ValidateCronInput,
    return_direct=False,
)
