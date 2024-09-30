#!/bin/sh
set -e

echo "Starting local-init.sh"

DB_NAME=$(echo $DATABASE_URL | awk -F'/' '{print $NF}')
echo "Database name: $DB_NAME"

echo "Waiting for PostgreSQL to be ready..."
echo $(psql -h "db" -U "user" -c '\l')
until PGPASSWORD=$POSTGRES_PASSWORD psql -h "db" -U "user" -d "postgres" -c '\l' >/dev/null 2>&1; do
  echo "Postgres is unavailable - sleeping"
  sleep 1
done
echo "PostgreSQL is up - executing initialization"

PGPASSWORD=$POSTGRES_PASSWORD psql -h "db" -U "user" -d "postgres" -c '\l'
if PGPASSWORD=$POSTGRES_PASSWORD psql -h "db" -U "user" -d "postgres" -lqt | cut -d \| -f 1 | grep -qw $DB_NAME; then
    echo "Database $DB_NAME already exists"
else
    echo "Database $DB_NAME does not exist. Creating..."
    PGPASSWORD=$POSTGRES_PASSWORD createdb -h "db" -U "user" $DB_NAME
    PGPASSWORD=$POSTGRES_PASSWORD psql -h "db" -U "user" -d "postgres" -c '\l'
fi

echo "Running migrations..."
alembic upgrade head

python /code/load_database.py

echo "Local initialization completed"
