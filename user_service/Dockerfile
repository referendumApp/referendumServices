FROM golang:1.24-alpine AS base
WORKDIR /code

ARG GOCACHE
ARG GOMODCACHE

ENV CGO_ENABLED=0
ENV GOCACHE=$GOCACHE
ENV GOMODCACHE=$GOMODCACHE

RUN --mount=type=cache,target=${GOMODCACHE} \
  --mount=type=bind,source=go.sum,target=go.sum \
  --mount=type=bind,source=go.mod,target=go.mod \
  go mod download

FROM base AS builder
ARG BINARY_PATH
ENV BINARY_PATH=$BINARY_PATH

RUN --mount=type=cache,target=${GOMODCACHE} \
  --mount=type=cache,target=${GOCACHE} \
  --mount=type=bind,source=go.sum,target=go.sum \
  --mount=type=bind,source=go.mod,target=go.mod \
  --mount=type=bind,source=./cmd/api/main.go,target=./cmd/api/main.go \
  --mount=type=bind,source=./internal,target=./internal \
  --mount=type=bind,source=./pkg/common,target=./pkg/common \
  go build -o ${BINARY_PATH} ./cmd/api/main.go

FROM alpine:latest AS user-prod
ARG BINARY_PATH
ENV BINARY_PATH=$BINARY_PATH

COPY --from=builder /code/${BINARY_PATH} ./app

ENTRYPOINT ["./app"]

FROM builder AS user-local
COPY cmd/dev cmd/dev
RUN apk add --no-cache curl

ENTRYPOINT ["go", "run", "-tags=dev", "./cmd/dev/main.go"]

FROM base AS test-builder
RUN --mount=type=bind,source=${GOMODCACHE},target=/go/pkg/mod \
  --mount=type=bind,source=${GOCACHE},target=/root/.cache/go-build \
  --mount=type=bind,source=go.sum,target=go.sum \
  --mount=type=bind,source=go.mod,target=go.mod \
  --mount=type=bind,source=./cmd/api,target=./cmd/api \
  --mount=type=bind,source=./internal,target=./internal \
  --mount=type=bind,source=./pkg/common,target=./pkg/common \
  --mount=type=bind,source=./testutil,target=./testutil \
  go test -c -tags=init,integration ./... -o test/

FROM alpine:latest AS test
COPY --from=test-builder /code/test/ ./test/
COPY go.mod go.mod
COPY go.sum go.sum
COPY kms_seed.yaml kms_seed.yaml

CMD ["sh", "-c", "./test/api.test -test.v && ./test/service.test -test.v"]
