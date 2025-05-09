package pds

import (
	"context"
	"database/sql"

	"github.com/bluesky-social/indigo/api/atproto"
	"github.com/referendumApp/referendumServices/internal/domain/atp"
	refApp "github.com/referendumApp/referendumServices/internal/domain/lexicon/referendumapp"
	refErr "github.com/referendumApp/referendumServices/internal/error"
	"github.com/referendumApp/referendumServices/internal/plc"
	"github.com/referendumApp/referendumServices/internal/util"
)

// CreateActor create DID in the PLC directory and initialize an 'Actor' struct
func (p *PDS) CreateActor(
	ctx context.Context,
	req refApp.ServerCreateAccount_Input,
	pw string,
) (*atp.Actor, *refErr.APIError) {
	var recoveryKey string
	if req.RecoveryKey != nil {
		recoveryKey = *req.RecoveryKey
	}
	if recoveryKey == "" {
		recoveryKey = p.km.RecoveryKey()
	}

	sigkey, err := p.km.CreateSigningKey(ctx)
	if err != nil {
		return nil, refErr.InternalServer()
	}

	did, err := p.plc.CreateDID(ctx, sigkey, []string{recoveryKey, p.km.RotationKey()}, req.Handle, p.serviceUrl)
	if err != nil {
		p.log.ErrorContext(ctx, "Failed to create DID", "error", err)
		return nil, refErr.PLCServer()
	}

	if err := p.km.CreateEncryptedKey(ctx, did, sigkey); err != nil {
		p.log.ErrorContext(ctx, "Failed to create encrypted signing key", "error", err)
		return nil, refErr.InternalServer()
	}

	actor := &atp.Actor{
		Handle:         sql.NullString{String: req.Handle, Valid: true},
		Email:          sql.NullString{String: req.Email, Valid: true},
		HashedPassword: sql.NullString{String: pw, Valid: true},
		RecoveryKey:    recoveryKey,
		Did:            did,
	}

	return actor, nil
}

// CreateNewRepo initialize a new repo and write the first record to the CAR store
func (p *PDS) CreateNewRepo(
	ctx context.Context,
	actor *atp.Actor,
	dname string,
) (*refApp.ServerCreateAccount_Output, *refErr.APIError) {
	profile := &refApp.PersonProfile{
		DisplayName: &dname,
	}

	if err := p.repoman.InitNewRepo(ctx, actor.ID, actor.Did, profile.NSID(), profile.Key(), profile); err != nil {
		p.log.ErrorContext(ctx, "Error initializing new actor repository", "error", err, "did", actor.Did)
		return nil, refErr.Repo()
	}

	accessToken, refreshToken, err := p.CreateTokens(ctx, actor.ID, actor.Did)
	if err != nil {
		return nil, refErr.InternalServer()
	}

	return &refApp.ServerCreateAccount_Output{
		Did:          actor.Did,
		DisplayName:  dname,
		Handle:       actor.Handle.String,
		AccessToken:  accessToken,
		RefreshToken: refreshToken,
		TokenType:    p.jwt.AuthScheme,
	}, nil
}

// CreateTokens method to create the access and refresh tokens and update the signing key cache for a session
func (p *PDS) CreateTokens(ctx context.Context, uid atp.Aid, did string) (string, string, error) {
	accessToken, err := p.jwt.CreateToken(uid, did, util.Access)
	if err != nil {
		p.log.ErrorContext(ctx, "Failed to create access token", "error", err)
		return "", "", err
	}
	refreshToken, err := p.jwt.CreateToken(uid, did, util.Refresh)
	if err != nil {
		p.log.ErrorContext(ctx, "Failed to create refresh token", "error", err)
		return "", "", err
	}

	return accessToken, refreshToken, nil
}

