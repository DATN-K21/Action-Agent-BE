# Ingest Service

A dedicated Celery worker service that processes document ingestion and search tasks from the message queue.

## Overview

The Ingest Service is responsible for:

1. Consuming messages from RabbitMQ queues
2. Processing document ingestion tasks (adding and removing)
3. Performing vector and text searches against PGVector
4. Handling communication with AI Service for status updates

## Queues

This service listens to the following queues:

- `document.processing`: For document ingestion and deletion
- `document.search`: For document search operations
- `ping`: For health check and monitoring

## Running Locally

To run the service locally:

```bash
# Install dependencies with uv
uv pip install -e .

# Set environment variables
export PGVECTOR_POSTGRES_URL_PATH=postgres:postgres@localhost:5432/postgres
export PGVECTOR_POSTGRES_SCHEMA=public
export RABBITMQ_URL=amqp://guest:guest@localhost:5672/
export REDIS_URL=redis://localhost:6379/0
export CELERY_CONCURRENCY=2

# Run the service
python -m app.main
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PGVECTOR_POSTGRES_URL_PATH` | PostgreSQL connection URL | None |
| `PGVECTOR_POSTGRES_SCHEMA` | PostgreSQL schema name | `public` |
| `RABBITMQ_URL` | RabbitMQ connection URL | None |
| `REDIS_URL` | Redis connection URL | None |
| `CELERY_CONCURRENCY` | Number of concurrent worker processes | CPU count |
| `DEBUG_MODE` | Enable debug logging | `False` |
| `LOGGING_LOG_LEVEL` | Log level (DEBUG, INFO, etc.) | `INFO` |

## Docker

Build and run using Docker:

```bash
docker build -t ingest-service .
docker run -e PGVECTOR_POSTGRES_URL_PATH=postgres:postgres@postgres:5432/postgres -e RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/ -e REDIS_URL=redis://redis:6379/0 ingest-service
```

## Scaling

This service can be horizontally scaled by running multiple instances. The Celery workers will automatically load balance tasks across instances.
