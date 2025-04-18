package app

import (
	"log/slog"

	"github.com/referendumApp/referendumServices/internal/car"
	"github.com/referendumApp/referendumServices/internal/database"
	"github.com/referendumApp/referendumServices/internal/env"
	"github.com/referendumApp/referendumServices/internal/repo"
)

// View struct containing dependencies for the app view
type View struct {
	meta         *ViewMeta
	repoman      *repo.Manager
	log          *slog.Logger
	cs           car.Store
	handleSuffix string
}

// NewAppView initializes a 'View' struct
func NewAppView(db *database.DB, repoman *repo.Manager, cs car.Store, cfg *env.Config) *View {
	avDb := db.WithSchema(cfg.AtpDBSchema)
	vm := &ViewMeta{avDb}
	return &View{
		meta:         vm,
		repoman:      repoman,
		cs:           cs,
		handleSuffix: cfg.HandleSuffix,
		log:          slog.Default().With("system", "appview"),
	}
}
