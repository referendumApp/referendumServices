#!/bin/sh
set -e

exec uvicorn api.app:app --host 0.0.0.0 --port 80
