#!/bin/sh
set -e

case "$1" in
    run-migrations)
        echo "Running migrations..."
        alembic upgrade head
        exit 0
        ;;
    start-app)
        echo "Starting application..."
        exec uvicorn api.main:app --host 0.0.0.0 --port 80
        ;;
    *)
        exec "$@"
        ;;
esac