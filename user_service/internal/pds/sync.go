package pds

import (
	"net/http"
	"strings"

	lexutil "github.com/bluesky-social/indigo/lex/util"
	"github.com/gorilla/websocket"

	"github.com/referendumApp/referendumServices/internal/events"
)

func (p *PDS) EventsHandler(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()

	upgrader := websocket.Upgrader{
		ReadBufferSize:  1 << 10,
		WriteBufferSize: 1 << 10,
		// Allow all origins (be cautious in production)
		CheckOrigin: func(r *http.Request) bool {
			return true
		},
	}

	// Upgrade the connection
	conn, err := upgrader.Upgrade(w, r, r.Header)
	if err != nil {
		p.log.ErrorContext(ctx, "Failed to upgrade the connection", "error", err)
		http.Error(w, "Could not upgrade connection", http.StatusBadRequest)
		return
	}

	// did := r.Header.Get("DID")
	// peering, err := p.lookupPeering(ctx, did)
	// if err != nil {
	// 	http.Error(w, "Failed to lookup peering did", http.StatusInternalServerError)
	// 	return
	// }

	ident := getClientIdentifier(r)

	evts, cancel, err := p.events.Subscribe(ctx, ident, func(evt *events.XRPCStreamEvent) bool {
		if !p.enforcePeering {
			return true
		}
		// if peering.ID == 0 {
		// 	return true
		// }

		return true
		// return slices.Contains(evt.PrivRelevantPds, peering.ID)
	}, nil)
	if err != nil {
		p.log.ErrorContext(ctx, "Failed subscribe to the event stream", "error", err)
		http.Error(w, "Internal PDS Error", http.StatusInternalServerError)
		return
	}
	defer cancel()

	header := events.EventHeader{Op: events.EvtKindMessage}
	for evt := range evts {
		wc, err := conn.NextWriter(websocket.BinaryMessage)
		if err != nil {
			p.log.ErrorContext(ctx, "Failed create websocket writer", "error", err)
			http.Error(w, "Internal PDS Error", http.StatusInternalServerError)
			return
		}

		var obj lexutil.CBOR

		switch {
		case evt.Error != nil:
			header.Op = events.EvtKindErrorFrame
			obj = evt.Error
		case evt.RepoCommit != nil:
			header.MsgType = events.Commit
			obj = evt.RepoCommit
		case evt.RepoHandle != nil:
			header.MsgType = events.Handle
			obj = evt.RepoHandle
		case evt.RepoIdentity != nil:
			header.MsgType = events.Identity
			obj = evt.RepoIdentity
		case evt.RepoAccount != nil:
			header.MsgType = events.Account
			obj = evt.RepoAccount
		case evt.RepoInfo != nil:
			header.MsgType = events.Info
			obj = evt.RepoInfo
		case evt.RepoMigrate != nil:
			header.MsgType = events.Migrate
			obj = evt.RepoMigrate
		case evt.RepoTombstone != nil:
			header.MsgType = events.Tombstone
			obj = evt.RepoTombstone
		default:
			p.log.ErrorContext(ctx, "Unrecognized event kind")
			http.Error(w, "Internal PDS Error", http.StatusInternalServerError)
			return
		}

		if err := header.MarshalCBOR(wc); err != nil {
			p.log.ErrorContext(ctx, "Failed to write header", "error", err)
			http.Error(w, "Internal PDS Error", http.StatusInternalServerError)
			return
		}

		if err := obj.MarshalCBOR(wc); err != nil {
			p.log.ErrorContext(ctx, "Failed to write event", "error", err)
			http.Error(w, "Internal PDS Error", http.StatusInternalServerError)
			return
		}

		if err := wc.Close(); err != nil {
			p.log.ErrorContext(ctx, "Failed to flush-close our event write", "error", err)
			http.Error(w, "Internal PDS Error", http.StatusInternalServerError)
			return
		}
	}
}

func getClientIdentifier(r *http.Request) string {
	// Get the real IP address
	ip := r.Header.Get("X-Forwarded-For")
	if ip == "" {
		ip = r.Header.Get("X-Real-IP")
	}
	if ip == "" {
		ip = r.RemoteAddr
	}

	// If there are multiple IPs in X-Forwarded-For, use the first one
	if idx := strings.Index(ip, ","); idx != -1 {
		ip = ip[:idx]
	}

	// Get the user agent
	userAgent := r.UserAgent()

	// Combine them into an identifier
	ident := ip + "-" + userAgent

	return ident
}
