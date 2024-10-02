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
create_database_if_not_exists $LEGISCAN_API_DB_NAME
create_database_if_not_exists $REFERENDUM_DB_NAME

echo "No migrations for LEGISCAN_API_DB_NAME"

echo "Running migrations for REFERENDUM_DB_NAME..."
if ! alembic -c alembic.ini upgrade head; then
  echo "Error running migrations for REFERENDUM_DB_NAME"
  exit 1
fi

# TODO - create data loaders
# echo "Loading data into LEGISCAN_API_DB_NAME..."
# python /code/load_LEGISCAN_API_DB_NAME.py

# echo "Loading data into REFERENDUM_DB_NAME..."
# python /code/load_REFERENDUM_DB_NAME.py

echo "Local initialization completed"
