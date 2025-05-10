package indexer

import (
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
)

var referencesCrawled = promauto.NewCounter(prometheus.CounterOpts{
	Name: "indexer_references_crawled",
	Help: "Number of references crawled",
})

var externalPersonCreationAttempts = promauto.NewCounter(prometheus.CounterOpts{
	Name: "indexer_external_person_creation_attempts",
	Help: "Number of external person creation attempts",
})

var personCrawlsEnqueued = promauto.NewCounter(prometheus.CounterOpts{
	Name: "indexer_person_crawls_enqueued",
	Help: "Number of person crawls enqueued",
})

var reposFetched = promauto.NewCounterVec(prometheus.CounterOpts{
	Name: "indexer_repos_fetched",
	Help: "Number of repos fetched",
}, []string{"status"})

var catchupEventsEnqueued = promauto.NewCounterVec(prometheus.CounterOpts{
	Name: "indexer_catchup_events_enqueued",
	Help: "Number of catchup events enqueued",
}, []string{"how"})

var catchupEventsProcessed = promauto.NewCounter(prometheus.CounterOpts{
	Name: "indexer_catchup_events_processed",
	Help: "Number of catchup events processed",
})

var catchupEventsFailed = promauto.NewCounterVec(prometheus.CounterOpts{
	Name: "indexer_catchup_events_failed",
	Help: "Number of catchup events processed",
}, []string{"err"})

var catchupReposGauge = promauto.NewGauge(prometheus.GaugeOpts{
	Name: "indexer_catchup_repos",
	Help: "Number of repos waiting on catchup",
})
