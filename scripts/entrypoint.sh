#!/bin/sh
set -e

exec uvicorn api.main:app --host 0.0.0.0 --port 80 --log-config None
