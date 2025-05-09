package car

import (
	"context"
	"sync"

	"github.com/referendumApp/referendumServices/internal/domain/atp"
	"go.opentelemetry.io/otel"
)

// LastShardSource interface for CAR shard metadata
type LastShardSource interface {
	GetLastShard(context.Context, atp.Aid) (*Shard, error)
}

type lastShardCache struct {
	source LastShardSource

	lscLk          sync.Mutex
	lastShardCache map[atp.Aid]*Shard
}

func (lsc *lastShardCache) init() {
	lsc.lastShardCache = make(map[atp.Aid]*Shard)
}

func (lsc *lastShardCache) check(user atp.Aid) *Shard {
	lsc.lscLk.Lock()
	defer lsc.lscLk.Unlock()

	ls, ok := lsc.lastShardCache[user]
	if ok {
		return ls
	}

	return nil
}

func (lsc *lastShardCache) remove(user atp.Aid) {
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

func (lsc *lastShardCache) get(ctx context.Context, user atp.Aid) (*Shard, error) {
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
