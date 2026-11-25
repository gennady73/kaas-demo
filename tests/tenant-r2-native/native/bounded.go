package r2native

import (
	"context"
	"time"
)

// Bounds facade waiting, NOT SDK execution. On timeout the caller quarantines
// the handle and latches the module against new mutations. A late commit can
// still finish; its outcome remains uncertain until outside observation.
func boundedResult(wait time.Duration, stage string, work func() Result) (Result, bool) {
	if wait <= 0 {
		return failure(context.DeadlineExceeded, stage), true
	}
	started := time.Now()
	done := make(chan Result, 1)
	go func() {
		defer func() {
			if recover() != nil {
				done <- bad(stage)
			}
		}()
		done <- work()
	}()
	timer := time.NewTimer(wait)
	defer timer.Stop()
	select {
	case result := <-done:
		if time.Since(started) > wait {
			return failure(context.DeadlineExceeded, stage), true
		}
		return result, false
	case <-timer.C:
		return failure(context.DeadlineExceeded, stage), true
	}
}
func (m *Module) waitLimit(limit time.Duration) time.Duration {
	remaining := time.Duration(limit.Milliseconds()-m.Now()) * time.Millisecond
	if remaining > 6*time.Second {
		return 6 * time.Second
	}
	return remaining
}

func (m *Module) boundedHandle(h *handle, wait time.Duration, stage string, work func() Result) Result {
	result, timedOut := boundedResult(wait, stage, work)
	if timedOut {
		h.quarantined = true
		m.faulted = true
	}
	return result
}