// CreateSession completes a login request and returns the access and refresh tokens
func (p *PDS) CreateSession(
	ctx context.Context,
	actor *atp.Actor,
) (*refApp.ServerCreateSession_Output, *refErr.APIError) {
	accessToken, refreshToken, err := p.CreateTokens(ctx, actor.ID, actor.Did)
	if err != nil {
		return nil, refErr.InternalServer()
	}

	if err := p.km.UpdateKeyCache(ctx, actor.Did); err != nil {
		return nil, refErr.InternalServer()
	}

	return &refApp.ServerCreateSession_Output{
		Did:          actor.Did,
		Handle:       actor.Handle.String,
		AccessToken:  accessToken,
		RefreshToken: refreshToken,
		TokenType:    p.jwt.AuthScheme,
	}, nil
}

// RefreshSession refreshes the JWT refresh token
// TODO: store the token in a HTTP cookie
func (p *PDS) RefreshSession(
	ctx context.Context,
	refreshToken string,
) (*refApp.ServerRefreshSession_Output, atp.Aid, string, *refErr.APIError) {
	token, err := p.jwt.DecodeJWT(refreshToken)
	if err != nil {
		p.log.ErrorContext(ctx, "Failed to decode refresh token", "error", err)
		return nil, 0, "", refErr.Unauthorized("Invalid refresh token")
	}

	// Parse and validate the token
	uid, did, err := util.ValidateToken(token, util.Refresh)
	if err != nil {
		p.log.ErrorContext(ctx, "Token validation failed", "error", err)
		return nil, 0, "", refErr.BadRequest("Failed to validate refresh token")
	}

	accessToken, refreshToken, err := p.CreateTokens(ctx, uid, did)
	if err != nil {
		return nil, 0, "", refErr.InternalServer()
	}

	if err := p.km.UpdateKeyCache(ctx, did); err != nil {
		return nil, 0, "", refErr.InternalServer()
	}

	resp := &refApp.ServerRefreshSession_Output{
		AccessToken:  accessToken,
		RefreshToken: refreshToken,
		TokenType:    p.jwt.AuthScheme,
	}

	return resp, uid, did, nil
}

func (p *PDS) DeleteSession(ctx context.Context, did string) *refErr.APIError {
	p.km.InvalidateKeys(ctx, did)

	return nil
}

// DeleteAccount tombstones the DID in the PLC, deletes DB metadata, and deletes CAR files
func (p *PDS) DeleteAccount(ctx context.Context, uid atp.Aid, did string) *refErr.APIError {
	op, err := p.plc.GetLatestOp(ctx, did)
	if err != nil {
		p.log.ErrorContext(ctx, "Error searching for latest operation in PLC log", "error", err)
		return refErr.PLCServer()
	}

	if operation, ok := op.Operation.(*plc.Op); !ok {
		p.log.ErrorContext(ctx, "Latest operation in PLC audit log is invalid", "did", did)
		return refErr.BadRequest("Invalid operation in PLC directory audit log")
	} else if operation.Type == "plc_tombstone" {
		p.log.ErrorContext(ctx, "Actor has already been tombstoned in the PLC directory", "did", did)
		return refErr.BadRequest("Actor has already been deleted")
	}

	if err := p.plc.TombstoneDID(ctx, did, op.CID); err != nil {
		p.log.ErrorContext(ctx, "Tombstone request to PLC directory failed", "error", err)
		return refErr.PLCServer()
	}

	if err := p.repoman.TakeDownRepo(ctx, uid); err != nil {
		p.log.ErrorContext(ctx, "Failed to delete take down repo", "error", err)
		return refErr.Repo()
	}

	p.km.InvalidateKeys(ctx, did)

	return nil
}

// HandleAtprotoDescribeServer provides server metadata for websocket conusmers
func (p *PDS) HandleAtprotoDescribeServer() *atproto.ServerDescribeServer_Output {
	// TODO: Add some other fields here
	return &atproto.ServerDescribeServer_Output{AvailableUserDomains: []string{p.handleSuffix}}
}
