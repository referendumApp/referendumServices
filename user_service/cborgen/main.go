package main

import (
	cbg "github.com/whyrusleeping/cbor-gen"

	"github.com/referendumApp/referendumServices/internal/plc"
)

func main() {
	genCfg := cbg.Gen{
		MaxStringLength: 1_000_000,
	}

	if err := genCfg.WriteMapEncodersToFile("internal/plc/cbor_gen.go", "plc", plc.CreateOp{}, plc.Service{}); err != nil {
		panic(err)
	}
}
