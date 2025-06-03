package app

import (
	"context"
	"log/slog"
	"time"

	"github.com/referendumApp/referendumServices/internal/database"
)

// View struct containing dependencies for the app view
type View struct {
	meta         *ViewMeta
	cache        *ActorCache
	log          *slog.Logger
	handleSuffix string
}

// NewAppView initializes a 'View' struct
func NewAppView(
	ctx context.Context,
	db *database.DB,
	dbSchema string,
	handleSuffix string,
	cacheHost string,
	logger *slog.Logger,
) (*View, error) {
	actorCache, err := NewActorCache(ctx, cacheHost, logger)
	if err != nil {
		return nil, err
	}
	avDb := db.WithSchema(dbSchema)
	vm := &ViewMeta{avDb}

	v := &View{
		meta:         vm,
		cache:        actorCache,
		handleSuffix: handleSuffix,
		log:          logger.WithGroup("app-view"),
	}

	go v.warmPublicServantCache(ctx, 24*time.Hour)

	return v, nil
}

func (v *View) warmPublicServantCache(ctx context.Context, interval time.Duration) {
	v.cache.PublicServantCache.Refresh(ctx, v.meta)

	ticker := time.NewTicker(interval)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			v.log.InfoContext(ctx, "Stopping the public servant cache refresh go routine", "err", ctx.Err())
			return
		case <-ticker.C:
			v.cache.PublicServantCache.Refresh(ctx, v.meta)
		}
	}
}
