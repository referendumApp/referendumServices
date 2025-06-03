// //revive:disable:exported
package indexer

// import (
// 	"context"
// 	"errors"
// 	"fmt"
// 	"log/slog"
// 	"time"

// 	sq "github.com/Masterminds/squirrel"
// 	comatproto "github.com/bluesky-social/indigo/api/atproto"
// 	bsky "github.com/bluesky-social/indigo/api/bsky"
// 	"github.com/bluesky-social/indigo/did"
// 	lexutil "github.com/bluesky-social/indigo/lex/util"
// 	"github.com/bluesky-social/indigo/util"
// 	"github.com/bluesky-social/indigo/xrpc"
// 	"github.com/ipfs/go-cid"
// 	"github.com/jackc/pgx/v5"
// 	"github.com/referendumApp/referendumServices/internal/database"
// 	"github.com/referendumApp/referendumServices/internal/domain/atp"
// 	"github.com/referendumApp/referendumServices/internal/events"
// 	"github.com/referendumApp/referendumServices/internal/repo"
// 	"go.opentelemetry.io/otel"
// )

// const MaxEventSliceLength = 1000000
// const MaxOpsSliceLength = 200

// type Indexer struct {
// 	db      *database.DB
// 	events  *events.EventManager
// 	Crawler *CrawlDispatcher
// 	log     *slog.Logger

// 	SendRemoteFollow       func(context.Context, string, uint) error
// 	CreateExternalUser     func(context.Context, string) (*atp.User, error)
// 	ApplyPDSClientSettings func(*xrpc.Client)

// 	didr did.Resolver

// 	doAggregations bool
// 	doSpider       bool
// }

// func NewIndexer(
// 	db *database.DB,
// 	evtman *events.EventManager,
// 	didr did.Resolver,
// 	fetcher *RepoFetcher,
// 	crawl, aggregate, spider bool,
// ) (*Indexer, error) {
// 	ix := &Indexer{
// 		db:             db,
// 		events:         evtman,
// 		didr:           didr,
// 		doAggregations: aggregate,
// 		doSpider:       spider,
// 		SendRemoteFollow: func(context.Context, string, uint) error {
// 			return nil
// 		},
// 		ApplyPDSClientSettings: func(*xrpc.Client) {},
// 		log:                    slog.Default().With("system", "indexer"),
// 	}

// 	if crawl {
// 		c, err := NewCrawlDispatcher(fetcher, fetcher.MaxConcurrency, ix.log)
// 		if err != nil {
// 			return nil, err
// 		}

// 		ix.Crawler = c
// 		ix.Crawler.Run()
// 	}

// 	return ix, nil
// }

// func (ix *Indexer) Shutdown() {
// 	if ix.Crawler != nil {
// 		ix.Crawler.Shutdown()
// 	}
// }

// func (ix *Indexer) HandleRepoEvent(ctx context.Context, evt *repo.Event) error {
// 	ctx, span := otel.Tracer("indexer").Start(ctx, "HandleRepoEvent")
// 	defer span.End()

// 	ix.log.DebugContext(ctx, "Handling Repo Event!", "aid", evt.Actor)

// 	outops := make([]*comatproto.SyncSubscribeRepos_RepoOp, 0, len(evt.Ops))
// 	for _, op := range evt.Ops {
// 		link := (*lexutil.LexLink)(op.RecCid)
// 		outops = append(outops, &comatproto.SyncSubscribeRepos_RepoOp{
// 			Path:   op.Collection + "/" + op.Rkey,
// 			Action: string(op.Kind),
// 			Cid:    link,
// 		})

// 		if err := ix.handleRepoOp(ctx, evt, &op); err != nil {
// 			ix.log.ErrorContext(ctx, "failed to handle repo op", "error", err)
// 		}
// 	}

// 	did, err := ix.db.LookupDidByAid(ctx, evt.Actor)
// 	if err != nil {
// 		return err
// 	}

// 	toobig := false
// 	slice := evt.RepoSlice
// 	if len(slice) > MaxEventSliceLength || len(outops) > MaxOpsSliceLength {
// 		slice = []byte{}
// 		outops = nil
// 		toobig = true
// 	}

