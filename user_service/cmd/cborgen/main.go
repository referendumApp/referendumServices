package main

import (
	cbg "github.com/whyrusleeping/cbor-gen"

	"github.com/referendumApp/referendumServices/internal/domain/lexicon/referendumapp"
	"github.com/referendumApp/referendumServices/internal/plc"
	"github.com/referendumApp/referendumServices/internal/repo"
)

func main() {
	genCfg := cbg.Gen{
		MaxStringLength: 1_000_000,
	}

	if err := genCfg.WriteMapEncodersToFile("internal/plc/cbor_gen.go", "plc", plc.CreateOp{}, plc.Service{}, plc.TombstoneOp{}); err != nil {
		panic(err)
	}

	if err := genCfg.WriteMapEncodersToFile(
		"internal/domain/lexicon/referendumapp/cbor_gen.go",
		"referendumapp",
		referendumapp.PersonProfile{},
		referendumapp.GraphFollow{},
		referendumapp.BillDetail{},
		referendumapp.BillVersion{},
		referendumapp.BillVersion_VersionRef{},
		referendumapp.BillAction{},
		referendumapp.LegislatorProfile{},
		referendumapp.PersonLegislatorFollow{},
		referendumapp.PersonEndorsement{},
		referendumapp.PersonActivity{},
		referendumapp.PersonActivity_ReplyRef{},
		referendumapp.PersonBillFollow{},
		referendumapp.LegislatorVote{},
		referendumapp.LegislatorSponsor{},
	); err != nil {
		panic(err)
	}

	if err := genCfg.WriteMapEncodersToFile("internal/repo/cbor_gen.go", "repo", repo.SignedCommit{}, repo.UnsignedCommit{}); err != nil {
		panic(err)
	}
}
