#!/bin/sh
set -e

echo "Starting local-init.sh"

DB_NAME="local-db"

echo "Waiting for PostgreSQL to be ready..."
until PGPASSWORD=$POSTGRES_PASSWORD psql -h "db" -U "user" -d "postgres" -c '\l' >/dev/null 2>&1; do
  echo "Postgres is unavailable - sleeping"
  sleep 1
done
echo "PostgreSQL is up - executing initialization"

if PGPASSWORD=$POSTGRES_PASSWORD psql -h "db" -U "user" -d "postgres" -lqt | cut -d \| -f 1 | grep -qw $DB_NAME; then
    echo "Database $DB_NAME already exists"
else
    echo "Database $DB_NAME does not exist. Creating..."
    PGPASSWORD=$POSTGRES_PASSWORD createdb -h "db" -U "user" $DB_NAME
    PGPASSWORD=$POSTGRES_PASSWORD psql -h "db" -U "user" -d "postgres" -c '\l'
fi

echo "Running migrations..."
if ! alembic upgrade head; then
  echo "Error running migrations"
  exit 1
fi

# TODO - add this back
#python /code/load_database.py

echo "Local initialization completed"
