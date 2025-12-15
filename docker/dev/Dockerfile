# docker/dev/Dockerfile
FROM python:3.12-slim-bookworm

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/src

WORKDIR /app

# Install system dependencies (needed for some python packages or pg drivers)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy project definition
COPY pyproject.toml uv.lock ./

# Install dependencies (system-wide inside container, no venv needed for docker)
RUN uv sync --frozen --no-install-project

COPY . .

RUN uv sync --frozen

# Command is handled by docker-compose usually, but fallback here
CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
