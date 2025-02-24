package main

import (
	"context"
	"fmt"
  "io"
	"os"
	"os/signal"

	"github.com/referendumApp/referendumATP/internal/server"
)

func run(ctx context.Context, getenv func(string) string, stderr io.Writer) error {
	ctx, cancel := signal.NotifyContext(ctx, os.Interrupt)
	defer cancel()

  handler := server.NewServer(getenv)
  server.StartServer(ctx, handler, stderr)

  return nil
}

func main() {
	ctx := context.Background()
	if err := run(ctx, os.Getenv, os.Stderr); err != nil {
		fmt.Fprintf(os.Stderr, "%s\n", err)
	}
}
