#!/bin/sh
set -e

exec python -m uvicorn api.main:app \
    --host 0.0.0.0 \
    --port 80 \
    --log-level info \
    --no-access-log