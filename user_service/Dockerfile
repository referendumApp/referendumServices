FROM golang:1.24-alpine as base
WORKDIR /code
COPY go.mod go.sum ./

RUN apk add --no-cache \
    gcc \
    musl-dev \
    make \
    pkgconfig \
    sqlite-dev

RUN go mod download

FROM base as prod-builder
COPY cmd/api cmd/api
COPY internal internal

ENV CGO_ENABLED=1
ENV GOOS=linux
ENV GOARCH=amd64

RUN go build -o /code/app ./cmd/api/main.go

FROM alpine:latest as user-prod
COPY --from=prod-builder /code/app .

ENTRYPOINT ["./app"]

FROM base as user-local
COPY . .

ENTRYPOINT ["go", "run", "-tags=dev", "./cmd/dev/main.go"]
