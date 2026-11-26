package r2native

// Selected Module paths with a blocking consumerAPI double; no SDK client.
import (
	k "github.com/confluentinc/confluent-kafka-go/v2/kafka"
	"sync/atomic"
	"testing"
	"time"
)

type containmentConsumer struct {
	*positionConsumer
	entered  chan struct{}
	release  chan struct{}
	finished chan struct{}
	calls    atomic.Int32
	stage    string
}

func (c *containmentConsumer) block() {
	c.calls.Add(1)
	close(c.entered)
	<-c.release
	close(c.finished)
}
func (c *containmentConsumer) CommitOffsets(p []k.TopicPartition) ([]k.TopicPartition, error) {
	if c.stage == "commit" {
		c.block()
	}
	return p, nil
}
func (c *containmentConsumer) Close() error {
	if c.stage == "close" {
		c.block()
	}
	return nil
}
func (c *containmentConsumer) Poll(ms int) k.Event {
	if c.stage == "poll" {
		c.block()
		return nil
	}
	return c.positionConsumer.Poll(ms)
}
func containmentWorld(stage string, age int64) (*Module, *handle, *containmentConsumer) {
	m, h, p := positionWorld()
	c := &containmentConsumer{positionConsumer: p, entered: make(chan struct{}), release: make(chan struct{}), finished: make(chan struct{}), stage: stage}
	h.c = c
	h.commitAllowed = true
	topic := h.topic
	h.last = &k.Message{TopicPartition: k.TopicPartition{Topic: &topic, Partition: 0, Offset: 7}}
	m.anchor = age
	return m, h, c
}
func awaitLocal(t *testing.T, ch <-chan struct{}) {
	t.Helper()
	select {
	case <-ch:
	case <-time.After(2 * time.Second):
		t.Fatal("local fake did not settle")
	}
}
func TestSelectedCommitTimeoutRetainsLateOffsetUncertainty(t *testing.T) {
	m, h, c := containmentWorld("commit", 269800)
	released := false
	t.Cleanup(func() {
		if !released {
			close(c.release)
		}
		awaitLocal(t, c.finished)
	})
	r := m.Commit(1)
	awaitLocal(t, c.entered)
	if r["ok"] != false || r["category"] != "timeout" || !h.quarantined || !m.faulted || h.last == nil {
		t.Fatal("commit uncertainty lost", r)
	}
	if m.Commit(1)["ok"] != false || m.Consume(1)["ok"] != false || m.Close(1)["ok"] != false || m.OpenProducer("kaas-sbx-a-producer", h.topic)["ok"] != false {
		t.Fatal("work admitted after quarantine")
	}
	if c.calls.Load() != 1 {
		t.Fatal("commit retried")
	}
	close(c.release)
	released = true
	awaitLocal(t, c.finished)
	if !h.quarantined || !m.faulted || h.last == nil {
		t.Fatal("late commit cleared uncertainty")
	}
	// Fake SDK returned next offset8, but caller-visible last stays unresolved.
}
func TestSelectedCloseTimeoutRetainsHandleAndQuarantine(t *testing.T) {
	m, h, c := containmentWorld("close", 299800)
	r := m.Close(1)
	awaitLocal(t, c.entered)
	close(c.release)
	awaitLocal(t, c.finished)
	if r["ok"] != false || r["category"] != "timeout" || !h.quarantined || !m.faulted || m.handles[1] != h {
		t.Fatal("late close cleared uncertainty", r)
	}
	if m.Close(1)["ok"] != false || c.calls.Load() != 1 {
		t.Fatal("concurrent close admitted")
	}
}
func TestSelectedExpiredDeadlinesPreventSDKAdmission(t *testing.T) {
	m, _, c := containmentWorld("commit", 270001)
	if m.Commit(1)["ok"] != false || m.Consume(1)["ok"] != false || c.calls.Load() != 0 {
		t.Fatal("expired mutation admitted")
	}
	m, h, c := containmentWorld("close", 300001)
	if m.Close(1)["ok"] != false || c.calls.Load() != 0 || !h.quarantined {
		t.Fatal("expired close admitted")
	}
}
func TestBlockingPollRequiresExternalContainmentRatherThanClaimingCancellation(t *testing.T) {
	m, h, c := containmentWorld("poll", 0)
	h.last = nil
	done := make(chan Result, 1)
	go func() { done <- m.positionWithin(1, 5*time.Millisecond) }()
	awaitLocal(t, c.entered)
	// Deliberately violate the SDK Poll timeout contract: facade cannot preempt it.
	time.Sleep(20 * time.Millisecond)
	select {
	case <-done:
		close(c.release)
		t.Fatal("falsely claimed cancellation")
	default:
	}
	close(c.release)
	awaitLocal(t, c.finished)
	select {
	case r := <-done:
		if r["ok"] != false {
			t.Fatal("stalled poll accepted")
		}
	case <-time.After(time.Second):
		t.Fatal("local poll did not return")
	}
}
