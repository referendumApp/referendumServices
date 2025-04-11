package car

import (
	"bytes"
	"context"
	"errors"
	"fmt"
	"strconv"
	"strings"

	sq "github.com/Masterminds/squirrel"
	"github.com/ipfs/go-cid"
	"github.com/jackc/pgx/v5"

	"github.com/referendumApp/referendumServices/internal/database"
	"github.com/referendumApp/referendumServices/internal/domain/atp"
)

type StoreMeta struct {
	db *database.DB
}

func (cs *StoreMeta) HasUidCid(ctx context.Context, user atp.Uid, k cid.Cid) (bool, error) {
	var count int64
	leftTbl := fmt.Sprintf("%s.%s", cs.db.Schema, BlockRef{}.TableName())
	rightTbl := fmt.Sprintf("%s.%s", cs.db.Schema, Shard{}.TableName())
	psql := sq.StatementBuilder.PlaceholderFormat(sq.Dollar)

	sql, args, err := psql.
		Select("COUNT(*)").
		From(leftTbl).
		LeftJoin(fmt.Sprintf("%s ON %s.shard = %s.id", rightTbl, leftTbl, rightTbl)).
		Where(sq.Eq{"uid": user}, sq.Eq{"cid": atp.DbCID{CID: k}}).ToSql()
	if err != nil {
		cs.db.Log.ErrorContext(ctx, "Error building left join query", "error", err)
		return false, err
	}

	if err := cs.db.GetRow(ctx, sql, args...).Scan(&count); err != nil {
		cs.db.Log.ErrorContext(ctx, "Error scanning row", "error", err, "sql", sql, "args", args)
		return false, err
	}

	return count > 0, nil
}

// For some Cid, lookup the block ref.
// Return the path of the file written, the offset within the file, and the user associated with the Cid.
func (cs *StoreMeta) LookupBlockRef(ctx context.Context, k cid.Cid) (string, int64, atp.Uid, error) {
	var path string
	var offset int64
	var uid atp.Uid
	sql := "SELECT (SELECT path FROM carstore.car_shards WHERE id = block_refs.shard) AS path, block_refs.byte_offset, block_refs.uid FROM carstore.block_refs WHERE block_refs.cid = $1"
	if err := cs.db.GetRow(ctx, sql, atp.DbCID{CID: k}).Scan(&path, &offset, &uid); err != nil {
		cs.db.Log.ErrorContext(ctx, "Error scanning row", "error", err, "sql", sql, "cid", k)
		var defaultUser atp.Uid
		return "", -1, defaultUser, err
	}

	return path, offset, uid, nil
}

func (cs *StoreMeta) GetLastShard(ctx context.Context, user atp.Uid) (*Shard, error) {
	filter := sq.Eq{"uid": user}

	query, err := database.BuildSelectAll(&Shard{}, cs.db.Schema, filter)
	if err != nil {
		cs.db.Log.ErrorContext(ctx, "Error building last shard query", "error", err, "uid", user)
		return nil, err
	}

	sql, args, err := query.OrderBy("seq DESC").ToSql()
	if err != nil {
		cs.db.Log.ErrorContext(ctx, "Error building raw last shard query", "error", err, "uid", user)
		return nil, err
	}

	lastShard, err := database.Get[Shard](ctx, cs.db, sql, args...)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			cs.db.Log.InfoContext(ctx, "No last shard found")
			return &Shard{}, nil
		}
		cs.db.Log.ErrorContext(ctx, "Error querying for last shard", "error", err, "sql", sql)
		return nil, err
	}

	return lastShard, nil
}

// return all of a users's shards, ascending by Seq
func (cs *StoreMeta) GetUserShards(ctx context.Context, user atp.Uid) ([]*Shard, error) {
	filter := sq.Eq{"uid": user}

	query, err := database.BuildSelectAll(&Shard{}, cs.db.Schema, filter)
	if err != nil {
		cs.db.Log.ErrorContext(ctx, "Error building car shards query", "error", err, "uid", user)
		return nil, err
	}

	sql, args, err := query.OrderBy("seq ASC").ToSql()
	if err != nil {
		cs.db.Log.ErrorContext(ctx, "Error building car shards query", "error", err, "uid", user)
		return nil, err
	}

	shards, err := database.Select[Shard](ctx, cs.db, sql, args...)
	if err != nil {
		cs.db.Log.ErrorContext(ctx, "Error querying car shards", "error", err, "sql", sql)
		return nil, err
	}

	return shards, nil
}

