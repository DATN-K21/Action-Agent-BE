@echo off
echo Starting Scheduler Service...

rem Check if environment variables are set
if not defined DATABASE_URL (
    echo ERROR: DATABASE_URL environment variable is not set
    exit /b 1
)

if not defined AI_SERVICE_URL (
    echo ERROR: AI_SERVICE_URL environment variable is not set
    exit /b 1
)

echo Environment variables validated successfully

rem Run database migrations
echo Running database migrations...
python -m app.migrate

rem Start the scheduler service
echo Starting scheduler service...
if not defined PORT set PORT=8000
if not defined DEBUG_SERVER set DEBUG_SERVER=false
uvicorn app.main:app --host 0.0.0.0 --port %PORT% --reload=%DEBUG_SERVER%
