#!/bin/bash

# AI Code Reviewer Bot - Entrypoint Script

set -e

echo "Starting AI Code Reviewer Bot..."

# Wait for database to be ready
echo "Waiting for database to be ready..."
while ! pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER; do
  echo "Database is unavailable - sleeping"
  sleep 2
done

echo "Database is ready!"

# Wait for Redis to be ready
echo "Waiting for Redis to be ready..."
while ! redis-cli -h $REDIS_HOST -p $REDIS_PORT ping; do
  echo "Redis is unavailable - sleeping"
  sleep 2
done

echo "Redis is ready!"

# Run database migrations
echo "Running database migrations..."
python -c "from db.session import create_tables; create_tables()"

# Start the application
echo "Starting FastAPI application..."
exec "$@"
