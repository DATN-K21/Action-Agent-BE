# Use Python 3.11 slim base image
FROM python:3.11-slim AS final

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_VERSION=1.8.2 \
    POETRY_NO_INTERACTION=1

# Install system dependencies and Poetry
RUN apt-get install -y --no-install-recommends curl gcc libpq-dev && \
    pip install "poetry==$POETRY_VERSION" && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy only dependency files first (leverage Docker cache)
COPY pyproject.toml poetry.lock ./

# Install dependencies globally (no virtual environment)
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --only main

# Copy the application code
COPY . .

# Expose the application port
EXPOSE 5001

# Default command to run the app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5001", "--reload"]
