# Use Python 3.11 slim base image
FROM python:3.11-slim-bullseye AS final

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set working directory
WORKDIR /app

# Copy only dependency files first (leverage Docker cache)
COPY pyproject.toml uv.lock .python-version ./ 

# Install dependencies
RUN uv sync --frozen --no-cache

# Copy the application code
COPY . .

# Expose the port
EXPOSE 5001

# Default command to run the app using `fastapi run`
CMD ["/app/.venv/bin/fastapi", "run", "app/main.py", "--port", "5001"]
