FROM python:3.9 AS base

WORKDIR /code

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# App stage
FROM base AS app

COPY ./api /code/api

CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "80"]

# Test stage
FROM base AS test

COPY . .

ENV PATH="/usr/local/bin:${PATH}"

CMD ["pytest"]
