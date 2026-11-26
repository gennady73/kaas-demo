package r2native

import (
	"encoding/json"
	"errors"
	"fmt"
	k "github.com/confluentinc/confluent-kafka-go/v2/kafka"
	"strings"
	"testing"
	"time"
)

// No SDK Producer, Consumer or AdminClient is constructed by these fakes.
type positionConsumer struct {
	events    []k.Event
	assigned  []k.TopicPartition
	positions []k.TopicPartition
	commits   int
}

func (c *positionConsumer) Poll(int) k.Event {
	if len(c.events) > 0 {
		e := c.events[0]
		c.events = c.events[1:]
		return e
	}
	time.Sleep(time.Millisecond)
	return nil
}
func (c *positionConsumer) Assignment() ([]k.TopicPartition, error) { return c.assigned, nil }
func (c *positionConsumer) Position([]k.TopicPartition) ([]k.TopicPartition, error) {
	return c.positions, nil
}
func (c *positionConsumer) CommitOffsets([]k.TopicPartition) ([]k.TopicPartition, error) {
	c.commits++
	panic("position must never commit")
}
func (c *positionConsumer) Close() error { return nil }
func positionWorld(events ...k.Event) (*Module, *handle, *positionConsumer) {
	topic := "kaas-sbx-a-events"
	part := k.TopicPartition{Topic: &topic, Partition: 0, Offset: k.OffsetInvalid}
	c := &positionConsumer{events: events, assigned: []k.TopicPartition{part}, positions: []k.TopicPartition{part}}
	h := &handle{c: c, topic: topic, joined: true}
	m := &Module{started: true, born: time.Now(), handles: map[int]*handle{1: h}}
	return m, h, c
}
func eof(topic string, partition int32, offset k.Offset) k.Event {
	return k.PartitionEOF(k.TopicPartition{Topic: &topic, Partition: partition, Offset: offset})
}

func TestInitialPositionUsesBrokerEOFWithoutMessagesOrCommits(t *testing.T) {
	for _, offset := range []k.Offset{0, 7} {
		m, h, c := positionWorld(eof("kaas-sbx-a-events", 0, offset))
		r := m.positionWithin(1, 20*time.Millisecond)
		if r["ok"] != true || r["position"] != int64(offset) || h.last != nil || c.commits != 0 {
			t.Fatal("EOF position not established without mutation", r)
		}
	}
}
func TestInitialPositionNeverGuessesZeroOrUsesStaleEOF(t *testing.T) {
	m, h, c := positionWorld()
	r := m.positionWithin(1, 5*time.Millisecond)
	if r["ok"] != false || r["category"] != "timeout" || c.commits != 0 {
		t.Fatal("silence became position")
	}
	topic := "kaas-sbx-a-events"
	h.eof = &k.TopicPartition{Topic: &topic, Partition: 0, Offset: 0}
	h.resetAssignmentEvidence()
	h.joined = true
	if m.positionWithin(1, 5*time.Millisecond)["ok"] != false {
		t.Fatal("revoked EOF reused")
	}
}
func TestInitialPositionRejectsWrongEOFAssignmentAndSDKError(t *testing.T) {
	for _, event := range []k.Event{eof("kaas-sbx-b-events", 0, 0), eof("kaas-sbx-a-events", 1, 0), eof("kaas-sbx-a-events", 0, k.OffsetInvalid)} {
		m, _, _ := positionWorld(event)
		if m.positionWithin(1, 10*time.Millisecond)["ok"] != false {
			t.Fatal("foreign/invalid EOF accepted")
		}
	}
	m, _, c := positionWorld(eof("kaas-sbx-a-events", 0, 0))
	wrong := "kaas-sbx-b-events"
	c.assigned[0].Topic = &wrong
	if m.positionWithin(1, 10*time.Millisecond)["ok"] != false {
		t.Fatal("foreign assignment accepted")
	}
	m, _, c = positionWorld(eof("kaas-sbx-a-events", 0, 0))
	c.positions[0].Error = k.NewError(k.ErrGroupAuthorizationFailed, "PASSWORD_CANARY", false)
	r := m.positionWithin(1, 10*time.Millisecond)
	raw, _ := json.Marshal(r)
	if r["category"] != "group_authorization_denied" || strings.Contains(string(raw), "CANARY") {
		t.Fatal("SDK error bypassed or leaked")
	}
}
func TestInitialPositionRequiresCurrentAssignmentAndRejectsBacklog(t *testing.T) {
	m, h, _ := positionWorld(eof("kaas-sbx-a-events", 0, 0))
	h.joined = false
	if m.positionWithin(1, 5*time.Millisecond)["ok"] != false {
		t.Fatal("EOF before join accepted")
	}
	topic := "kaas-sbx-a-events"
	m, _, _ = positionWorld(&k.Message{TopicPartition: k.TopicPartition{Topic: &topic, Partition: 0, Offset: 0}, Value: []byte("PASSWORD_CANARY")})
	r := m.positionWithin(1, 10*time.Millisecond)
	raw, _ := json.Marshal(r)
	if r["ok"] != false || strings.Contains(string(raw), "CANARY") {
		t.Fatal("initial backlog accepted/leaked")
	}
}
func TestEOFIsNotAnAuthorizationDenial(t *testing.T) {
	m, _, c := positionWorld(eof("kaas-sbx-a-events", 0, 0))
	r := m.Consume(1)
	if r["ok"] != true || len(r["messages"].([]interface{})) != 0 || r["category"] != nil || c.commits != 0 {
		t.Fatal("EOF became denial")
	}
}
func TestNormalSDKPositionStillWorks(t *testing.T) {
	m, _, c := positionWorld()
	c.positions[0].Offset = 4
	r := m.positionWithin(1, 5*time.Millisecond)
	if r["ok"] != true || r["position"] != int64(4) {
		t.Fatal("normal SDK position changed", r)
	}
}

