FROM python:3.9 AS base

WORKDIR /code

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade -r requirements.txt

# App stage
FROM base AS api

COPY src/api /code/api
COPY src/database /code/database
COPY scripts/entrypoint.sh /code/entrypoint.sh

RUN chmod +x /code/entrypoint.sh

# Local init stage
FROM base AS local-init

RUN apt-get update && apt-get install -y postgresql-client

COPY src/api /code/api
COPY alembic.ini /code/alembic.ini
COPY alembic /code/alembic
COPY data /code/data
COPY scripts/local_init.sh /code/local_init.sh
COPY scripts/load_database.py /code/load_database.py

RUN chmod +x /code/local_init.sh

# Test stage
FROM base AS test

COPY src /code
COPY src/database /code/database
COPY tests /code/tests

ENV PYTHONPATH=/app:$PYTHONPATH

CMD ["pytest"]
