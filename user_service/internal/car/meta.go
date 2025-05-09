package car

import (
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

// StoreMeta embeds the DB specifically for CAR store related queries
type StoreMeta struct {
	*database.DB
}

// HasUidCid checks that a user has block references
func (cs *StoreMeta) HasUidCid(ctx context.Context, user atp.Aid, k cid.Cid) (bool, error) {
	var count int64
	leftTbl := cs.Schema + "." + BlockRef{}.TableName()
	rightTbl := cs.Schema + "." + Shard{}.TableName()
	psql := sq.StatementBuilder.PlaceholderFormat(sq.Dollar)

	sql, args, err := psql.
		Select("COUNT(*)").
		From(leftTbl).
		LeftJoin(fmt.Sprintf("%s ON %s.shard = %s.id", rightTbl, leftTbl, rightTbl)).
		Where(sq.Eq{"uid": user}, sq.Eq{"cid": atp.DbCID{CID: k}}).ToSql()
	if err != nil {
		cs.Log.ErrorContext(ctx, "Error building left join query", "error", err)
		return false, err
	}

	if err := cs.GetRow(ctx, sql, args...).Scan(&count); err != nil {
		cs.Log.ErrorContext(ctx, "Error scanning row", "error", err, "sql", sql, "args", args)
		return false, err
	}

	return count > 0, nil
}

// LookupBlockRef for some Cid, lookup the block ref
// Return the path of the file written, the offset within the file, and the user associated with the Cid
func (cs *StoreMeta) LookupBlockRef(ctx context.Context, k cid.Cid) (string, int64, atp.Aid, error) {
	var path string
	var offset int64
	var uid atp.Aid
	sql := "SELECT (SELECT path FROM carstore.car_shards WHERE id = block_refs.shard) AS path, block_refs.byte_offset, block_refs.uid FROM carstore.block_refs WHERE block_refs.cid = $1"
	if err := cs.GetRow(ctx, sql, atp.DbCID{CID: k}).Scan(&path, &offset, &uid); err != nil {
		cs.Log.ErrorContext(ctx, "Error scanning row", "error", err, "sql", sql, "cid", k)
		var defaultUser atp.Aid
		return "", -1, defaultUser, err
	}

	return path, offset, uid, nil
}

// GetLastShard queries the car_shards table for the most recent shard written to the store
func (cs *StoreMeta) GetLastShard(ctx context.Context, user atp.Aid) (*Shard, error) {
	filter := sq.Eq{"uid": user}

	query, err := database.BuildSelectAll(&Shard{}, cs.Schema, filter)
	if err != nil {
		cs.Log.ErrorContext(ctx, "Error building last shard query", "error", err, "uid", user)
		return nil, err
	}

	sql, args, err := query.OrderBy("seq DESC").ToSql()
	if err != nil {
		cs.Log.ErrorContext(ctx, "Error building raw last shard query", "error", err, "uid", user)
		return nil, err
	}

	lastShard, err := database.Get[Shard](ctx, cs.DB, sql, args...)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			cs.Log.InfoContext(ctx, "No CAR shards found")
			return &Shard{}, nil
		}
		cs.Log.ErrorContext(ctx, "Error querying for last shard", "error", err, "sql", sql)
		return nil, err
	}

	return lastShard, nil
}

// GetUserShards return all of a users's shards, ascending by Seq
func (cs *StoreMeta) GetUserShards(ctx context.Context, user atp.Aid) ([]*Shard, error) {
	filter := sq.Eq{"uid": user}

	query, err := database.BuildSelectAll(&Shard{}, cs.Schema, filter)
	if err != nil {
		cs.Log.ErrorContext(ctx, "Error building CAR shards query", "error", err, "uid", user)
		return nil, err
	}

	sql, args, err := query.OrderBy("seq ASC").ToSql()
	if err != nil {
		cs.Log.ErrorContext(ctx, "Error building CAR shards query", "error", err, "uid", user)
		return nil, err
	}

	shards, err := database.Select[Shard](ctx, cs.DB, sql, args...)
	if err != nil {
		cs.Log.ErrorContext(ctx, "Error querying CAR shards", "error", err, "sql", sql)
		return nil, err
	}

	return shards, nil
}

// GetUserShardsDesc return all of a users's shards, descending by Seq
func (cs *StoreMeta) GetUserShardsDesc(ctx context.Context, user atp.Aid, minSeq int) ([]*Shard, error) {
	filter := sq.And{sq.Eq{"uid": user}, sq.GtOrEq{"seq": minSeq}}

	query, err := database.BuildSelectAll(&Shard{}, cs.Schema, filter)
	if err != nil {
		cs.Log.ErrorContext(ctx, "Error building CAR shards query", "error", err, "uid", user)
		return nil, err
	}

	sql, args, err := query.OrderBy("seq DESC").ToSql()
	if err != nil {
		cs.Log.ErrorContext(ctx, "Error building raw CAR shards query", "error", err, "uid", user)
		return nil, err
	}

	shards, err := database.Select[Shard](ctx, cs.DB, sql, args...)
	if err != nil {
		cs.Log.ErrorContext(ctx, "Error querying for CAR shards", "error", err, "sql", sql)
		return nil, err
	}

	return shards, nil
}

