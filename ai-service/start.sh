#!/bin/bash
set -e

# Production startup script for AI Service
# This script ensures migrations are run before starting the application

echo "=== AI Service Startup Script ==="
echo "Starting at: $(date)"

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
fi

# Check database connection
echo "Checking database connection..."
if ! docker exec ai-database pg_isready -U postgres > /dev/null 2>&1; then
    echo "ERROR: Database is not ready. Please ensure PostgreSQL container is running."
    echo "Run: cd /workspaces/Action-Agent-BE && docker-compose up -d"
    exit 1
fi

echo "Database is ready ✓"

# Run database migrations
echo "Running database migrations..."
alembic upgrade head
echo "Migrations completed ✓"

# Start the application
echo "Starting FastAPI application..."
echo "Access the API at: http://localhost:15001"
echo "Press Ctrl+C to stop the server"
echo "=========================="

exec uvicorn app.main:app --host 0.0.0.0 --port 15001 --reload
