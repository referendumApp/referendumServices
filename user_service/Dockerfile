FROM golang:1.24-alpine as base
WORKDIR /code
COPY go.mod go.sum ./

RUN go mod download

FROM base as prod-builder
COPY cmd/api cmd/api
COPY internal internal

RUN CGO_ENABLED=0 GOOS=linux go build -o /code/app ./cmd/api/main.go

FROM alpine:latest as user-prod
COPY --from=prod-builder /code/app .

ENTRYPOINT ["./app"]

FROM base as user-local

COPY . .

ENTRYPOINT ["go", "run", "-tags=dev", "./cmd/dev/main.go"]
