package car

import (
	"context"
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
		return maybeLs, nil
	}

	lastShard, err := lsc.source.GetLastShard(ctx, user)
	if err != nil {
		return nil, err
	}

	lsc.put(lastShard)
	return lastShard, nil
}
