FROM python:3.11-slim-bookworm AS final

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Copy uv from its official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Create app directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./ 

# Install dependencies with uv
RUN uv sync --frozen --no-cache

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash ingest
RUN chown -R ingest:ingest /app
USER ingest

# Command to start Celery worker
CMD [ "celery", "--app=app.main", "worker" ]