// 	ix.log.DebugContext(ctx, "Sending event", "did", did)
// 	if err := ix.events.AddEvent(ctx, &events.XRPCStreamEvent{
// 		RepoCommit: &comatproto.SyncSubscribeRepos_Commit{
// 			Repo:   did,
// 			Blocks: slice,
// 			Rev:    evt.Rev,
// 			Since:  evt.Since,
// 			Commit: lexutil.LexLink(evt.NewRoot),
// 			Time:   time.Now().Format(util.ISO8601),
// 			Ops:    outops,
// 			TooBig: toobig,
// 		},
// 		PrivUid: evt.Actor,
// 	}); err != nil {
// 		return fmt.Errorf("failed to push event: %w", err)
// 	}

// 	return nil
// }

// func (ix *Indexer) handleRepoOp(ctx context.Context, evt *repo.Event, op *repo.Op) error {
// 	switch op.Kind {
// 	case repo.EvtKindCreateRecord:
// 		if ix.doAggregations {
// 			_, err := ix.handleRecordCreate(ctx, evt, op, true)
// 			if err != nil {
// 				return fmt.Errorf("handle recordCreate: %w", err)
// 			}
// 		}
// 		if ix.doSpider {
// 			if err := ix.crawlRecordReferences(ctx, op); err != nil {
// 				return err
// 			}
// 		}
// 	case repo.EvtKindDeleteRecord:
// 		if ix.doAggregations {
// 			if err := ix.handleRecordDelete(ctx, evt, op, true); err != nil {
// 				return fmt.Errorf("handle recordDelete: %w", err)
// 			}
// 		}
// 	case repo.EvtKindUpdateRecord:
// 		if ix.doAggregations {
// 			if err := ix.handleRecordUpdate(ctx, evt, op, true); err != nil {
// 				return fmt.Errorf("handle recordCreate: %w", err)
// 			}
// 		}
// 	default:
// 		return fmt.Errorf("unrecognized repo event type: %q", op.Kind)
// 	}

// 	return nil
// }

// func (ix *Indexer) crawlAtUriRef(ctx context.Context, uri string) error {
// 	puri, err := util.ParseAtUri(uri)
// 	if err != nil {
// 		return err
// 	}

// 	referencesCrawled.Inc()

// 	_, err = ix.GetUserOrMissing(ctx, puri.Did)
// 	if err != nil {
// 		return err
// 	}
// 	return nil
// }

// func (ix *Indexer) crawlRecordReferences(ctx context.Context, op *repo.Op) error {
// 	ctx, span := otel.Tracer("indexer").Start(ctx, "crawlRecordReferences")
// 	defer span.End()

// 	switch rec := op.Record.(type) {
// 	case *bsky.FeedPost:
// 		for _, e := range rec.Entities {
// 			if e.Type == "mention" {
// 				_, err := ix.GetUserOrMissing(ctx, e.Value)
// 				if err != nil {
// 					ix.log.InfoContext(ctx, "failed to parse user mention", "ref", e.Value, "error", err)
// 				}
// 			}
// 		}

// 		if rec.Reply == nil {
// 			return nil
// 		}

// 		if rec.Reply.Parent != nil {
// 			if err := ix.crawlAtUriRef(ctx, rec.Reply.Parent.Uri); err != nil {
// 				ix.log.InfoContext(ctx, "failed to crawl reply parent", "cid", op.RecCid, "replyuri", rec.Reply.Parent.Uri, "error", err)
// 			}
// 		}

// 		if rec.Reply.Root != nil {
// 			if err := ix.crawlAtUriRef(ctx, rec.Reply.Root.Uri); err != nil {
// 				ix.log.InfoContext(ctx, "failed to crawl reply root", "cid", op.RecCid, "rooturi", rec.Reply.Root.Uri, "error", err)
// 			}
// 		}

