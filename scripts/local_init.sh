#!/bin/sh
set -e

echo "Starting local-init.sh"

echo "Waiting for PostgreSQL to be ready..."
until PGPASSWORD=$POSTGRES_PASSWORD psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "postgres" -c '\l' >/dev/null 2>&1; do
  echo "Postgres is unavailable - sleeping"
  sleep 1
done
echo "PostgreSQL is up - executing initialization"

create_database_if_not_exists() {
    local DB_NAME=$1
    if PGPASSWORD=$POSTGRES_PASSWORD psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -lqt | cut -d \| -f 1 | grep -qw $DB_NAME; then
        echo "Database $DB_NAME already exists"
    else
        echo "Database $DB_NAME does not exist. Creating..."
        PGPASSWORD=$POSTGRES_PASSWORD createdb -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" $DB_NAME
        echo "Database $DB_NAME created"
    fi
}
create_database_if_not_exists $LEGISCAN_DATABASE
create_database_if_not_exists $REFERENDUM_DATABASE

echo "No migrations for LEGISCAN_DATABASE"

echo "Running migrations for REFERENDUM_DATABASE..."
if ! alembic -c alembic.ini upgrade head; then
  echo "Error running migrations for REFERENDUM_DATABASE"
  exit 1
fi

# TODO - create data loaders
# echo "Loading data into LEGISCAN_DATABASE..."
# python /code/load_legiscan_database.py

# echo "Loading data into REFERENDUM_DATABASE..."
# python /code/load_referendum_database.py

echo "Local initialization completed"
