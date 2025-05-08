package app

import (
	"log/slog"

	"github.com/referendumApp/referendumServices/internal/database"
)

// View struct containing dependencies for the app view
type View struct {
	meta         *ViewMeta
	log          *slog.Logger
	handleSuffix string
}

// NewAppView initializes a 'View' struct
func NewAppView(db *database.DB, dbSchema string, handleSuffix string, logger *slog.Logger) *View {
	avDb := db.WithSchema(dbSchema)
	vm := &ViewMeta{avDb}
	return &View{
		meta:         vm,
		handleSuffix: handleSuffix,
		log:          logger.WithGroup("appview"),
	}
}
