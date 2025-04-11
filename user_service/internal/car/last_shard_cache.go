package car

import (
	"context"
	"fmt"
	"sync"

	"go.opentelemetry.io/otel"

	"github.com/referendumApp/referendumServices/internal/domain/atp"
)

type LastShardSource interface {
	GetLastShard(context.Context, atp.Uid) (*Shard, error)
}

type lastShardCache struct {
	source LastShardSource

	lscLk          sync.Mutex
	lastShardCache map[atp.Uid]*Shard
}

func (lsc *lastShardCache) Init() {
	lsc.lastShardCache = make(map[atp.Uid]*Shard)
}

func (lsc *lastShardCache) check(user atp.Uid) *Shard {
	lsc.lscLk.Lock()
	defer lsc.lscLk.Unlock()

	ls, ok := lsc.lastShardCache[user]
	if ok {
		return ls
	}

	return nil
}

func (lsc *lastShardCache) remove(user atp.Uid) {
	lsc.lscLk.Lock()
	defer lsc.lscLk.Unlock()

	delete(lsc.lastShardCache, user)
}

func (lsc *lastShardCache) put(ls *Shard) {
	if ls == nil {
		return
	}
	lsc.lscLk.Lock()
	defer lsc.lscLk.Unlock()

	lsc.lastShardCache[ls.Uid] = ls
}

func (lsc *lastShardCache) get(ctx context.Context, user atp.Uid) (*Shard, error) {
	ctx, span := otel.Tracer("carstore").Start(ctx, "getLastShard")
	defer span.End()

	maybeLs := lsc.check(user)
	if maybeLs != nil {
		fmt.Printf("Cache hit for user %v: Rev=%q, ID=%d, Path=%s\n",
			user, maybeLs.Rev, maybeLs.ID, maybeLs.Path)
		return maybeLs, nil
	}

	fmt.Printf("Cache miss for user %v, fetching from source\n", user)
	lastShard, err := lsc.source.GetLastShard(ctx, user)
	if err != nil {
		fmt.Printf("Error fetching shard for user %v: %v\n", user, err)
		return nil, err
	}

	fmt.Printf("Fetched shard for user %v: Rev=%q, ID=%d, Path=%s\n",
		user, lastShard.Rev, lastShard.ID, lastShard.Path)

	lsc.put(lastShard)
	return lastShard, nil
}
