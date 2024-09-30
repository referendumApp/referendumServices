FROM python:3.9 AS base

WORKDIR /code

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade -r requirements.txt

# App stage
FROM base AS app

COPY ./api /code/api
COPY entrypoint.sh /code/entrypoint.sh

RUN chmod +x /code/entrypoint.sh

# Local init stage
FROM base AS local-init

RUN apt-get update && apt-get install -y postgresql-client

COPY ./api /code/api
COPY alembic.ini /code/alembic.ini
COPY alembic /code/alembic
COPY local_init.sh /code/local_init.sh

RUN chmod +x /code/local_init.sh

# Test stage
FROM base AS test

COPY . .

ENV PATH="/usr/local/bin:${PATH}"

CMD ["pytest"]