//revive:disable:exported
package indexer

import (
	"bytes"
	"context"
	"errors"
	"fmt"
	"io"
	"io/fs"
	"log/slog"
	"sync"

	"github.com/bluesky-social/indigo/api/atproto"
	"github.com/bluesky-social/indigo/xrpc"
	ipld "github.com/ipfs/go-ipld-format"
	"github.com/jackc/pgx/v5"
	"github.com/referendumApp/referendumServices/internal/database"
	"github.com/referendumApp/referendumServices/internal/domain/atp"
	"github.com/referendumApp/referendumServices/internal/repo"
	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/attribute"
	"golang.org/x/time/rate"
)

func NewRepoFetcher(db *database.DB, rm *repo.Manager, maxConcurrency int) *RepoFetcher {
	return &RepoFetcher{
		repoman:                rm,
		db:                     db,
		Limiters:               make(map[uint]*rate.Limiter),
		ApplyPDSClientSettings: func(*xrpc.Client) {},
		MaxConcurrency:         maxConcurrency,
		log:                    slog.Default().With("system", "indexer"),
	}
}

type RepoFetcher struct {
	ApplyPDSClientSettings func(*xrpc.Client)

	repoman *repo.Manager
	db      *database.DB
	log     *slog.Logger

	Limiters map[uint]*rate.Limiter
	LimitMux sync.RWMutex

	MaxConcurrency int
}

func (rf *RepoFetcher) GetLimiter(pdsID uint) *rate.Limiter {
	rf.LimitMux.RLock()
	defer rf.LimitMux.RUnlock()

	return rf.Limiters[pdsID]
}

func (rf *RepoFetcher) GetOrCreateLimiter(pdsID uint, pdsrate float64) *rate.Limiter {
	rf.LimitMux.Lock()
	defer rf.LimitMux.Unlock()

	lim, ok := rf.Limiters[pdsID]
	if !ok {
		lim = rate.NewLimiter(rate.Limit(pdsrate), 1)
		rf.Limiters[pdsID] = lim
	}

	return lim
}

func (rf *RepoFetcher) SetLimiter(pdsID uint, lim *rate.Limiter) {
	rf.LimitMux.Lock()
	defer rf.LimitMux.Unlock()

	rf.Limiters[pdsID] = lim
}

func (rf *RepoFetcher) fetchRepo(
	ctx context.Context,
	c *xrpc.Client,
	pds *atp.PDS,
	did string,
	rev string,
) ([]byte, error) {
	ctx, span := otel.Tracer("indexer").Start(ctx, "fetchRepo")
	defer span.End()

	span.SetAttributes(
		attribute.String("pds", pds.Host),
		attribute.String("did", did),
		attribute.String("rev", rev),
	)

	limiter := rf.GetOrCreateLimiter(pds.ID, pds.CrawlRateLimit)

	// Wait to prevent DOSing the PDS when connecting to a new stream with lots of active repos
	if err := limiter.Wait(ctx); err != nil {
		rf.log.ErrorContext(ctx, "Rate limiter failed to wait", "error", err)
		return nil, err
	}

	rf.log.DebugContext(ctx, "SyncGetRepo", "did", did, "since", rev)
	// TODO: max size on these? A malicious PDS could just send us a petabyte sized repo here and kill us
	repo, err := atproto.SyncGetRepo(ctx, c, did, rev)
	if err != nil {
		reposFetched.WithLabelValues("fail").Inc()
		return nil, fmt.Errorf("failed to fetch repo (did=%s,rev=%s,host=%s): %w", did, rev, pds.Host, err)
	}
	reposFetched.WithLabelValues("success").Inc()

	return repo, nil
}

// TODO: since this function is the only place we depend on the repomanager, i wonder if this should be wired some other way?
func (rf *RepoFetcher) FetchAndIndexRepo(ctx context.Context, job *crawlWork) error {
	ctx, span := otel.Tracer("indexer").Start(ctx, "FetchAndIndexRepo")
	defer span.End()

	span.SetAttributes(attribute.Int("catchup", len(job.catchup)))

	ai := job.act

	pds, err := rf.db.LookupPDSById(ctx, ai.PDS.Int64)
	if err != nil {
		catchupEventsFailed.WithLabelValues("nopds").Inc()
		return fmt.Errorf(
			"expected to find pds record (%d) in db for crawling one of their persons: %w",
			ai.PDS.Int64,
			err,
		)
	}

	rev, err := rf.repoman.GetRepoRev(ctx, ai.Aid)
	if err != nil && !errors.Is(err, pgx.ErrNoRows) {
		catchupEventsFailed.WithLabelValues("noroot").Inc()
		return fmt.Errorf("failed to get repo root: %w", err)
	}

	// attempt to process buffered events
	if !job.initScrape && len(job.catchup) > 0 {
		first := job.catchup[0]
		var resync bool
		if first.evt.Since == nil || rev == *first.evt.Since {
			for i, j := range job.catchup {
				catchupEventsProcessed.Inc()
				if eventErr := rf.repoman.HandleExternalActorEvent(ctx, pds.ID, ai.Aid, ai.Did, j.evt.Since, j.evt.Rev, j.evt.Blocks, j.evt.Ops); eventErr != nil {
					rf.log.ErrorContext(
						ctx,
						"buffered event catchup failed",
						"error",
						eventErr,
						"did",
						ai.Did,
						"i",
						i,
						"jobCount",
						len(job.catchup),
						"seq",
						j.evt.Seq,
					)
					resync = true // fall back to a repo sync
					break
				}
			}

			if !resync {
				return nil
			}
		}
	}

	revp := &rev
	if rev == "" {
		span.SetAttributes(attribute.Bool("full", true))
		revp = nil
	}

	c := atp.ClientForPds(pds)
	rf.ApplyPDSClientSettings(c)

	repo, err := rf.fetchRepo(ctx, c, pds, ai.Did, rev)
	if err != nil {
		return err
	}

	if impErr := rf.repoman.ImportNewRepo(ctx, ai.Aid, ai.Did, bytes.NewReader(repo), revp); impErr != nil {
		span.RecordError(impErr)

		if ipld.IsNotFound(impErr) || errors.Is(impErr, io.EOF) || errors.Is(impErr, fs.ErrNotExist) {
			rf.log.ErrorContext(ctx, "partial repo fetch was missing data", "did", ai.Did, "pds", pds.Host, "rev", rev)
			repo, fetchErr := rf.fetchRepo(ctx, c, pds, ai.Did, "")
			if fetchErr != nil {
				return fetchErr
			}

			if newImpErr := rf.repoman.ImportNewRepo(ctx, ai.Aid, ai.Did, bytes.NewReader(repo), nil); newImpErr != nil {
				span.RecordError(newImpErr)
				return fmt.Errorf("failed to import backup repo (%s): %w", ai.Did, newImpErr)
			}

			return nil
		}
		return fmt.Errorf("importing fetched repo (curRev: %s): %w", rev, impErr)
	}

	return nil
}
