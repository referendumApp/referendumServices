package util

import (
	"context"
	"io"
	"log/slog"
)

func SetupLogger(ctx context.Context, stdout io.Writer) *slog.Logger {
	var levelVar slog.LevelVar
	levelVar.Set(slog.LevelInfo)

	handler := slog.NewJSONHandler(stdout, &slog.HandlerOptions{Level: &levelVar})

	return slog.New(handler)
}
