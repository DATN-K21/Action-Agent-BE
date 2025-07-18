# Scheduler Service

The Scheduler Service for the Action-Executing AI Agent system. This service provides job scheduling capabilities with CRUD operations for managing scheduled tasks.

## Features

- **Job Scheduling**: Create, read, update, and delete scheduled jobs
- **Cron Support**: Uses cron expressions for flexible scheduling
- **Database Integration**: PostgreSQL for persistent job storage
- **Redis Integration**: For caching and job state management
- **APScheduler**: Advanced Python Scheduler for job execution
- **FastAPI**: Modern, fast web framework for building APIs

## API Endpoints

- `POST /jobs` - Create a new scheduled job
- `GET /jobs` - List all jobs
- `GET /jobs/{job_id}` - Get specific job details
- `PUT /jobs/{job_id}` - Update a job
- `DELETE /jobs/{job_id}` - Delete a job
- `POST /jobs/{job_id}/run` - Manually trigger a job
- `GET /jobs/{job_id}/logs` - Get job execution logs

## Environment Variables

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `AI_SERVICE_URL`: URL of the AI service for job execution
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

## Development

1. Install dependencies: `uv sync`
2. Run the service: `uvicorn app.main:app --reload`
3. Access API docs: `http://localhost:8000/docs`

## Job Types

Jobs can be configured to:
- Send prompts to AI service team endpoints
- Execute one-time or recurring tasks
- Use cron expressions for complex scheduling
- Include team context and configuration
