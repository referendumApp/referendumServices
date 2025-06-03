package app

import (
	"context"
	"errors"
	"fmt"
	"log"
	"log/slog"
	"strconv"
	"time"

	"github.com/go-redis/cache/v8"
	"github.com/go-redis/redis/v8"
	"github.com/referendumApp/referendumServices/internal/domain/atp"
)

type Cache struct {
	cache *cache.Cache
	log   *slog.Logger
	ttl   time.Duration
}

type ActorCache struct {
	UserCache          *UserCache
	PublicServantCache *PublicServantCache
}

func NewActorCache(ctx context.Context, host string, logger *slog.Logger) (*ActorCache, error) {
	log.Println("Setting up actor cache")

	userRedis := redis.NewClient(&redis.Options{
		Addr: host,
		DB:   0,
	})

	psRedis := redis.NewClient(&redis.Options{
		Addr: host,
		DB:   1,
	})

	userCache := cache.New(&cache.Options{
		Redis:        userRedis,
		LocalCache:   cache.NewTinyLFU(1000, time.Minute),
		StatsEnabled: true,
	})

	psCache := cache.New(&cache.Options{
		Redis:        psRedis,
		LocalCache:   cache.NewTinyLFU(5000, 2*time.Hour),
		StatsEnabled: true,
	})

	if _, err := userRedis.Ping(ctx).Result(); err != nil {
		return nil, fmt.Errorf("error connecting to user cache: %w", err)
	}

	if _, err := psRedis.Ping(ctx).Result(); err != nil {
		return nil, fmt.Errorf("error connecting to public servant cache: %w", err)
	}

	userCacheInstance := &UserCache{
		Cache: &Cache{
			cache: userCache,
			log:   logger.WithGroup("user-cache"),
			ttl:   24 * time.Hour,
		},
	}

	psCacheInstance := &PublicServantCache{
		Cache: &Cache{
			cache: psCache,
			log:   logger.WithGroup("ps-cache"),
			ttl:   30 * 24 * time.Hour,
		},
	}

	log.Println("Successfully set up actor cache!")

	return &ActorCache{UserCache: userCacheInstance, PublicServantCache: psCacheInstance}, nil
}

func (c *Cache) key(aid atp.Aid) string {
	return strconv.FormatUint(uint64(aid), 10)
}

func (c *Cache) Exists(ctx context.Context, aid atp.Aid) bool {
	return c.cache.Exists(ctx, c.key(aid))
}

// UserCache extends 'Cache' struct user profile specific getter and setter methods
type UserCache struct {
	*Cache
}

func (c *UserCache) Set(ctx context.Context, aid atp.Aid, profile *actorProfile) {
	if err := c.cache.Set(&cache.Item{Ctx: ctx, Key: c.key(aid), Value: profile, TTL: c.ttl}); err != nil {
		c.log.ErrorContext(ctx, "Failed to cache user profile", "error", err, "aid", aid)
	}
}

// TODO: can use the 'prometheus' package to track cache miss/hit metrics
func (c *UserCache) Get(ctx context.Context, aid atp.Aid) *actorProfile {
	var profile actorProfile

	if err := c.cache.Get(ctx, c.key(aid), &profile); err != nil {
		c.log.WarnContext(ctx, "Cache miss for user profile", "error", err, "aid", aid)
		if errors.Is(err, cache.ErrCacheMiss) {
			return nil
		}
		return nil
	}

	return &profile
}

// PublicServantCache extends 'Cache' struct public servant DID specific getter and setter methods
type PublicServantCache struct {
	*Cache
}

func (c *PublicServantCache) Set(ctx context.Context, aid atp.Aid, did string) {
	if err := c.cache.Set(&cache.Item{Ctx: ctx, Key: c.key(aid), Value: did, TTL: c.ttl}); err != nil {
		c.log.ErrorContext(ctx, "Failed to cache public servant DID", "error", err, "aid", aid, "did", did)
	}
}

// TODO: can use the 'prometheus' package to track cache miss/hit metrics
func (c *PublicServantCache) Get(ctx context.Context, aid atp.Aid) string {
	var did string

	if err := c.cache.Get(ctx, c.key(aid), &did); err != nil {
		c.log.WarnContext(ctx, "Cache miss for public servant DID", "error", err, "aid", aid)
		if errors.Is(err, cache.ErrCacheMiss) {
			return ""
		}
		return ""
	}

	return did
}

func (c *PublicServantCache) Refresh(ctx context.Context, meta *ViewMeta) {
	psIDs, err := meta.GetAllPublicServantIDs(ctx)
	if err != nil {
		c.log.ErrorContext(ctx, "Error getting public servant IDs", "error", err)
	}
	for _, psID := range psIDs {
		c.Set(ctx, psID.Aid, psID.Did)
	}
}