// 		return nil
// 	case *bsky.FeedRepost:
// 		if rec.Subject != nil {
// 			if err := ix.crawlAtUriRef(ctx, rec.Subject.Uri); err != nil {
// 				ix.log.InfoContext(ctx, "failed to crawl repost subject", "cid", op.RecCid, "subjecturi", rec.Subject.Uri, "error", err)
// 			}
// 		}
// 		return nil
// 	case *bsky.FeedLike:
// 		if rec.Subject != nil {
// 			if err := ix.crawlAtUriRef(ctx, rec.Subject.Uri); err != nil {
// 				ix.log.InfoContext(ctx, "failed to crawl like subject", "cid", op.RecCid, "subjecturi", rec.Subject.Uri, "error", err)
// 			}
// 		}
// 		return nil
// 	case *bsky.GraphFollow:
// 		_, err := ix.GetUserOrMissing(ctx, rec.Subject)
// 		if err != nil {
// 			ix.log.InfoContext(ctx, "failed to crawl follow subject", "cid", op.RecCid, "subjectdid", rec.Subject, "error", err)
// 		}
// 		return nil
// 	case *bsky.GraphBlock:
// 		_, err := ix.GetUserOrMissing(ctx, rec.Subject)
// 		if err != nil {
// 			ix.log.InfoContext(ctx, "failed to crawl follow subject", "cid", op.RecCid, "subjectdid", rec.Subject, "error", err)
// 		}
// 		return nil
// 	case *bsky.ActorProfile:
// 		return nil
// 	case *bsky.GraphList:
// 		return nil
// 	case *bsky.GraphListitem:
// 		return nil
// 	case *bsky.FeedGenerator:
// 		return nil
// 	default:
// 		ix.log.WarnContext(ctx, "unrecognized record type (crawling references)", "record", op.Record, "collection", op.Collection)
// 		return nil
// 	}
// }

// func (ix *Indexer) GetUserOrMissing(ctx context.Context, did string) (*atp.User, error) {
// 	ctx, span := otel.Tracer("indexer").Start(ctx, "GetUserOrMissing")
// 	defer span.End()

// 	ai, err := ix.db.LookupUserByDid(ctx, did)
// 	if err == nil {
// 		return ai, nil
// 	}

// 	if !errors.Is(err, pgx.ErrNoRows) {
// 		return nil, err
// 	}

// 	// unknown user... create it and send it off to the crawler
// 	return ix.createMissingUserRecord(ctx, did)
// }

// func (ix *Indexer) createMissingUserRecord(ctx context.Context, did string) (*atp.User, error) {
// 	ctx, span := otel.Tracer("indexer").Start(ctx, "createMissingUserRecord")
// 	defer span.End()

// 	externalUserCreationAttempts.Inc()

// 	user, err := ix.CreateExternalUser(ctx, did)
// 	if err != nil {
// 		return nil, err
// 	}

// 	if err := ix.addUserToCrawler(ctx, user); err != nil {
// 		return nil, fmt.Errorf("failed to add unknown user to crawler: %w", err)
// 	}

// 	return user, nil
// }

// func (ix *Indexer) addUserToCrawler(ctx context.Context, ai *atp.User) error {
// 	ix.log.DebugContext(ctx, "Sending user to crawler: ", "did", ai.Did)
// 	if ix.Crawler == nil {
// 		return nil
// 	}

// 	return ix.Crawler.Crawl(ctx, ai)
// }

// // func (ix *Indexer) handleInitActor(ctx context.Context, evt *repo.RepoEvent, op *repo.RepoOp) error {
// // 	ai := op.ActorInfo
// //
// // 	if err := ix.db.CreateWithConflict(ctx, &atp.User{
// // 		Aid:         evt.Actor,
// // 		Handle:      sql.NullString{String: ai.Handle, Valid: true},
// // 		Did:         ai.Did,
// // 		DisplayName: ai.DisplayName,
// // 		Type:        ai.Type,
// // 		PDS:         evt.PDS,
// // 	}, "aid"); err != nil {
// // 		return fmt.Errorf("initializing new actor info: %w", err)
// // 	}
// //
// // 	if err := ix.db.Create(ctx, &atp.UserFollowRecord{Follower: evt.User, Target: evt.User}); err != nil {
// // 		return err
// // 	}
// //
// // 	return nil
// // }

// func (ix *Indexer) GetPost(ctx context.Context, uri string) (*atp.ActivityPost, error) {
// 	puri, err := util.ParseAtUri(uri)
// 	if err != nil {
// 		return nil, err
// 	}

// 	post, err := ix.db.LookupActivityPostByDid(ctx, puri.Rkey, puri.Did)
// 	if err != nil {
// 		return nil, err
// 	}

// 	return post, nil
// }