// SeqForRev return the CAR shard sequence number for a revision
func (cs *StoreMeta) SeqForRev(ctx context.Context, user atp.Aid, sinceRev string) (int, error) {
	var seq int

	filter := sq.And{sq.Eq{"uid": user}, sq.GtOrEq{"rev": sinceRev}}
	psql := sq.StatementBuilder.PlaceholderFormat(sq.Dollar)

	sql, args, err := psql.Select("seq").From(Shard{}.TableName()).Where(filter).OrderBy("rev ASC").ToSql()
	if err != nil {
		cs.Log.ErrorContext(ctx, "Error building early shard query", "error", err, "uid", user)
		return 0, err
	}

	if err := cs.GetRow(ctx, sql, args...).Scan(&seq); err != nil {
		cs.Log.ErrorContext(ctx, "Error finding early shard", "error", err, "uid", user)
		return 0, err
	}

	return seq, nil
}

// GetCompactionTargets return the number of CAR shards for each user
func (cs *StoreMeta) GetCompactionTargets(ctx context.Context, minShardCount int) ([]*CompactionTarget, error) {
	sql := fmt.Sprintf(
		"SELECT usr, count(*) as num_shards FROM %s.%s GROUP BY usr HAVING count(*) > $1 ORDER BY num_shards DESC",
		cs.Schema,
		Shard{}.TableName(),
	)

	targets, err := database.Select[CompactionTarget](ctx, cs.DB, sql, minShardCount)
	if err != nil {
		cs.Log.ErrorContext(ctx, "Error executing compaction target query", "error", err)
		return nil, err
	}

	return targets, nil
}

// PutShardAndRefs inserts records to the car_shards and block_refs tables
func (cs *StoreMeta) PutShardAndRefs(ctx context.Context, shard *Shard, brefs []*BlockRef) error {
	// TODO: Can use a CTE to insert both the shard and block refs in the same query
	if err := cs.WithTransaction(ctx, func(ctx context.Context, tx pgx.Tx) error {
		row, err := database.CreateReturningWithTx(ctx, cs.DB, tx, shard, "id")
		if err != nil {
			cs.Log.ErrorContext(ctx, "Error creating shard", "error", err)
			return err
		}

		if serr := row.Scan(&shard.ID); serr != nil {
			cs.Log.ErrorContext(ctx, "Failed to scan new User ID", "error", serr)
			return serr
		}

		batchSize := 2000
		for i := 0; i < len(brefs); i += batchSize {
			entities := make([]database.TableEntity, 0, batchSize)
			batch := brefs[i:]
			if len(batch) > batchSize {
				batch = batch[:batchSize]
			}

			for _, ref := range batch {
				ref.Shard = shard.ID
				entities = append(entities, ref)
			}

			if err := cs.CreateBatchWithTx(ctx, tx, entities); err != nil {
				cs.Log.ErrorContext(ctx, "Error batch creating block refs", "error", err)
				return err
			}
		}

		return nil
	}); err != nil {
		return err
	}

	return nil
}

// DeleteShardsAndRefs deletes records from the car_shards and block_refs tables
func (cs *StoreMeta) DeleteShardsAndRefs(ctx context.Context, ids []uint) error {
	if err := cs.WithTransaction(ctx, func(ctx context.Context, tx pgx.Tx) error {
		blkFilter := sq.Eq{"shard": ids}
		if err := cs.DeleteWithTx(ctx, tx, &BlockRef{}, blkFilter); err != nil {
			cs.Log.ErrorContext(ctx, "Error deleting block refs", "error", err, "ids", ids)
			return err
		}

		sdFilter := sq.Eq{"id": ids}
		if err := cs.DeleteWithTx(ctx, tx, &Shard{}, sdFilter); err != nil {
			cs.Log.ErrorContext(ctx, "Error deleting shards", "error", err, "ids", ids)
			return err
		}

		return nil
	}); err != nil {
		return err
	}

	return nil
}

// GetBlockRefsForShards get the block refs based off a slice of CAR shards
func (cs *StoreMeta) GetBlockRefsForShards(ctx context.Context, shardIds []uint) ([]*BlockRef, error) {
	chunkSize := 2000
	out := make([]*BlockRef, 0, len(shardIds))
	for i := 0; i < len(shardIds); i += chunkSize {
		sl := shardIds[i:]
		if len(sl) > chunkSize {
			sl = sl[:chunkSize]
		}

		sval := valuesStatementForShards(sl)
		sql := fmt.Sprintf(
			`SELECT block_refs.* FROM carstore.block_refs INNER JOIN (VALUES %s) AS vals(v) ON block_refs.shard = v`,
			sval,
		)

		chunkResults, err := database.Select[BlockRef](ctx, cs.DB, sql)
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
