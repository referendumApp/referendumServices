package repo

import (
	"crypto/rand"
	"encoding/binary"
	"fmt"
	"sync"
	"time"
)

const alpha = "234567abcdefghijklmnopqrstuvwxyz"

func s32encode(i uint64) string {
	var s string
	for i > 0 {
		c := i & 0x1f
		i >>= 5
		s = alpha[c:c+1] + s
	}
	return s
}

func init() {
	var randBytes [8]byte
	_, err := rand.Read(randBytes[:])
	if err != nil {
		panic(fmt.Sprintf("failed to generate secure random clockId: %v", err))
	}

	clockId = binary.BigEndian.Uint64(randBytes[:]) & 0x1f
}

var lastTime uint64
var clockId uint64
var ltLock sync.Mutex

// NextTID time based encoded record key
func NextTID() string {
	// Safe conversion: UnixMicro() for current dates is always positive and well within uint64 range
	t := uint64(time.Now().UnixMicro()) //nolint:gosec

	ltLock.Lock()
	if lastTime >= t {
		t = lastTime + 1
	}

	lastTime = t
	ltLock.Unlock()

	return s32encode(t) + s32encode(clockId)
}
