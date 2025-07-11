# Scheduler Tool for AI Service

This tool provides comprehensive scheduling capabilities for the AI service by communicating with the scheduler-service. It allows users to create, manage, and monitor scheduled tasks that automatically execute AI prompts based on specified schedules.

## Features

- **Create Scheduled Jobs**: Schedule one-time or recurring AI prompt executions
- **Job Management**: Update, pause, resume, and delete scheduled jobs
- **Job Monitoring**: View job details, execution history, and status
- **Cron Validation**: Validate cron expressions and preview execution times
- **Manual Execution**: Trigger jobs manually for testing or immediate execution

## Tool Functions

### 1. Create Scheduled Job
Creates a new scheduled job that will automatically execute AI prompts.

**Parameters:**
- `name`: Job name (required)
- `description`: Job description (optional)
- `job_type`: "one_time" or "recurring" (default: "recurring")
- `cron_expression`: Cron expression for recurring jobs (e.g., "0 9 * * *" for 9 AM daily)
- `prompt`: The prompt to send to AI service when job executes (required)
- `team_id`: Team ID that will process the prompt (required)
- `timezone`: Timezone for the schedule (default: "UTC")
- `is_active`: Whether the job should be active (default: true)

**Example:**
```python
create_scheduled_job(
    name="Daily Report Generation",
    description="Generate daily team summary reports",
    job_type="recurring",
    cron_expression="0 9 * * *",  # 9 AM daily
    prompt="Generate a comprehensive daily report summarizing team activities and progress",
    team_id="team-123",
    timezone="UTC",
    is_active=True
)
```

### 2. Get Scheduled Jobs
Retrieve a list of scheduled jobs with optional filtering.

**Parameters:**
- `status`: Filter by job status ("pending", "running", "completed", "failed", "paused")
- `job_type`: Filter by job type ("one_time", "recurring")
- `limit`: Maximum number of jobs to return (default: 10)
- `skip`: Number of jobs to skip for pagination (default: 0)

### 3. Get Job Details
Get detailed information about a specific job.

**Parameters:**
- `job_id`: ID of the job to retrieve (required)

### 4. Update Scheduled Job
Update an existing scheduled job's configuration.

**Parameters:**
- `job_id`: ID of the job to update (required)
- `name`: New job name (optional)
- `description`: New job description (optional)
- `cron_expression`: New cron expression (optional)
- `prompt`: New prompt to execute (optional)
- `is_active`: Whether the job should be active (optional)

### 5. Delete Scheduled Job
Delete a scheduled job permanently.

**Parameters:**
- `job_id`: ID of the job to delete (required)

### 6. Run Job Now
Trigger immediate execution of a scheduled job.

**Parameters:**
- `job_id`: ID of the job to run (required)

### 7. Pause Scheduled Job
Pause a scheduled job to prevent execution.

**Parameters:**
- `job_id`: ID of the job to pause (required)

### 8. Resume Scheduled Job
Resume a previously paused scheduled job.

**Parameters:**
- `job_id`: ID of the job to resume (required)

### 9. Get Job Executions
Get execution history for a specific job.

**Parameters:**
- `job_id`: ID of the job to get executions for (required)

### 10. Validate Cron Expression
Validate a cron expression and see when it would execute.

**Parameters:**
- `cron_expression`: Cron expression to validate (required)
- `timezone`: Timezone for validation (default: "UTC")

## Cron Expression Examples

- `0 9 * * *` - Daily at 9:00 AM
- `0 9 * * 1` - Every Monday at 9:00 AM
- `0 */2 * * *` - Every 2 hours
- `30 14 * * 1-5` - Weekdays at 2:30 PM
- `0 0 1 * *` - First day of every month at midnight
- `0 9 1 1 *` - January 1st at 9:00 AM (yearly)

## Configuration

The scheduler tool requires the following environment configuration:

```env
SCHEDULER_SERVICE_URL=http://localhost:15400
```

This should point to your scheduler-service instance.

## Integration with AI Teams

When a scheduled job executes, it automatically:

1. Sends the specified prompt to the configured team
2. Uses the `/api/v1/team/stream` endpoint for processing
3. Logs execution results and status
4. Handles retries according to job configuration

## Error Handling

The tool provides comprehensive error handling:

- **Connection Errors**: Graceful handling of scheduler service unavailability
- **Validation Errors**: Clear error messages for invalid inputs
- **HTTP Errors**: Detailed error reporting from the scheduler service
- **Timeout Handling**: Prevents hanging requests with 30-second timeout

## Usage in AI Conversations

Users can interact with the scheduler through natural language:

- "Schedule a daily report generation at 9 AM"
- "Create a weekly team sync reminder for Mondays"
- "Pause the marketing automation job"
- "Show me all active scheduled jobs"
- "Run the data backup job now"

The AI assistant will automatically use the appropriate scheduler tool functions based on user intent.

## Dependencies

This tool depends on:

- `httpx` for HTTP client functionality
- `langchain.tools` for tool structure
- `pydantic` for data validation
- The scheduler-service for job management

## Testing

Run the included test script to verify integration:

```bash
python app/core/tools/scheduler/test_scheduler_tool.py
```

This will test basic functionality and verify the connection to the scheduler service.