// return all of a users's shards, descending by Seq
func (cs *StoreMeta) GetUserShardsDesc(ctx context.Context, user atp.Uid, minSeq int) ([]*Shard, error) {
	filter := sq.And{sq.Eq{"uid": user}, sq.GtOrEq{"seq": minSeq}}

	query, err := database.BuildSelectAll(&Shard{}, cs.db.Schema, filter)
	if err != nil {
		cs.db.Log.ErrorContext(ctx, "Error building car shards query", "error", err, "uid", user)
		return nil, err
	}

	sql, args, err := query.OrderBy("seq DESC").ToSql()
	if err != nil {
		cs.db.Log.ErrorContext(ctx, "Error building raw car shards query", "error", err, "uid", user)
		return nil, err
	}

	shards, err := database.Select[Shard](ctx, cs.db, sql, args...)
	if err != nil {
		cs.db.Log.ErrorContext(ctx, "Error querying for car shards", "error", err, "sql", sql)
		return nil, err
	}

	return shards, nil
}

func (cs *StoreMeta) GetUserStaleRefs(ctx context.Context, user atp.Uid) ([]*StaleRef, error) {
	filter := sq.Eq{"uid": user}

	staleRefs, err := database.SelectAll(ctx, cs.db, StaleRef{}, filter)
	if err != nil {
		return nil, err
	}

	return staleRefs, nil
}

func (cs *StoreMeta) SeqForRev(ctx context.Context, user atp.Uid, sinceRev string) (int, error) {
	var seq int

	filter := sq.And{sq.Eq{"uid": user}, sq.GtOrEq{"rev": sinceRev}}
	psql := sq.StatementBuilder.PlaceholderFormat(sq.Dollar)

	sql, args, err := psql.Select("seq").From(Shard{}.TableName()).Where(filter).OrderBy("rev ASC").ToSql()
	if err != nil {
		cs.db.Log.ErrorContext(ctx, "Error building early shard query", "error", err, "uid", user)
		return 0, err
	}

	if err := cs.db.GetRow(ctx, sql, args...).Scan(&seq); err != nil {
		cs.db.Log.ErrorContext(ctx, "Error finding early shard", "error", err, "uid", user)
		return 0, err
	}

	return seq, nil
}

func (cs *StoreMeta) GetCompactionTargets(ctx context.Context, minShardCount int) ([]*CompactionTarget, error) {
	sql := fmt.Sprintf("select usr, count(*) as num_shards from %s.%s group by usr having count(*) > $1 order by num_shards desc", cs.db.Schema, Shard{}.TableName())

	targets, err := database.Select[CompactionTarget](ctx, cs.db, sql, minShardCount)
	if err != nil {
		cs.db.Log.ErrorContext(ctx, "Error executing compaction target query", "error", err)
		return nil, err
	}

	return targets, nil
}

func (cs *StoreMeta) PutShardAndRefs(ctx context.Context, shard *Shard, brefs []*BlockRef, rmcids map[cid.Cid]bool) error {
	// TODO: Can use a CTE to insert both the shard and block refs in the same query
	if err := cs.db.WithTransaction(ctx, func(ctx context.Context, tx pgx.Tx) error {
		newShard, err := database.CreateReturningWithTx(ctx, cs.db, tx, *shard, "id")
		if err != nil {
			cs.db.Log.ErrorContext(ctx, "Error creating shard", "error", err)
			return err
		}
		shard.ID = newShard.ID

		batchSize := 2000
		for i := 0; i < len(brefs); i += batchSize {
			entities := make([]database.TableEntity, 0, batchSize)
			batch := brefs[i:]
			if len(batch) > batchSize {
				batch = batch[:batchSize]
			}

			for _, ref := range batch {
				ref.Shard = newShard.ID
				entities = append(entities, ref)
			}

			if err := cs.db.CreateBatchWithTx(ctx, tx, entities); err != nil {
				cs.db.Log.ErrorContext(ctx, "Error batch creating block refs", "error", err)
				return err
			}
		}

		if len(rmcids) > 0 {
			cids := make([]cid.Cid, 0, len(rmcids))
			for c := range rmcids {
				cids = append(cids, c)
			}

			if err := cs.db.CreateWithTx(ctx, tx, &StaleRef{Cids: packCids(cids), Uid: shard.Uid}); err != nil {
				cs.db.Log.ErrorContext(ctx, "Error creating stale ref", "error", err)
				return err
			}
		}
		return nil
	}); err != nil {
		return err
	}

	return nil
}

