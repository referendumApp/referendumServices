package pds

import (
	"context"
	"database/sql"

	"github.com/bluesky-social/indigo/api/atproto"
	"github.com/referendumApp/referendumServices/internal/domain/atp"
	refApp "github.com/referendumApp/referendumServices/internal/domain/lexicon/referendumapp"
	refErr "github.com/referendumApp/referendumServices/internal/error"
	"github.com/referendumApp/referendumServices/internal/util"
)

// CreateUser create DID in the PLC directory and initialize a 'User' struct
func (p *PDS) CreateUser(
	ctx context.Context,
	req refApp.ServerCreateAccount_Input,
	pw string,
) (*atp.User, *refErr.APIError) {
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

	user := &atp.User{
		Handle:         sql.NullString{String: req.Handle, Valid: true},
		Email:          sql.NullString{String: req.Email, Valid: true},
		HashedPassword: sql.NullString{String: pw, Valid: true},
		RecoveryKey:    recoveryKey,
		Did:            did,
	}

	return user, nil
}

// CreateNewRepo initialize a new repo and write the first record to the CAR store
func (p *PDS) CreateNewRepo(
	ctx context.Context,
	user *atp.User,
	dname string,
) (*refApp.ServerCreateSession_Output, *refErr.APIError) {
	profile := &refApp.PersonProfile{
		DisplayName: &dname,
	}

	if err := p.repoman.InitNewRepo(ctx, user.ID, user.Did, profile.NSID(), profile.Key(), profile); err != nil {
		p.log.ErrorContext(ctx, "Error initializing new user repository", "error", err, "did", user.Did)
		return nil, refErr.Repo()
	}

	accessToken, refreshToken, err := p.CreateTokens(ctx, user.ID, user.Did)
	if err != nil {
		return nil, refErr.InternalServer()
	}

	return &refApp.ServerCreateSession_Output{
		Did:          user.Did,
		Handle:       user.Handle.String,
		AccessToken:  accessToken,
		RefreshToken: refreshToken,
		TokenType:    p.jwt.AuthScheme,
	}, nil
}

// CreateTokens method to create the access and refresh tokens and update the signing key cache for a session
func (p *PDS) CreateTokens(ctx context.Context, uid atp.Uid, did string) (string, string, error) {
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
	user *atp.User,
) (*refApp.ServerCreateSession_Output, *refErr.APIError) {
	accessToken, refreshToken, err := p.CreateTokens(ctx, user.ID, user.Did)
	if err != nil {
		return nil, refErr.InternalServer()
	}

	if err := p.km.UpdateKeyCache(ctx, user.Did); err != nil {
		return nil, refErr.InternalServer()
	}

	return &refApp.ServerCreateSession_Output{
		Did:          user.Did,
		Handle:       user.Handle.String,
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
) (*refApp.ServerRefreshSession_Output, atp.Uid, string, *refErr.APIError) {
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

func (p *PDS) DeleteSession(did string) *refErr.APIError {
	p.km.InvalidateKeys(did)

	return nil
}

// DeleteAccount tombstones the DID in the PLC, deletes DB metadata, and deletes CAR files
func (p *PDS) DeleteAccount(ctx context.Context, uid atp.Uid, did string) *refErr.APIError {
	op, err := p.plc.GetLatestOp(ctx, did)
	if err != nil {
		p.log.ErrorContext(ctx, "Error searching for latest operation in PLC log", "error", err)
		return refErr.PLCServer()
	}

	if err := p.plc.TombstoneDID(ctx, did, op.CID); err != nil {
		p.log.ErrorContext(ctx, "Tombstone request to PLC directory failed", "error", err)
		return refErr.PLCServer()
	}

	if err := p.repoman.TakeDownRepo(ctx, uid); err != nil {
		p.log.ErrorContext(ctx, "Failed to delete CAR shards", "error", err)
		return refErr.Repo()
	}

	p.km.InvalidateKeys(did)

	return nil
}

// HandleAtprotoDescribeServer provides server metadata for websocket conusmers
func (p *PDS) HandleAtprotoDescribeServer() *atproto.ServerDescribeServer_Output {
	// TODO: Add some other fields here
	return &atproto.ServerDescribeServer_Output{AvailableUserDomains: []string{p.handleSuffix}}
}
