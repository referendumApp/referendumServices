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

func (lsc *lastShardCache) check(actor atp.Aid) *Shard {
	lsc.lscLk.Lock()
	defer lsc.lscLk.Unlock()

	ls, ok := lsc.lastShardCache[actor]
	if ok {
		return ls
	}

	return nil
}

func (lsc *lastShardCache) remove(actor atp.Aid) {
	lsc.lscLk.Lock()
	defer lsc.lscLk.Unlock()

	delete(lsc.lastShardCache, actor)
}

func (lsc *lastShardCache) put(ls *Shard) {
	if ls == nil {
		return
	}
	lsc.lscLk.Lock()
	defer lsc.lscLk.Unlock()

	lsc.lastShardCache[ls.Aid] = ls
}

func (lsc *lastShardCache) get(ctx context.Context, actor atp.Aid) (*Shard, error) {
	ctx, span := otel.Tracer("carstore").Start(ctx, "getLastShard")
	defer span.End()

	maybeLs := lsc.check(actor)
	if maybeLs != nil {
		return maybeLs, nil
	}

	lastShard, err := lsc.source.GetLastShard(ctx, actor)
	if err != nil {
		return nil, err
	}

	lsc.put(lastShard)
	return lastShard, nil
}
