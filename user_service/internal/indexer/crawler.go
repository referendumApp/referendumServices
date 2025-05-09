//revive:disable:exported
package indexer

import (
	"context"
	"fmt"
	"log/slog"
	"sync"
	"time"

	comatproto "github.com/bluesky-social/indigo/api/atproto"
	"github.com/referendumApp/referendumServices/internal/domain/atp"
	"go.opentelemetry.io/otel"
)

type CrawlDispatcher struct {
	// from Crawl()
	ingest chan *atp.Person
	// from AddToCatchupQueue()
	catchup chan *crawlWork
	// from main loop to fetchWorker()
	repoSync chan *crawlWork

	done       chan struct{}
	complete   chan atp.Aid
	todo       map[atp.Aid]*crawlWork
	inProgress map[atp.Aid]*crawlWork

	log         *slog.Logger
	repoFetcher CrawlRepoFetcher
	maplk       sync.Mutex

	concurrency int
}

// this is what we need of RepoFetcher
type CrawlRepoFetcher interface {
	FetchAndIndexRepo(ctx context.Context, job *crawlWork) error
}

func NewCrawlDispatcher(repoFetcher CrawlRepoFetcher, concurrency int, log *slog.Logger) (*CrawlDispatcher, error) {
	if concurrency < 1 {
		return nil, fmt.Errorf("must specify a non-zero positive integer for crawl dispatcher concurrency")
	}

	out := &CrawlDispatcher{
		ingest:      make(chan *atp.Person),
		repoSync:    make(chan *crawlWork),
		complete:    make(chan atp.Aid),
		catchup:     make(chan *crawlWork),
		repoFetcher: repoFetcher,
		concurrency: concurrency,
		todo:        make(map[atp.Aid]*crawlWork),
		inProgress:  make(map[atp.Aid]*crawlWork),
		log:         log,
		done:        make(chan struct{}),
	}
	go out.CatchupRepoGaugePoller()

	return out, nil
}

func (c *CrawlDispatcher) Run() {
	go c.mainLoop()

	for range c.concurrency {
		go c.fetchWorker()
	}
}

func (c *CrawlDispatcher) Shutdown() {
	close(c.done)
}

type catchupJob struct {
	evt  *comatproto.SyncSubscribeRepos_Commit
	host *atp.PDS
	user *atp.Person
}

type crawlWork struct {
	act *atp.Person

	// for events that come in while this actor's crawl is enqueued
	// catchup items are processed during the crawl
	catchup []*catchupJob

	// for events that come in while this actor is being processed
	// next items are processed after the crawl
	next []*catchupJob

	initScrape bool
}

func (c *CrawlDispatcher) mainLoop() {
	var nextDispatchedJob *crawlWork
	var jobsAwaitingDispatch []*crawlWork

	// dispatchQueue represents the repoSync worker channel to which we dispatch crawl work
	var dispatchQueue chan *crawlWork

	for {
		select {
		case actorToCrawl := <-c.ingest:
			// TODO: max buffer size
			crawlJob := c.enqueueJobForActor(actorToCrawl)
			if crawlJob == nil {
				break
			}

			if nextDispatchedJob == nil {
				nextDispatchedJob = crawlJob
				dispatchQueue = c.repoSync
			} else {
				jobsAwaitingDispatch = append(jobsAwaitingDispatch, crawlJob)
			}
		case dispatchQueue <- nextDispatchedJob:
			c.dequeueJob(nextDispatchedJob)

			if len(jobsAwaitingDispatch) > 0 {
				nextDispatchedJob = jobsAwaitingDispatch[0]
				jobsAwaitingDispatch = jobsAwaitingDispatch[1:]
			} else {
				nextDispatchedJob = nil
				dispatchQueue = nil
			}
		case catchupJob := <-c.catchup:
			// CatchupJobs are for processing events that come in while a crawl is in progress
			// They are lower priority than new crawls so we only add them to the queue if there isn't already a job in progress
			if nextDispatchedJob == nil {
				nextDispatchedJob = catchupJob
				dispatchQueue = c.repoSync
			} else {
				jobsAwaitingDispatch = append(jobsAwaitingDispatch, catchupJob)
			}
		case uid := <-c.complete:
			c.maplk.Lock()

			job, ok := c.inProgress[uid]
			if !ok {
				panic("should not be possible to not have a job in progress we receive a completion signal for")
			}
			delete(c.inProgress, uid)

			// If there are any subsequent jobs for this UID, add it back to the todo list or buffer.
			// We're basically pumping the `next` queue into the `catchup` queue and will do this over and over until the `next` queue is empty.
			if len(job.next) > 0 {
				c.todo[uid] = job
				job.initScrape = false
				job.catchup = job.next
				job.next = nil
				if nextDispatchedJob == nil {
					nextDispatchedJob = job
					dispatchQueue = c.repoSync
				} else {
					jobsAwaitingDispatch = append(jobsAwaitingDispatch, job)
				}
			}
			c.maplk.Unlock()
		}
	}
}

