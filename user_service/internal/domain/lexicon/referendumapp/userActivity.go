// Code generated by cmd/lexgen (see Makefile's lexgen); DO NOT EDIT.

package referendumapp

// schema: com.referendumapp.user.activity

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"

	comatproto "github.com/bluesky-social/indigo/api/atproto"
	appbsky "github.com/bluesky-social/indigo/api/bsky"
	"github.com/bluesky-social/indigo/lex/util"
	"github.com/referendumApp/referendumServices/internal/repo"
	cbg "github.com/whyrusleeping/cbor-gen"
)

func init() {
	util.RegisterType("com.referendumapp.user.activity", &UserActivity{})
	util.RegisterType("com.referendumapp.user.activity#replyRef", &UserActivity_ReplyRef{})
}

// RECORDTYPE: UserActivity
type UserActivity struct {
	LexiconTypeID string `json:"$type" cborgen:"$type,const=com.referendumapp.user.activity" validate:"required"`
	// createdAt: Client-declared timestamp when this post was originally created.
	CreatedAt string              `json:"createdAt" cborgen:"createdAt" validate:"required,datetime"`
	Embed     *UserActivity_Embed `json:"embed,omitempty" cborgen:"embed,omitempty" validate:"omitempty"`
	// facets: Annotations of text (mentions, URLs, hashtags, etc)
	Facets []*appbsky.RichtextFacet `json:"facets,omitempty" cborgen:"facets,omitempty" validate:"omitempty"`
	// labels: Self-label values for this post. Effectively content warnings.
	Labels *UserActivity_Labels `json:"labels,omitempty" cborgen:"labels,omitempty" validate:"omitempty"`
	// langs: Indicates human language of post primary text content.
	Langs []string               `json:"langs,omitempty" cborgen:"langs,omitempty" validate:"omitempty,max=3"`
	Reply *UserActivity_ReplyRef `json:"reply,omitempty" cborgen:"reply,omitempty" validate:"omitempty"`
	// text: The primary post content. May be an empty string, if there are embeds.
	Text string `json:"text" cborgen:"text" validate:"required,max=3000"`
}

type UserActivity_Embed struct {
	EmbedImages          *appbsky.EmbedImages
	EmbedVideo           *appbsky.EmbedVideo
	EmbedExternal        *appbsky.EmbedExternal
	EmbedRecord          *appbsky.EmbedRecord
	EmbedRecordWithMedia *appbsky.EmbedRecordWithMedia
}

func (t *UserActivity_Embed) MarshalJSON() ([]byte, error) {
	if t.EmbedImages != nil {
		t.EmbedImages.LexiconTypeID = "app.bsky.embed.images"
		return json.Marshal(t.EmbedImages)
	}
	if t.EmbedVideo != nil {
		t.EmbedVideo.LexiconTypeID = "app.bsky.embed.video"
		return json.Marshal(t.EmbedVideo)
	}
	if t.EmbedExternal != nil {
		t.EmbedExternal.LexiconTypeID = "app.bsky.embed.external"
		return json.Marshal(t.EmbedExternal)
	}
	if t.EmbedRecord != nil {
		t.EmbedRecord.LexiconTypeID = "app.bsky.embed.record"
		return json.Marshal(t.EmbedRecord)
	}
	if t.EmbedRecordWithMedia != nil {
		t.EmbedRecordWithMedia.LexiconTypeID = "app.bsky.embed.recordWithMedia"
		return json.Marshal(t.EmbedRecordWithMedia)
	}
	return nil, fmt.Errorf("cannot marshal empty enum")
}

func (t *UserActivity_Embed) UnmarshalJSON(b []byte) error {
	typ, err := util.TypeExtract(b)
	if err != nil {
		return err
	}

	switch typ {
	case "app.bsky.embed.images":
		t.EmbedImages = new(appbsky.EmbedImages)
		return json.Unmarshal(b, t.EmbedImages)
	case "app.bsky.embed.video":
		t.EmbedVideo = new(appbsky.EmbedVideo)
		return json.Unmarshal(b, t.EmbedVideo)
	case "app.bsky.embed.external":
		t.EmbedExternal = new(appbsky.EmbedExternal)
		return json.Unmarshal(b, t.EmbedExternal)
	case "app.bsky.embed.record":
		t.EmbedRecord = new(appbsky.EmbedRecord)
		return json.Unmarshal(b, t.EmbedRecord)
	case "app.bsky.embed.recordWithMedia":
		t.EmbedRecordWithMedia = new(appbsky.EmbedRecordWithMedia)
		return json.Unmarshal(b, t.EmbedRecordWithMedia)

	default:
		return nil
	}
}

