package service

import (
	"fmt"
	"net/http"
	"regexp"
	"strconv"
	"strings"
	"time"

	refApp "github.com/referendumApp/referendumServices/internal/domain/lexicon/referendumapp"
	refErr "github.com/referendumApp/referendumServices/internal/error"
	"github.com/referendumApp/referendumServices/internal/util"
)

func (s *Service) handleHealth(w http.ResponseWriter, r *http.Request) {
	if err := s.av.HandleHealth(w, r); err != nil {
		err.WriteResponse(w)
		return
	}

	if err := s.pds.HandleHealth(w, r); err != nil {
		err.WriteResponse(w)
		return
	}

	resp := map[string]bool{"healthy": true}

	s.encode(r.Context(), w, http.StatusOK, resp)
}

func (s *Service) handleDescribeServer(w http.ResponseWriter, r *http.Request) {
	resp := s.pds.HandleAtprotoDescribeServer()
	s.encode(r.Context(), w, http.StatusOK, resp)
}

func (s *Service) handleCreateUser(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()

	var req refApp.ServerCreateAccount_Input
	if err := s.decodeAndValidate(ctx, w, r.Body, &req); err != nil {
		return
	}

	err := s.av.ValidateHandle(ctx, req.Handle)
	if err != nil {
		err.WriteResponse(w)
		return
	}

	hashed_pw, err := s.av.ResolveNewUser(ctx, &req)
	if err != nil {
		err.WriteResponse(w)
		return
	}

	var recoveryKey string
	if req.RecoveryKey != nil {
		recoveryKey = *req.RecoveryKey
	}

	actor, err := s.pds.CreateActor(ctx, req.Handle, req.DisplayName, recoveryKey, req.Email, hashed_pw)
	if err != nil {
		err.WriteResponse(w)
		return
	}

	user, cerr := s.av.CreateUser(ctx, actor, req.DisplayName)
	if cerr != nil {
		cerr.WriteResponse(w)
		return
	}

	resp, err := s.pds.CreateNewUserRepo(ctx, actor, user)
	if err != nil {
		err.WriteResponse(w)
		return
	}

	s.encode(ctx, w, http.StatusCreated, resp)
}

func (s *Service) handleCreateLegislator(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()

	var req refApp.ServerCreateLegislator_Input
	if err := s.decodeAndValidate(ctx, w, r.Body, &req); err != nil {
		return
	}

	var handle string
	sanitizedName := strings.ToLower(req.Name)
	sanitizedName = regexp.MustCompile(`[^a-z0-9-]`).ReplaceAllString(sanitizedName, "-")
	sanitizedName = strings.Trim(sanitizedName, "-")
	handle = fmt.Sprintf("%s.referendumapp.com", sanitizedName)
	err := s.av.ValidateHandle(ctx, handle)
	if err != nil {
		handle = fmt.Sprintf("%s-%d.referendumapp.com", sanitizedName, req.LegislatorId)
		err = s.av.ValidateHandle(ctx, handle)
		if err != nil {
			err.WriteResponse(w)
			return
		}
	}

	err = s.av.ResolveNewLegislator(ctx, &req)
	if err != nil {
		err.WriteResponse(w)
		return
	}

	actor, err := s.pds.CreateActor(ctx, handle, req.Name, "", "", "")
	if err != nil {
		err.WriteResponse(w)
		return
	}

	if cerr := s.av.SaveActorAndLegislator(ctx, actor, req.LegislatorId, req.Name); cerr != nil {
		cerr.WriteResponse(w)
		return
	}

	resp, err := s.pds.CreateNewLegislatorRepo(ctx, actor, &req)
	if err != nil {
		err.WriteResponse(w)
		return
	}

	s.encode(ctx, w, http.StatusCreated, resp)
}

func (s *Service) handleCreateSession(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()

	if err := r.ParseForm(); err != nil {
		s.log.ErrorContext(ctx, "Invalid form", "error", err)
		refErr.BadRequest("Faild to parse form data from request").WriteResponse(w)
		return
	}

	login := refApp.ServerCreateSession_Input{
		GrantType: r.Form.Get("grantType"),
		Username:  r.Form.Get("username"),
		Password:  r.Form.Get("password"),
	}

	if err := util.Validate.Struct(login); err != nil {
		apiErr := s.handleValidationErrors(ctx, err)
		apiErr.WriteResponse(w)
		return
	}

	actor, err := s.av.GetAuthenticatedActor(ctx, login.Username, login.Password)
	if err != nil {
		err.WriteResponse(w)
		return
	}

	resp, err := s.pds.CreateSession(ctx, actor)
	if err != nil {
		err.WriteResponse(w)
		return
	}

	s.encode(ctx, w, http.StatusCreated, resp)
}

func (s *Service) handleRefreshSession(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()

	var req refApp.ServerRefreshSession_Input
	if err := s.decodeAndValidate(ctx, w, r.Body, &req); err != nil {
		return
	}

	resp, aid, did, err := s.pds.RefreshSession(ctx, req.RefreshToken)
	if err != nil {
		err.WriteResponse(w)
		return
	}

	if err := s.av.AuthenticateSession(ctx, aid, did); err != nil {
		err.WriteResponse(w)
		return
	}

	s.encode(ctx, w, http.StatusOK, resp)
}

