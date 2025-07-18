#!/bin/bash

# Startup script for scheduler-service

echo "Starting Scheduler Service..."

# Check if environment variables are set
if [ -z "$DATABASE_URL" ]; then
    echo "ERROR: DATABASE_URL environment variable is not set"
    exit 1
fi

if [ -z "$AI_SERVICE_URL" ]; then
    echo "ERROR: AI_SERVICE_URL environment variable is not set"
    exit 1
fi

echo "Environment variables validated successfully"

# Run database migrations
echo "Running database migrations..."
python -m app.migrate

# Start the scheduler service
echo "Starting scheduler service..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --reload=${DEBUG_SERVER:-false}