// func (ix *Indexer) handleRecordDelete(ctx context.Context, evt *repo.Event, op *repo.Op, local bool) error {
// 	ix.log.DebugContext(ctx, "record delete event", "collection", op.Collection)

// 	switch op.Collection {
// 	case "app.referendum.feed.post":
// 		u, err := ix.db.LookupUserByAid(ctx, evt.Actor)
// 		if err != nil {
// 			return err
// 		}

// 		uri := "at://" + u.Did + "/app.referendum.feed.post/" + op.Rkey

// 		// NB: currently not using the 'or missing' variant here. If we delete
// 		// something that we've never seen before, maybe just dont bother?
// 		fp, err := ix.GetPost(ctx, uri)
// 		if err != nil {
// 			if errors.Is(err, pgx.ErrNoRows) {
// 				ix.log.WarnContext(
// 					ctx,
// 					"deleting post weve never seen before. Weird.",
// 					"actor",
// 					evt.Actor,
// 					"rkey",
// 					op.Rkey,
// 				)
// 				return nil
// 			}
// 			return err
// 		}

// 		if err := ix.db.Update(ctx, &atp.ActivityPost{Deleted: true}, sq.Eq{"id": fp.ID}); err != nil {
// 			return err
// 		}
// 	case "app.referendum.feed.vote":
// 		return ix.db.HandleRecordDeleteFeedLike(ctx, evt.Actor, op.Rkey)
// 	case "app.referendum.graph.follow":
// 		return ix.db.HandleRecordDeleteGraphFollow(ctx, evt.Actor, op.Rkey)
// 	case "app.referendum.graph.confirmation":
// 		return nil
// 	default:
// 		return fmt.Errorf("unrecognized record type (delete): %q", op.Collection)
// 	}

// 	return nil
// }

// func (ix *Indexer) handleRecordCreate(ctx context.Context, evt *repo.Event, op *repo.Op, local bool) ([]uint, error) {
// 	ix.log.DebugContext(ctx, "record create event", "collection", op.Collection)

// 	var out []uint
// 	switch rec := op.Record.(type) {
// 	case *bsky.FeedPost:
// 		if err := ix.handleRecordCreateActivityPost(ctx, evt.Actor, op.Rkey, *op.RecCid, rec); err != nil {
// 			return nil, err
// 		}

// 	case *bsky.FeedLike:
// 		return nil, ix.handleRecordCreateFeedLike(ctx, rec, evt, op)
// 	case *bsky.GraphFollow:
// 		return out, ix.handleRecordCreateGraphFollow(ctx, rec, evt, op)
// 	case *bsky.GraphBlock:
// 		return out, nil
// 	case *bsky.GraphList:
// 		return out, nil
// 	case *bsky.GraphListitem:
// 		return out, nil
// 	case *bsky.FeedGenerator:
// 		return out, nil
// 	case *bsky.ActorProfile:
// 		ix.log.DebugContext(ctx, "TODO: got actor profile record creation, need to do something with this")
// 	default:
// 		ix.log.WarnContext(ctx, "unrecognized record", "record", op.Record, "collection", op.Collection)
// 		return nil, fmt.Errorf("unrecognized record type (creation): %s", op.Collection)
// 	}

// 	return out, nil
// }

// func (ix *Indexer) handleRecordCreateFeedLike(
// 	ctx context.Context,
// 	rec *bsky.FeedLike,
// 	evt *repo.Event,
// 	op *repo.Op,
// ) error {
// 	post, err := ix.GetPostOrMissing(ctx, rec.Subject.Uri)
// 	if err != nil {
// 		return err
// 	}

// 	act, err := ix.db.LookupUserByAid(ctx, post.Author)
// 	if err != nil {
// 		return err
// 	}

// 	vr := &atp.EndorsementRecord{
// 		Endorser: evt.Actor,
// 		Post:     post.ID,
// 		Created:  rec.CreatedAt,
// 		Rkey:     op.Rkey,
// 		Cid:      atp.DbCID{CID: *op.RecCid},
// 	}
// 	if err := ix.db.Create(ctx, vr); err != nil {
// 		return err
// 	}

// 	if err := ix.db.UpdateActivityPostUpCount(ctx, post.ID); err != nil {
// 		return err
// 	}
// 	if err := ix.addNewVoteNotification(ctx, act.Aid, vr); err != nil {
// 		return err
// 	}

