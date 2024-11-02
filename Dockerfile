FROM python:3.11.4-slim-bullseye AS base

WORKDIR /code
COPY pyproject.toml .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir .

# Alembic migration stage
FROM base AS migrations

COPY alembic.ini /code/
COPY alembic /code/alembic

# API stage
FROM base AS api

COPY api /code/api
COPY common /code/common
COPY scripts/entrypoint.sh /code/entrypoint.sh
RUN chmod +x /code/entrypoint.sh

CMD ["/code/entrypoint.sh"]

# Pipeline stage
FROM base AS pipeline

COPY pipeline /code/pipeline
COPY common /code/common

CMD ["python", "-m", "pipeline.run"]

# Local init stage
FROM base AS local-db-init

RUN apt-get update && apt-get install -y postgresql-client curl unzip

# Install AWS CLI
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" \
    && unzip awscliv2.zip \
    && ./aws/install \
    && rm -rf aws awscliv2.zip

COPY api /code/api
COPY common /code/common
COPY alembic.ini /code/alembic.ini
COPY alembic /code/alembic
COPY data /code/data
COPY scripts/local_db_init.sh /code/local_db_init.sh
COPY scripts/load_database.py /code/load_database.py

RUN chmod +x /code/local_db_init.sh

# API Local stage
FROM base AS api-local

RUN pip install --no-cache-dir .[test]

COPY api /code/api
COPY common /code/common
COPY scripts/entrypoint.sh /code/entrypoint.sh
RUN chmod +x /code/entrypoint.sh

CMD ["/code/entrypoint.sh"]

# Test stage
FROM base AS test

RUN pip install --no-cache-dir .[test]

COPY api /code/api
COPY pipeline /code/pipeline
COPY common /code/common

ENV PYTHONPATH=/code:$PYTHONPATH

CMD ["pytest"]