// enqueueJobForActor adds a new crawl job to the todo list if there isn't already a job in progress for this actor
func (c *CrawlDispatcher) enqueueJobForActor(ai *atp.Person) *crawlWork {
	c.maplk.Lock()
	defer c.maplk.Unlock()
	_, ok := c.inProgress[ai.Uid]
	if ok {
		return nil
	}

	_, has := c.todo[ai.Uid]
	if has {
		return nil
	}

	crawlJob := &crawlWork{
		act:        ai,
		initScrape: true,
	}
	c.todo[ai.Uid] = crawlJob
	return crawlJob
}

// dequeueJob removes a job from the todo list and adds it to the inProgress list
func (c *CrawlDispatcher) dequeueJob(job *crawlWork) {
	c.maplk.Lock()
	defer c.maplk.Unlock()
	delete(c.todo, job.act.Uid)
	c.inProgress[job.act.Uid] = job
}

func (c *CrawlDispatcher) addToCatchupQueue(catchup *catchupJob) *crawlWork {
	c.maplk.Lock()
	defer c.maplk.Unlock()

	// If the actor crawl is enqueued, we can append to the catchup queue which gets emptied during the crawl
	job, ok := c.todo[catchup.user.Uid]
	if ok {
		catchupEventsEnqueued.WithLabelValues("todo").Inc()
		job.catchup = append(job.catchup, catchup)
		return nil
	}

	// If the actor crawl is in progress, we can append to the nextr queue which gets emptied after the crawl
	job, ok = c.inProgress[catchup.user.Uid]
	if ok {
		catchupEventsEnqueued.WithLabelValues("prog").Inc()
		job.next = append(job.next, catchup)
		return nil
	}

	catchupEventsEnqueued.WithLabelValues("new").Inc()
	// Otherwise, we need to create a new crawl job for this actor and enqueue it
	cw := &crawlWork{
		act:     catchup.user,
		catchup: []*catchupJob{catchup},
	}
	c.todo[catchup.user.Uid] = cw
	return cw
}

func (c *CrawlDispatcher) fetchWorker() {
	for job := range c.repoSync {
		if err := c.repoFetcher.FetchAndIndexRepo(context.TODO(), job); err != nil {
			c.log.Error("failed to perform repo crawl", "did", job.act.Did, "err", err)
		}
		// TODO: do we still just do this if it errors?
		c.complete <- job.act.Uid
	}
}

func (c *CrawlDispatcher) Crawl(ctx context.Context, ai *atp.Person) error {
	if !ai.PDS.Valid {
		panic("must have pds for user in queue")
	}

	userCrawlsEnqueued.Inc()

	ctx, span := otel.Tracer("crawler").Start(ctx, "addToCrawler")
	defer span.End()

	select {
	case c.ingest <- ai:
		return nil
	case <-ctx.Done():
		return ctx.Err()
	}
}

func (c *CrawlDispatcher) AddToCatchupQueue(
	ctx context.Context,
	host *atp.PDS,
	u *atp.Person,
	evt *comatproto.SyncSubscribeRepos_Commit,
) error {
	if !u.PDS.Valid {
		panic("must have pds for user in queue")
	}

	catchup := &catchupJob{
		evt:  evt,
		host: host,
		user: u,
	}

	cw := c.addToCatchupQueue(catchup)
	if cw == nil {
		return nil
	}

	select {
	case c.catchup <- cw:
		return nil
	case <-ctx.Done():
		return ctx.Err()
	}
}

func (c *CrawlDispatcher) RepoInSlowPath(ctx context.Context, uid atp.Aid) bool {
	c.maplk.Lock()
	defer c.maplk.Unlock()
	if _, ok := c.todo[uid]; ok {
		return true
	}

	if _, ok := c.inProgress[uid]; ok {
		return true
	}

	return false
}

func (c *CrawlDispatcher) countReposInSlowPath() int {
	c.maplk.Lock()
	defer c.maplk.Unlock()
	return len(c.inProgress) + len(c.todo)
}

func (c *CrawlDispatcher) CatchupRepoGaugePoller() {
	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()
	for {
		select {
		case <-c.done:
		case <-ticker.C:
			catchupReposGauge.Set(float64(c.countReposInSlowPath()))
		}
	}
}