func (cs *StoreMeta) DeleteShardsAndRefs(ctx context.Context, ids []uint) error {
	if err := cs.db.WithTransaction(ctx, func(ctx context.Context, tx pgx.Tx) error {
		sdFilter := sq.Eq{"id": ids}
		if err := cs.db.DeleteWithTx(ctx, tx, &Shard{}, sdFilter); err != nil {
			cs.db.Log.ErrorContext(ctx, "Error deleting shards", "error", err, "ids", ids)
			return err
		}

		blkFilter := sq.Eq{"shard": ids}
		if err := cs.db.DeleteWithTx(ctx, tx, &BlockRef{}, blkFilter); err != nil {
			cs.db.Log.ErrorContext(ctx, "Error deleting block refs", "error", err, "ids", ids)
			return err
		}

		return nil
	}); err != nil {
		return err
	}

	return nil
}

func (cs *StoreMeta) GetBlockRefsForShards(ctx context.Context, shardIds []uint) ([]*BlockRef, error) {
	chunkSize := 2000
	out := make([]*BlockRef, 0, len(shardIds))
	for i := 0; i < len(shardIds); i += chunkSize {
		sl := shardIds[i:]
		if len(sl) > chunkSize {
			sl = sl[:chunkSize]
		}

		sval := valuesStatementForShards(sl)
		sql := fmt.Sprintf(`SELECT block_refs.* FROM carstore.block_refs INNER JOIN (VALUES %s) AS vals(v) ON block_refs.shard = v`, sval)

		chunkResults, err := database.Select[BlockRef](ctx, cs.db, sql)
		if err != nil {
			return nil, fmt.Errorf("error getting block refs: %w", err)
		}

		out = append(out, chunkResults...)
	}
	return out, nil
}

// valuesStatementForShards builds a postgres compatible statement string from int literals
func valuesStatementForShards(shards []uint) string {
	sb := new(strings.Builder)
	for i, v := range shards {
		sb.WriteByte('(')
		sb.WriteString(strconv.FormatUint(uint64(v), 10))
		sb.WriteByte(')')
		if i != len(shards)-1 {
			sb.WriteByte(',')
		}
	}
	return sb.String()
}

func (cs *StoreMeta) SetStaleRef(ctx context.Context, uid atp.Uid, staleToKeep []cid.Cid) error {
	if err := cs.db.WithTransaction(ctx, func(ctx context.Context, tx pgx.Tx) error {
		filter := sq.Eq{"uid": uid}
		if err := cs.db.DeleteWithTx(ctx, tx, &StaleRef{}, filter); err != nil {
			cs.db.Log.ErrorContext(ctx, "Error deleting stale ref", "error", err)
			return err
		}

		// now create a new staleRef with all the refs we couldn't clear out
		if len(staleToKeep) > 0 {
			if err := cs.db.CreateWithTx(ctx, tx, &StaleRef{Cids: packCids(staleToKeep), Uid: uid}); err != nil {
				cs.db.Log.ErrorContext(ctx, "Error creating stale ref", "error", err)
				return err
			}
		}

		return nil
	}); err != nil {
		return err
	}

	return nil
}

func packCids(cids []cid.Cid) []byte {
	buf := new(bytes.Buffer)
	for _, c := range cids {
		buf.Write(c.Bytes())
	}

	return buf.Bytes()
}