func (t *UserActivity_Embed) MarshalCBOR(w io.Writer) error {

	if t == nil {
		_, err := w.Write(cbg.CborNull)
		return err
	}
	if t.EmbedImages != nil {
		return t.EmbedImages.MarshalCBOR(w)
	}
	if t.EmbedVideo != nil {
		return t.EmbedVideo.MarshalCBOR(w)
	}
	if t.EmbedExternal != nil {
		return t.EmbedExternal.MarshalCBOR(w)
	}
	if t.EmbedRecord != nil {
		return t.EmbedRecord.MarshalCBOR(w)
	}
	if t.EmbedRecordWithMedia != nil {
		return t.EmbedRecordWithMedia.MarshalCBOR(w)
	}
	return fmt.Errorf("cannot cbor marshal empty enum")
}

func (t *UserActivity_Embed) UnmarshalCBOR(r io.Reader) error {
	typ, b, err := util.CborTypeExtractReader(r)
	if err != nil {
		return err
	}

	switch typ {
	case "app.bsky.embed.images":
		t.EmbedImages = new(appbsky.EmbedImages)
		return t.EmbedImages.UnmarshalCBOR(bytes.NewReader(b))
	case "app.bsky.embed.video":
		t.EmbedVideo = new(appbsky.EmbedVideo)
		return t.EmbedVideo.UnmarshalCBOR(bytes.NewReader(b))
	case "app.bsky.embed.external":
		t.EmbedExternal = new(appbsky.EmbedExternal)
		return t.EmbedExternal.UnmarshalCBOR(bytes.NewReader(b))
	case "app.bsky.embed.record":
		t.EmbedRecord = new(appbsky.EmbedRecord)
		return t.EmbedRecord.UnmarshalCBOR(bytes.NewReader(b))
	case "app.bsky.embed.recordWithMedia":
		t.EmbedRecordWithMedia = new(appbsky.EmbedRecordWithMedia)
		return t.EmbedRecordWithMedia.UnmarshalCBOR(bytes.NewReader(b))

	default:
		return nil
	}
}

// Self-label values for this post. Effectively content warnings.
type UserActivity_Labels struct {
	LabelDefs_SelfLabels *comatproto.LabelDefs_SelfLabels
}

func (t *UserActivity_Labels) MarshalJSON() ([]byte, error) {
	if t.LabelDefs_SelfLabels != nil {
		t.LabelDefs_SelfLabels.LexiconTypeID = "com.atproto.label.defs#selfLabels"
		return json.Marshal(t.LabelDefs_SelfLabels)
	}
	return nil, fmt.Errorf("cannot marshal empty enum")
}

func (t *UserActivity_Labels) UnmarshalJSON(b []byte) error {
	typ, err := util.TypeExtract(b)
	if err != nil {
		return err
	}

	switch typ {
	case "com.atproto.label.defs#selfLabels":
		t.LabelDefs_SelfLabels = new(comatproto.LabelDefs_SelfLabels)
		return json.Unmarshal(b, t.LabelDefs_SelfLabels)

	default:
		return nil
	}
}

func (t *UserActivity_Labels) MarshalCBOR(w io.Writer) error {

	if t == nil {
		_, err := w.Write(cbg.CborNull)
		return err
	}
	if t.LabelDefs_SelfLabels != nil {
		return t.LabelDefs_SelfLabels.MarshalCBOR(w)
	}
	return fmt.Errorf("cannot cbor marshal empty enum")
}

func (t *UserActivity_Labels) UnmarshalCBOR(r io.Reader) error {
	typ, b, err := util.CborTypeExtractReader(r)
	if err != nil {
		return err
	}

	switch typ {
	case "com.atproto.label.defs#selfLabels":
		t.LabelDefs_SelfLabels = new(comatproto.LabelDefs_SelfLabels)
		return t.LabelDefs_SelfLabels.UnmarshalCBOR(bytes.NewReader(b))

	default:
		return nil
	}
}

// UserActivity_ReplyRef is a "replyRef" in the com.referendumapp.user.activity schema.
//
// RECORDTYPE: UserActivity_ReplyRef
type UserActivity_ReplyRef struct {
	LexiconTypeID string                    `json:"$type" cborgen:"$type,const=com.referendumapp.user.activity#replyRef" validate:"required"`
	Parent        *comatproto.RepoStrongRef `json:"parent" cborgen:"parent" validate:"required"`
	Root          *comatproto.RepoStrongRef `json:"root" cborgen:"root" validate:"required"`
}

func (t UserActivity) NSID() string {
	return "com.referendumapp.user.activity"
}

func (t UserActivity) Key() string {
	return repo.NextTID()
}
