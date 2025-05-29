//revive:disable:exported
package atp

import (
	"database/sql/driver"
	"encoding/json"
	"fmt"
	"strings"

	"github.com/ipfs/go-cid"
)

type DbCID struct {
	CID cid.Cid
}

func (dbc *DbCID) Scan(v any) error {
	b, ok := v.([]byte)
	if !ok {
		return fmt.Errorf("dbcids must get bytes")
	}

	if len(b) == 0 {
		return nil
	}

	c, err := cid.Cast(b)
	if err != nil {
		return err
	}

	dbc.CID = c
	return nil
}

func (dbc DbCID) Value() (driver.Value, error) {
	if !dbc.CID.Defined() {
		return nil, fmt.Errorf("cannot serialize undefined cid to database")
	}
	return dbc.CID.Bytes(), nil
}

func (dbc DbCID) MarshalJSON() ([]byte, error) {
	return json.Marshal(dbc.CID.String())
}

func (dbc *DbCID) UnmarshalJSON(b []byte) error {
	var s string
	if err := json.Unmarshal(b, &s); err != nil {
		return err
	}

	c, err := cid.Decode(s)
	if err != nil {
		return err
	}

	dbc.CID = c
	return nil
}

type VoteChoice string

const (
	VoteChoiceYes VoteChoice = "YES"
	VoteChoiceNo  VoteChoice = "NO"
)

func (v *VoteChoice) UnmarshalJSON(data []byte) error {
	var s string
	if err := json.Unmarshal(data, &s); err != nil {
		return err
	}

	choice := VoteChoice(strings.ToUpper(s))
	if choice == VoteChoiceYes || choice == VoteChoiceNo {
		return fmt.Errorf("invalid vote choice: %s", s)
	}

	*v = choice
	return nil
}