// 	return nil
// }

// func (ix *Indexer) handleRecordCreateGraphFollow(
// 	ctx context.Context,
// 	rec *bsky.GraphFollow,
// 	evt *repo.Event,
// 	op *repo.Op,
// ) error {
// 	subj, err := ix.db.LookupUserByDid(ctx, rec.Subject)
// 	if err != nil {
// 		if !errors.Is(err, pgx.ErrNoRows) {
// 			return fmt.Errorf("failed to lookup user: %w", err)
// 		}

// 		nu, err := ix.createMissingUserRecord(ctx, rec.Subject)
// 		if err != nil {
// 			return fmt.Errorf("create external user: %w", err)
// 		}

// 		subj = nu
// 	}

// 	// 'follower' followed 'target'
// 	fr := &atp.ActorFollowRecord{
// 		Follower: evt.Actor,
// 		Target:   subj.Aid,
// 		Rkey:     op.Rkey,
// 		Cid:      atp.DbCID{CID: *op.RecCid},
// 	}
// 	if err := ix.db.Create(ctx, fr); err != nil {
// 		return err
// 	}

// 	return nil
// }

// func (ix *Indexer) handleRecordUpdate(ctx context.Context, evt *repo.Event, op *repo.Op, local bool) error {
// 	ix.log.DebugContext(ctx, "record update event", "collection", op.Collection)

// 	switch rec := op.Record.(type) {
// 	case *bsky.FeedPost:
// 		u, err := ix.db.LookupUserByAid(ctx, evt.Actor)
// 		if err != nil {
// 			return err
// 		}

// 		uri := "at://" + u.Did + "/app.bsky.feed.post/" + op.Rkey
// 		fp, err := ix.GetPostOrMissing(ctx, uri)
// 		if err != nil {
// 			return err
// 		}

// 		oldReply := fp.ReplyTo != 0
// 		newReply := rec.Reply != nil

// 		if oldReply != newReply {
// 			// the 'replyness' of the post was changed... that's weird
// 			ix.log.ErrorContext(ctx, "need to properly handle case where reply-ness of posts is changed")
// 			return nil
// 		}

// 		if newReply {
// 			replyto, err := ix.GetPostOrMissing(ctx, rec.Reply.Parent.Uri)
// 			if err != nil {
// 				return err
// 			}

// 			if replyto.ID != fp.ReplyTo {
// 				ix.log.ErrorContext(ctx, "post was changed to be a reply to a different post")
// 				return nil
// 			}
// 		}

// 		if err := ix.db.Update(ctx, &atp.ActivityPost{Cid: atp.DbCID{CID: *op.RecCid}}, sq.Eq{"id": fp.ID}); err != nil {
// 			return err
// 		}

// 		return nil

// 	case *bsky.FeedLike:
// 		vr, err := ix.db.LookupEndorsementRecordByUid(ctx, evt.Actor, op.Rkey)
// 		if err != nil {
// 			return err
// 		}

// 		fp, err := ix.GetPostOrMissing(ctx, rec.Subject.Uri)
// 		if err != nil {
// 			return err
// 		}

// 		if vr.Post != fp.ID {
// 			// vote is on a completely different post, delete old one, create new one
// 			if err := ix.db.HandleRecordDeleteFeedLike(ctx, evt.Actor, op.Rkey); err != nil {
// 				return err
// 			}

// 			return ix.handleRecordCreateFeedLike(ctx, rec, evt, op)
// 		}

// 		return ix.handleRecordCreateFeedLike(ctx, rec, evt, op)
// 	case *bsky.GraphFollow:
// 		if err := ix.db.HandleRecordDeleteGraphFollow(ctx, evt.Actor, op.Rkey); err != nil {
// 			return err
// 		}

// 		return ix.handleRecordCreateGraphFollow(ctx, rec, evt, op)
// 	case *bsky.ActorProfile:
// 		ix.log.DebugContext(ctx, "TODO: got actor profile record update, need to do something with this")
// 	default:
// 		return fmt.Errorf("unrecognized record type (update): %s", op.Collection)
// 	}

// 	return nil
// }

// func (ix *Indexer) GetPostOrMissing(ctx context.Context, uri string) (*atp.ActivityPost, error) {
// 	puri, err := util.ParseAtUri(uri)
// 	if err != nil {
// 		return nil, err
// 	}