func (s *Service) handleDeleteSession(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()

	_, did, err := s.getAuthenticatedIds(ctx)
	if err != nil {
		err.WriteResponse(w)
		return
	}

	if err := s.pds.DeleteSession(ctx, did); err != nil {
		err.WriteResponse(w)
		return
	}
}

func (s *Service) handleDeleteUser(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()

	aid, did, err := s.getAuthenticatedIds(ctx)
	if err != nil {
		err.WriteResponse(w)
		return
	}

	if err := s.pds.DeleteActor(ctx, aid, did); err != nil {
		err.WriteResponse(w)
		return
	}

	if err := s.av.DeleteActor(ctx, aid, did); err != nil {
		err.WriteResponse(w)
		return
	}

	if err := s.av.DeleteUser(ctx, aid, did); err != nil {
		err.WriteResponse(w)
		return
	}
}

func (s *Service) handleUpdateUserProfile(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()

	var req refApp.UserUpdateProfile_Input
	if err := s.decodeAndValidate(ctx, w, r.Body, &req); err != nil {
		return
	}

	aid, _, err := s.getAuthenticatedIds(ctx)
	if err != nil {
		err.WriteResponse(w)
		return
	}

	if req.DisplayName != nil {
		profile := &refApp.UserProfile{
			DisplayName: req.DisplayName,
		}

		if _, err := s.pds.UpdateRecord(ctx, aid, profile); err != nil {
			err.WriteResponse(w)
			return
		}
	}

	if err := s.av.UpdateUserProfile(ctx, aid, &req); err != nil {
		err.WriteResponse(w)
		return
	}
}

func (s *Service) handleGetUserProfile(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()

	aid, _, err := s.getAuthenticatedIds(ctx)
	if err != nil {
		err.WriteResponse(w)
		return
	}

	var profile refApp.UserProfile
	if _, err := s.pds.GetRecord(ctx, aid, &profile); err != nil {
		err.WriteResponse(w)
		return
	}

	s.encode(ctx, w, http.StatusOK, profile)
}

func (s *Service) handleGetLegislator(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()

	var legislatorId *int64
	legislatorIdStr := r.URL.Query().Get("legislatorId")
	if legislatorIdStr != "" {
		id, err := strconv.ParseInt(legislatorIdStr, 10, 64)
		if err != nil {
			apiErr := refErr.BadRequest("Invalid legislatorId format")
			apiErr.WriteResponse(w)
			return
		}
		legislatorId = &id
	}

	var handle *string
	handleStr := r.URL.Query().Get("handle")
	if handleStr != "" {
		handle = &handleStr
	}

	legislator, err := s.av.GetLegislator(ctx, legislatorId, handle)
	if err != nil {
		err.WriteResponse(w)
		return
	}

	var profile refApp.LegislatorProfile
	_, err = s.pds.GetRecord(ctx, legislator.Aid, &profile)
	if err != nil {
		err.WriteResponse(w)
		return
	}

	s.encode(ctx, w, http.StatusOK, profile)
}

func updateStringIfNotNil(target *string, source *string) {
	if source != nil {
		*target = *source
	}
}

func updateStringPtrIfNotNil(target **string, source *string) {
	if source != nil {
		if *target == nil {
			*target = new(string)
		}
		**target = *source
	}
}

func (s *Service) handleUpdateLegislator(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()

	var req refApp.LegislatorUpdateProfile_Input
	if err := s.decodeAndValidate(ctx, w, r.Body, &req); err != nil {
		return
	}

	var legislator, err = s.av.GetLegislator(ctx, &req.LegislatorId, nil)
	if err != nil {
		err.WriteResponse(w)
		return
	}

	var currentProfile refApp.LegislatorProfile
	if _, err := s.pds.GetRecord(ctx, legislator.Aid, &currentProfile); err != nil {
		err.WriteResponse(w)
		return
	}

	profile := currentProfile
	updateStringIfNotNil(&profile.Name, req.Name)
	updateStringIfNotNil(&profile.District, req.District)
	updateStringIfNotNil(&profile.Party, req.Party)
	updateStringIfNotNil(&profile.Role, req.Role)
	updateStringIfNotNil(&profile.State, req.State)
	updateStringIfNotNil(&profile.Legislature, req.Legislature)
	updateStringPtrIfNotNil(&profile.Phone, req.Phone)
	updateStringPtrIfNotNil(&profile.ImageUrl, req.ImageUrl)
	updateStringPtrIfNotNil(&profile.Address, req.Address)

	if req.Image != nil {
		profile.Image = req.Image
	}

	if _, err := s.pds.UpdateRecord(ctx, legislator.Aid, &profile); err != nil {
		err.WriteResponse(w)
		return
	}

	if err := s.av.UpdateLegislator(ctx, legislator.Aid, &req); err != nil {
		err.WriteResponse(w)
		return
	}

	w.WriteHeader(http.StatusOK)
}

