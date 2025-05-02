FROM golang:1.24-alpine as builder
WORKDIR /code

ARG GOMODCACHE
ENV GOMODCACHE=$GOMODCACHE

RUN --mount=type=cache,target=${GOMODCACHE} \
    --mount=type=bind,source=go.sum,target=go.sum \
    --mount=type=bind,source=go.mod,target=go.mod \
    go mod download

ARG BINARY_PATH
ARG GOCACHE

ENV BINARY_PATH=$BINARY_PATH
ENV CGO_ENABLED=0
ENV GOCACHE=$GOCACHE

RUN --mount=type=cache,target=${GOMODCACHE} \
    --mount=type=cache,target=${GOCACHE} \
    --mount=type=bind,source=go.sum,target=go.sum \
    --mount=type=bind,source=go.mod,target=go.mod \
    --mount=type=bind,source=./cmd/api/main.go,target=./cmd/api/main.go \
    --mount=type=bind,source=./internal,target=./internal \
    go build -o ${BINARY_PATH} ./cmd/api/main.go

FROM alpine:latest as user-prod
ARG BINARY_PATH
ENV BINARY_PATH=$BINARY_PATH

COPY --from=builder /code/${BINARY_PATH} ./app

ENTRYPOINT ["./app"]

FROM builder as user-local
COPY cmd/dev cmd/dev
RUN apk add --no-cache curl

ENTRYPOINT ["go", "run", "-tags=dev", "./cmd/dev/main.go"]
