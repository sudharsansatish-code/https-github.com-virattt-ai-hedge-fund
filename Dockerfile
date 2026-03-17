# AI Hedge Fund - Docker Image
# Multi-stage build for smaller final image

FROM python:3.12-slim AS base

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry==1.8.4

# Copy dependency files first (for Docker layer caching)
COPY pyproject.toml poetry.lock* ./

# Install dependencies (no dev deps in production)
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --only main

# Copy application code
COPY . .

# Create data directory for SQLite and logs
RUN mkdir -p /app/data /app/config

# Expose FastAPI port (Render sets PORT env var)
ENV PORT=8000
EXPOSE ${PORT}

# Production command: $PORT for Render, keep-alive > Render's 60s default
CMD ["sh", "-c", "python -m uvicorn app.backend.main:app --host 0.0.0.0 --port ${PORT} --timeout-keep-alive 65"]