func (s *Service) handleDeleteLegislator(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()

	var legislatorId *int64
	legislatorIdStr := r.URL.Query().Get("legislatorId")
	if legislatorIdStr != "" {
		id, err := strconv.ParseInt(legislatorIdStr, 10, 64)
		if err != nil {
			apiErr := refErr.BadRequest("Invalid legislatorId format")
			apiErr.WriteResponse(w)
			return
		}
		legislatorId = &id
	}

	legislator, apiErr := s.av.GetLegislator(ctx, legislatorId, nil)
	if apiErr != nil {
		apiErr.WriteResponse(w)
		return
	}

	did, err := s.av.GetDidForAid(ctx, legislator.Aid)
	if err != nil {
		err.WriteResponse(w)
		return
	}

	if err := s.pds.DeleteActor(ctx, legislator.Aid, *did); err != nil {
		err.WriteResponse(w)
		return
	}

	if err := s.av.DeleteActor(ctx, legislator.Aid, *did); err != nil {
		err.WriteResponse(w)
		return
	}

	if err := s.av.DeleteLegislator(ctx, legislator.Aid, *did); err != nil {
		err.WriteResponse(w)
		return
	}
}

func (s *Service) handleGraphFollow(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()

	var req refApp.GraphFollow_Input
	if err := s.decodeAndValidate(ctx, w, r.Body, &req); err != nil {
		return
	}

	aid, _, err := s.getAuthenticatedIds(ctx)
	if err != nil {
		err.WriteResponse(w)
		return
	}

	rec := &refApp.GraphFollow{Subject: req.Did, CreatedAt: time.Now().UTC().Format(util.ISO8601)}
	cc, tid, err := s.pds.CreateRecord(ctx, aid, rec)
	if err != nil {
		err.WriteResponse(w)
		return
	}

	if err := s.av.HandleGraphFollow(ctx, aid, req.TargetID, req.TargetCollection, cc, rec.NSID(), tid); err != nil {
		err.WriteResponse(w)
		return
	}
}

func (s *Service) handleGraphUnfollow(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()

	targetID, err := s.getAidURLParam(ctx, "targetID")
	if err != nil {
		err.WriteResponse(w)
		return
	}

	aid, _, err := s.getAuthenticatedIds(ctx)
	if err != nil {
		err.WriteResponse(w)
		return
	}

	collection, rkey, err := s.av.HandleGraphUnfollow(ctx, aid, targetID)
	if err != nil {
		err.WriteResponse(w)
		return
	}

	if err := s.pds.DeleteRecord(ctx, aid, collection, rkey); err != nil {
		err.WriteResponse(w)
		return
	}
}

func (s *Service) handleGraphFollowers(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()

	aid, _, err := s.getAuthenticatedIds(ctx)
	if err != nil {
		err.WriteResponse(w)
		return
	}

	followers, err := s.av.HandleGraphFollowers(ctx, aid)
	if err != nil {
		err.WriteResponse(w)
		return
	}

	s.encode(ctx, w, http.StatusOK, followers)
}

func (s *Service) handleGraphFollowing(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()

	aid, _, err := s.getAuthenticatedIds(ctx)
	if err != nil {
		err.WriteResponse(w)
		return
	}

	following, err := s.av.HandleGraphFollowing(ctx, aid)
	if err != nil {
		err.WriteResponse(w)
		return
	}

	s.encode(ctx, w, http.StatusOK, following)
}

func (s *Service) handleCreateAdmin(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()

	var req refApp.ServerCreateSystemUser_Input
	if err := s.decodeAndValidate(ctx, w, r.Body, &req); err != nil {
		return
	}

	actor, err := s.pds.CreateActor(ctx, req.Handle, *req.DisplayName, "", req.Email, "")
	if err != nil {
		err.WriteResponse(w)
		return
	}

	user, err := s.av.CreateUser(ctx, actor, *req.DisplayName)
	if err != nil {
		err.WriteResponse(w)
		return
	}

	resp, err := s.pds.CreateNewUserRepo(ctx, actor, user)
	if err != nil {
		err.WriteResponse(w)
		return
	}

	adminResp := refApp.ServerCreateSystemUser_Output{
		Did:    resp.Did,
		Handle: resp.Handle,
		ApiKey: *actor.AuthSettings.ApiKey,
	}

	s.encode(ctx, w, http.StatusCreated, adminResp)
}

func (s *Service) handleGraphVote(w http.ResponseWriter, r *http.Request) {}

func (s *Service) handleGraphUnvote(w http.ResponseWriter, r *http.Request) {}

func (s *Service) handleContentFollow(w http.ResponseWriter, r *http.Request) {}

func (s *Service) handleContentUnfollow(w http.ResponseWriter, r *http.Request) {}

func (s *Service) handleContentVote(w http.ResponseWriter, r *http.Request) {}

func (s *Service) handleContentUnvote(w http.ResponseWriter, r *http.Request) {}
