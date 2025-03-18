#!/bin/sh
set -e

echo "Starting local_db_init.sh"

echo "Waiting for PostgreSQL to be ready..."
until PGPASSWORD=$POSTGRES_PASSWORD psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "postgres" -c '\l' >/dev/null 2>&1; do
  echo "Postgres is unavailable - sleeping"
  sleep 1
done
echo "PostgreSQL is up - executing initialization"

create_database_if_not_exists() {
    local DB_NAME=$1
    if PGPASSWORD=$POSTGRES_PASSWORD psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -lqt | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
        echo "Database $DB_NAME already exists"
    else
        echo "Database $DB_NAME does not exist. Creating..."
        PGPASSWORD=$POSTGRES_PASSWORD createdb -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" "$DB_NAME"
        echo "Database $DB_NAME created"
    fi
}
create_database_if_not_exists "$LEGISCAN_API_DB_NAME"
create_database_if_not_exists "$REFERENDUM_DB_NAME"
create_database_if_not_exists "$PLC_DB_NAME"
create_database_if_not_exists "$CARSTORE_DB_NAME"

CREATE_LEGISCAN_USER="
DO \$\$
BEGIN
   -- Check if the user already exists
   IF NOT EXISTS (
       SELECT FROM pg_catalog.pg_roles
       WHERE rolname = '${LEGISCAN_API_DB_NAME}'
   ) THEN
       -- Create the user
       CREATE USER ${LEGISCAN_API_DB_NAME} WITH PASSWORD '${POSTGRES_PASSWORD}';
       -- Grant necessary permissions (modify as per requirements)
       GRANT CREATE ON SCHEMA public TO ${LEGISCAN_API_DB_NAME};
   END IF;
END \$\$;
"

PGPASSWORD=$POSTGRES_PASSWORD psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$LEGISCAN_API_DB_NAME" -c "$CREATE_LEGISCAN_USER"

PGPASSWORD=$POSTGRES_PASSWORD psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$LEGISCAN_API_DB_NAME" -f "/code/data/legiscan_api.sql"

echo "Local initialization completed"
