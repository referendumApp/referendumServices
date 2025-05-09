package service

import (
	"net/http"
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

	pw, err := s.av.ResolveHandle(ctx, &req)
	if err != nil {
		err.WriteResponse(w)
		return
	}

	actor, err := s.pds.CreateActor(ctx, req, pw)
	if err != nil {
		err.WriteResponse(w)
		return
	}

	if cerr := s.av.CreateActorAndPerson(ctx, actor, req.Handle, req.DisplayName); cerr != nil {
		cerr.WriteResponse(w)
		return
	}

	resp, err := s.pds.CreateNewRepo(ctx, actor, req.DisplayName)
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

	actor, err := s.av.AuthenticateUser(ctx, login.Username, login.Password)
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

	resp, uid, did, err := s.pds.RefreshSession(ctx, req.RefreshToken)
	if err != nil {
		err.WriteResponse(w)
		return
	}

	if err := s.av.AuthenticateSession(ctx, uid, did); err != nil {
		err.WriteResponse(w)
		return
	}

	s.encode(ctx, w, http.StatusOK, resp)
}

func (s *Service) handleDeleteSession(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()

	_, did, err := s.getAndValidatePerson(ctx)
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

	uid, did, err := s.getAndValidatePerson(ctx)
	if err != nil {
		err.WriteResponse(w)
		return
	}

	if err := s.pds.DeleteAccount(ctx, uid, did); err != nil {
		err.WriteResponse(w)
		return
	}

	if err := s.av.DeleteAccount(ctx, uid, did); err != nil {
		err.WriteResponse(w)
		return
	}
}

func (s *Service) handleUserProfileUpdate(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()

	var req refApp.PersonUpdateProfile_Input
	if err := s.decodeAndValidate(ctx, w, r.Body, &req); err != nil {
		return
	}

	uid, _, err := s.getAndValidatePerson(ctx)
	if err != nil {
		err.WriteResponse(w)
		return
	}

	if req.DisplayName != nil {
		profile := &refApp.PersonProfile{
			DisplayName: req.DisplayName,
		}

		if _, err := s.pds.UpdateRecord(ctx, uid, profile); err != nil {
			err.WriteResponse(w)
			return
		}
	}

	if err := s.av.UpdateProfile(ctx, uid, &req); err != nil {
		err.WriteResponse(w)
		return
	}
}

func (s *Service) handleGetUserProfile(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()

	uid, _, err := s.getAndValidatePerson(ctx)
	if err != nil {
		err.WriteResponse(w)
		return
	}

	var profile refApp.PersonProfile
	if _, err := s.pds.GetRecord(ctx, uid, &profile); err != nil {
		err.WriteResponse(w)
		return
	}
	// profile, err := s.av.GetProfile(ctx, uid)
	// if err != nil {
	// 	err.WriteResponse(w)
	// 	return
	// }

	s.encode(ctx, w, http.StatusOK, profile)
}

func (s *Service) handleGraphFollow(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()

	var req refApp.GraphFollow_Input
	if err := s.decodeAndValidate(ctx, w, r.Body, &req); err != nil {
		return
	}

	uid, _, err := s.getAndValidatePerson(ctx)
	if err != nil {
		err.WriteResponse(w)
		return
	}

	rec := &refApp.GraphFollow{Subject: req.Did, CreatedAt: time.Now().UTC().Format(util.ISO8601)}
	cc, tid, err := s.pds.CreateRecord(ctx, uid, rec)
	if err != nil {
		err.WriteResponse(w)
		return
	}

	if err := s.av.HandleGraphFollow(ctx, uid, req.Did, cc, tid); err != nil {
		err.WriteResponse(w)
		return
	}
}

func (s *Service) handleGraphFollowers(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()

	uid, _, err := s.getAndValidatePerson(ctx)
	if err != nil {
		err.WriteResponse(w)
		return
	}

	followers, err := s.av.HandleGraphFollowers(ctx, uid)
	if err != nil {
		err.WriteResponse(w)
		return
	}

	s.encode(ctx, w, http.StatusOK, followers)
}

func (s *Service) handleGraphFollowing(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()

	uid, _, err := s.getAndValidatePerson(ctx)
	if err != nil {
		err.WriteResponse(w)
		return
	}

	following, err := s.av.HandleGraphFollowing(ctx, uid)
	if err != nil {
		err.WriteResponse(w)
		return
	}

	s.encode(ctx, w, http.StatusOK, following)
}
