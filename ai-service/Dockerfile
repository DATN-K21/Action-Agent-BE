FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_VERSION=1.8.2

# Install system dependencies and Poetry
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl gcc libpq-dev && \
    pip install "poetry==$POETRY_VERSION" && \
    apt-get remove -y gcc libpq-dev && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy dependency files first for better caching
COPY pyproject.toml poetry.lock* ./

# Install dependencies without virtual environments
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --only main && \
    poetry cache clear --all pypi

# Copy the rest of the application code
COPY . .

# Default command to run the app
ENTRYPOINT ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5001", "--reload"]
