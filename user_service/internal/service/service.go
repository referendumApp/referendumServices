package service

import (
	"context"
	"io"

	"github.com/referendumApp/referendumServices/internal/config"
	"github.com/referendumApp/referendumServices/internal/database"
	"github.com/referendumApp/referendumServices/internal/server"
)

type Service struct {
	Server *server.Server
}

// Load env vars, start resources, and manage resource lifecycle
func New(ctx context.Context, stderr io.Writer) (*Service, error) {
	cfg := config.LoadConfigFromEnv()

	db, err := database.Connect(cfg)
	if err != nil {
		return nil, err
	}

	srv := server.New(cfg, db)

	if err := srv.Start(ctx, stderr); err != nil {
		return nil, err
	}

	return &Service{
		Server: srv,
	}, nil
}

func (s *Service) Shutdown(ctx context.Context) error {
	return s.Server.Shutdown(ctx)
}
