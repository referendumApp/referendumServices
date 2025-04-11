package app

import (
	"log/slog"

	"github.com/referendumApp/referendumServices/internal/car"
	"github.com/referendumApp/referendumServices/internal/database"
	"github.com/referendumApp/referendumServices/internal/repo"
)

type View struct {
	db      *database.DB
	repoman *repo.Manager
	log     *slog.Logger
	cs      car.Store
}

func NewAppView(db *database.DB, repoman *repo.Manager, cs car.Store) *View {
	return &View{db: db, repoman: repoman, cs: cs, log: slog.Default().With("system", "appview")}
}
