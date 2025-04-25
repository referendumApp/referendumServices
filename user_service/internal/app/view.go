package app

import (
	"log/slog"

	"github.com/referendumApp/referendumServices/internal/database"
	"github.com/referendumApp/referendumServices/internal/env-config"
)

// View struct containing dependencies for the app view
type View struct {
	meta         *ViewMeta
	log          *slog.Logger
	handleSuffix string
}

// NewAppView initializes a 'View' struct
func NewAppView(db *database.DB, cfg *env.Config, logger *slog.Logger) *View {
	avDb := db.WithSchema(cfg.AtpDBSchema)
	vm := &ViewMeta{avDb}
	return &View{
		meta:         vm,
		handleSuffix: cfg.HandleSuffix,
		log:          logger.WithGroup("appview"),
	}
}
