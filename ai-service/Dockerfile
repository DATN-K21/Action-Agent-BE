FROM python:3.11-slim-bullseye AS final

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock .python-version ./ 
RUN uv sync --frozen --no-cache

COPY . .

EXPOSE 5001
CMD ["/app/.venv/bin/fastapi", "run", "app/main.py", "--port", "5001"]
