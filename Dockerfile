FROM python:3.11 AS base

WORKDIR /code
COPY pyproject.toml .
RUN pip install --no-cache-dir .

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
FROM base AS local-init

RUN apt-get update && apt-get install -y postgresql-client

COPY api /code/api
COPY common /code/common
COPY alembic.ini /code/alembic.ini
COPY alembic /code/alembic
COPY data /code/data
COPY scripts/local_init.sh /code/local_init.sh
COPY scripts/load_database.py /code/load_database.py

RUN chmod +x /code/local_init.sh

# Test stage
FROM base AS test

RUN pip install --no-cache-dir .[test]

COPY api /code/api
COPY pipeline /code/pipeline
COPY common /code/common


ENV PYTHONPATH=/code:$PYTHONPATH

CMD ["pytest"]