// Mirrors event.go -> setupTopicPartitionFromCrktpar: a normal EOF event
// can carry its typed partition-level EOF sentinel in TopicPartition.Error.
func TestSDKShapedPartitionEOFSentinelEstablishesInitialPosition(t *testing.T) {
	for _, offset := range []k.Offset{0, 7} {
		for _, wrapped := range []bool{false, true} {
			topic := "kaas-sbx-a-events"
			var err error = k.NewError(k.ErrPartitionEOF, "SYNTHETIC_EOF_CANARY", false)
			if wrapped {
				err = fmt.Errorf("SYNTHETIC_WRAPPER: %w", err)
			}
			m, h, c := positionWorld(k.PartitionEOF(k.TopicPartition{Topic: &topic, Partition: 0, Offset: offset, Error: err}))
			r := m.positionWithin(1, 20*time.Millisecond)
			if r["ok"] != true || r["position"] != int64(offset) || c.commits != 0 || h.eof == nil || h.eof.Error != nil {
				t.Fatal("normal SDK EOF rejected", r)
			}
			raw, _ := json.Marshal(r)
			if strings.Contains(string(raw), "CANARY") {
				t.Fatal("native error text escaped")
			}
		}
	}
}
func TestEOFSentinelNormalizationRejectsOtherErrorsFatalAndTextSpoofs(t *testing.T) {
	for _, err := range []error{errors.New("Broker: No more messages"), k.NewError(k.ErrTopicAuthorizationFailed, "CANARY", false), k.NewError(k.ErrGroupAuthorizationFailed, "CANARY", false), k.NewError(k.ErrTransport, "CANARY", false), k.NewError(k.ErrPartitionEOF, "CANARY", true)} {
		topic := "kaas-sbx-a-events"
		m, _, c := positionWorld(k.PartitionEOF(k.TopicPartition{Topic: &topic, Partition: 0, Offset: 0, Error: err}))
		r := m.positionWithin(1, 10*time.Millisecond)
		if r["ok"] != false || c.commits != 0 {
			t.Fatal("non-normal EOF error accepted")
		}
	}
}
func TestStandaloneEOFErrorIsNeverConvertedIntoPositionOrDenial(t *testing.T) {
	m, _, c := positionWorld(k.NewError(k.ErrPartitionEOF, "CANARY", false))
	r := m.positionWithin(1, 10*time.Millisecond)
	if r["ok"] != false || r["category"] != "unknown" || c.commits != 0 {
		t.Fatal("non-event EOF error normalized", r)
	}
}
func TestSDKShapedEOFPreservesAssignmentGuards(t *testing.T) {
	for _, part := range []int32{1, -1} {
		topic := "kaas-sbx-a-events"
		_, valid := validatedEOF(k.PartitionEOF(k.TopicPartition{Topic: &topic, Partition: part, Offset: 0, Error: k.NewError(k.ErrPartitionEOF, "", false)}), topic)
		if valid {
			t.Fatal("wrong partition accepted")
		}
	}
	topic := "kaas-sbx-b-events"
	if _, valid := validatedEOF(k.PartitionEOF(k.TopicPartition{Topic: &topic, Partition: 0, Offset: 0, Error: k.NewError(k.ErrPartitionEOF, "", false)}), "kaas-sbx-a-events"); valid {
		t.Fatal("wrong topic accepted")
	}
	topic = "kaas-sbx-a-events"
	if _, valid := validatedEOF(k.PartitionEOF(k.TopicPartition{Topic: &topic, Partition: 0, Offset: k.OffsetInvalid, Error: k.NewError(k.ErrPartitionEOF, "", false)}), topic); valid {
		t.Fatal("negative offset accepted")
	}
}
