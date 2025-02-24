# Multi-stage build for Python Data Service
FROM python:3.11.4-slim-bullseye AS data-base

RUN pip install uv
WORKDIR /code
COPY pyproject.toml .
RUN uv pip install --system .

# Alembic migration stage
FROM data-base AS migrations

COPY alembic.ini /code/
COPY alembic /code/alembic

# API stage
FROM data-base AS api

COPY data_service/api /code/api
COPY data_service/common /code/common
COPY data_service/scripts/entrypoint.sh /code/entrypoint.sh
RUN chmod +x /code/entrypoint.sh

CMD ["/code/entrypoint.sh"]

# Pipeline stage
FROM data-base AS pipeline

COPY data_service/pipeline /code/pipeline
COPY data_service/common /code/common

CMD ["python", "-m", "pipeline.run"]

# Local init stage
FROM data-base AS local-db-init

RUN apt-get update && \
    apt-get install -y postgresql-client && \
    rm -rf /var/lib/apt/lists/*

COPY data_service/api /code/api
COPY data_service/common /code/common
COPY data_service/alembic.ini /code/alembic.ini
COPY data_service/alembic /code/alembic
COPY data_service/data /code/data
COPY data_service/scripts/local_db_init.sh /code/local_db_init.sh
COPY data_service/scripts/load_datadata-base.py /code/load_datadata-base.py

RUN chmod +x /code/local_db_init.sh

# API Local stage
FROM data-base AS api-local

RUN uv pip install --system ".[test]"

COPY data_service/api /code/api
COPY data_service/common /code/common
COPY data_service/scripts/entrypoint.sh /code/entrypoint.sh
RUN chmod +x /code/entrypoint.sh

CMD ["/code/entrypoint.sh"]

# Test stage
FROM data-base AS test

RUN uv pip install --system ".[test]"

COPY data_service/api /code/api
COPY data_service/pipeline /code/pipeline
COPY data_service/common /code/common

ENV PYTHONPATH=/code:$PYTHONPATH

CMD ["pytest"]

# Multi-stage build for ATP Go Service
FROM golang:1.24-alpine as atp-base
WORKDIR /code
COPY go.mod go.sum ./

RUN go mod download

FROM atp-base as prod-builder
COPY cmd/api cmd/api
COPY internal internal

RUN CGO_ENABLED=0 GOOS=linux go build -o app ./cmd/api/main.go

FROM alpine:latest as atp-prod
COPY --from=atp-base /code/app .

ENTRYPOINT ["./app"]

FROM atp-base as atp-local

COPY . .

ENTRYPOINT ["go", "run", "-tags=dev", "./cmd/dev/main.go"]