// 	post, err := ix.db.LookupActivityPostByDid(ctx, puri.Rkey, puri.Did)
// 	if err != nil {
// 		return nil, err
// 	}

// 	if post.ID == 0 {
// 		// reply to a post we don't know about, create a record for it anyway
// 		return ix.createMissingPostRecord(ctx, puri)
// 	}

// 	return post, nil
// }

// func (ix *Indexer) handleRecordCreateActivityPost(
// 	ctx context.Context,
// 	actor atp.Aid,
// 	rkey string,
// 	rcid cid.Cid,
// 	rec *bsky.FeedPost,
// ) error {
// 	var replyid uint
// 	if rec.Reply != nil {
// 		replyto, err := ix.GetPostOrMissing(ctx, rec.Reply.Parent.Uri)
// 		if err != nil {
// 			return err
// 		}

// 		replyid = replyto.ID

// 		rootref, err := ix.GetPostOrMissing(ctx, rec.Reply.Root.Uri)
// 		if err != nil {
// 			return err
// 		}

// 		// TODO: use this for indexing?
// 		_ = rootref
// 	}

// 	var mentions []*atp.User
// 	for _, e := range rec.Entities {
// 		if e.Type == "mention" {
// 			ai, err := ix.GetUserOrMissing(ctx, e.Value)
// 			if err != nil {
// 				return err
// 			}

// 			mentions = append(mentions, ai)
// 		}
// 	}

// 	// var maybe atp.ActivityPost
// 	maybe, err := ix.db.LookupActivityPostByUid(ctx, rkey, actor)
// 	if err != nil {
// 		return err
// 	}

// 	fp := &atp.ActivityPost{
// 		Rkey:    rkey,
// 		Cid:     atp.DbCID{CID: rcid},
// 		Author:  actor,
// 		ReplyTo: replyid,
// 	}

// 	if maybe.ID != 0 {
// 		// we're likely filling in a missing reference
// 		if !maybe.Missing {
// 			// TODO: we've already processed this record creation
// 			ix.log.WarnContext(ctx, "potentially erroneous event, duplicate create", "rkey", rkey, "actor", actor)
// 		}

// 		if err := ix.db.CreateConflict(ctx, fp, "rkey", "author"); err != nil {
// 			return fmt.Errorf("initializing new feed post: %w", err)
// 		}
// 	} else {
// 		if err := ix.db.Create(ctx, fp); err != nil {
// 			return err
// 		}
// 	}

// 	if err := ix.addNewPostNotification(ctx, rec, fp, mentions); err != nil {
// 		return err
// 	}

// 	return nil
// }

// func (ix *Indexer) createMissingPostRecord(ctx context.Context, puri *util.ParsedUri) (*atp.ActivityPost, error) {
// 	ix.log.WarnContext(ctx, "creating missing post record")
// 	ai, err := ix.GetUserOrMissing(ctx, puri.Did)
// 	if err != nil {
// 		return nil, err
// 	}

// 	fp, err := ix.db.LookupActivityPostByUid(ctx, puri.Rkey, ai.Aid)
// 	if err != nil {
// 		if !errors.Is(err, pgx.ErrNoRows) {
// 			return nil, err
// 		}
// 		newFp := &atp.ActivityPost{Author: ai.Aid, Rkey: puri.Rkey, Missing: true}
// 		if err := ix.db.Create(ctx, newFp); err != nil {
// 			return nil, err
// 		}
// 		return newFp, nil
// 	}

// 	return fp, nil
// }

// func (ix *Indexer) addNewPostNotification(
// 	ctx context.Context,
// 	post *bsky.FeedPost,
// 	fp *atp.ActivityPost,
// 	mentions []*atp.User,
// ) error {
// 	if post.Reply != nil {
// 		_, err := ix.GetPost(ctx, post.Reply.Parent.Uri)
// 		if err != nil {
// 			ix.log.ErrorContext(ctx, "probably shouldn't error when processing a reply to a not-found post")
// 			return err
// 		}
// 	}

// 	return nil
// }

// func (ix *Indexer) addNewVoteNotification(ctx context.Context, postauthor atp.Aid, vr *atp.EndorsementRecord) error {
// 	return nil
// }
