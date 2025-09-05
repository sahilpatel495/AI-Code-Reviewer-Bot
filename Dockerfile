# AI Code Reviewer Bot - Dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    nodejs \
    npm \
    openjdk-11-jdk \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js tools
RUN npm install -g eslint prettier typescript

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install additional Python tools
RUN pip install --no-cache-dir \
    ruff \
    black \
    bandit \
    mypy \
    sqlfluff

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs /app/tmp

# Set permissions
RUN chmod +x /app/entrypoint.sh

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command
CMD ["python", "app.py"]
