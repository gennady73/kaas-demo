// Separate xk6 module: it does not alter k6/x/kafka or its existing clients.
package r2native

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"errors"
	"io"
	"os"
	"strings"
	"time"

	k "github.com/confluentinc/confluent-kafka-go/v2/kafka"
	"go.k6.io/k6/js/modules"
)

func init() { modules.Register("k6/x/kaasr2", new(Root)) }

type Root struct{}
type Module struct {
	born      time.Time
	anchor    int64
	started   bool
	faulted   bool
	binarySHA string
	next      int
	handles   map[int]*handle
	sent      map[string]bool
}

// Narrow SDK seam lets offline regressions exercise polling without clients.
type consumerAPI interface {
	Poll(int) k.Event
	Assignment() ([]k.TopicPartition, error)
	Position([]k.TopicPartition) ([]k.TopicPartition, error)
	CommitOffsets([]k.TopicPartition) ([]k.TopicPartition, error)
	Close() error
}

type handle struct {
	p                 *k.Producer
	c                 consumerAPI
	topic, group      string
	last              *k.Message
	eof               *k.TopicPartition
	joined, forbidden bool
	commitAllowed     bool
	quarantined       bool
}

func (*Root) NewModuleInstance(modules.VU) modules.Instance {
	return &Module{born: time.Now(), handles: map[int]*handle{}, sent: map[string]bool{}}
}
func (m *Module) Exports() modules.Exports { return modules.Exports{Default: m} }

type Result map[string]interface{}

func ok(fields Result) Result {
	if fields == nil {
		fields = Result{}
	}
	fields["ok"] = true
	return fields
}
func failure(err error, stage string) Result {
	category, code := "unknown", 0
	var e k.Error
	if errors.As(err, &e) {
		code = int(e.Code())
		switch e.Code() {
		case k.ErrTopicAuthorizationFailed:
			category = "topic_authorization_denied"
		case k.ErrGroupAuthorizationFailed:
			category = "group_authorization_denied"
		case k.ErrClusterAuthorizationFailed:
			category = "cluster_authorization_denied"
		case k.ErrSaslAuthenticationFailed, k.ErrAuthentication:
			category = "authentication_failed"
		case k.ErrSsl:
			category = "tls_failed"
		case k.ErrTransport, k.ErrAllBrokersDown:
			category = "network_failed"
		case k.ErrTimedOut, k.ErrMsgTimedOut:
			category = "timeout"
		}
	}
	if errors.Is(err, context.DeadlineExceeded) {
		category = "timeout"
	}
	// Never return Error(), nested causes, client configuration or native log text.
	return Result{"ok": false, "mapping_id": "KAAS_R2_CONFLUENT_2_14_V1", "category": category, "stage": stage, "native_code": code}
}
func bad(stage string) Result { return failure(nil, stage) }
func tenant(name string) string {
	for _, t := range []string{"kaas-sbx-a", "kaas-sbx-b"} {
		if name == t+"-producer" || name == t+"-consumer" {
			return t
		}
	}
	return ""
}
func topicOK(topic string) bool {
	return topic == "kaas-sbx-a-events" || topic == "kaas-sbx-a-audit" || topic == "kaas-sbx-b-events" || topic == "kaas-sbx-b-audit"
}

// Canonical fixture observation is distinct from a negative client target.
// This is a harness binding, not an additional Kafka ACL policy.
func observationOK(topic, group string) bool {
	return topicOK(topic) && groupOK(group) && topic == strings.TrimSuffix(group, "-group")
}
func groupOK(group string) bool {
	return strings.HasSuffix(group, "-group") && topicOK(strings.TrimSuffix(group, "-group"))
}
func config(principal, password string) (k.ConfigMap, error) {
	if tenant(principal) == "" || password == "" || strings.ContainsAny(password, "\r\n\x00") {
		return nil, errors.New("binding")
	}
	return k.ConfigMap{
		"bootstrap.servers": "kaas-dev-kafka-bootstrap.kaas-kafka.svc:9093",
		"security.protocol": "SASL_SSL", "sasl.mechanism": "SCRAM-SHA-512", "sasl.username": principal, "sasl.password": password,
		"ssl.ca.location": "/credentials/cluster-ca/ca.crt", "enable.ssl.certificate.verification": true, "ssl.endpoint.identification.algorithm": "https",
		"allow.auto.create.topics": false, "socket.timeout.ms": 2000, "socket.connection.setup.timeout.ms": 2000,
		"api.version.request.timeout.ms": 2000, "log_level": 0,
	}, nil
}
func loadConfig(principal string) (k.ConfigMap, error) {
	if tenant(principal) == "" {
		return nil, errors.New("binding")
	}
	password, err := os.ReadFile("/credentials/" + principal + "/password")
	if err != nil {
		return nil, errors.New("credential")
	}
	return config(principal, string(password))
}
func producerConfig(c k.ConfigMap) k.ConfigMap {
	// One identical path for positive controls and all negative writes. Explicit
	// non-idempotence avoids consumer-role tests failing first at IdempotentWrite.
	c["enable.idempotence"] = false
	c["message.send.max.retries"] = 0
	c["acks"] = "all"
	c["max.in.flight.requests.per.connection"] = 1
	c["message.timeout.ms"] = 5000
	c["request.timeout.ms"] = 2000
	c["message.max.bytes"] = 3145728
	c["compression.type"] = "none"
	c["queue.buffering.max.messages"] = 1
	c["queue.buffering.max.kbytes"] = 4096
	return c
}
func consumerConfig(c k.ConfigMap, group string) k.ConfigMap {
	c["group.id"] = group
	c["enable.auto.commit"] = false
	c["enable.auto.offset.store"] = false
	c["enable.partition.eof"] = true
	c["auto.offset.reset"] = "earliest"
	c["fetch.message.max.bytes"] = 4194304
	c["fetch.max.bytes"] = 4194304
	c["fetch.wait.max.ms"] = 250
	c["session.timeout.ms"] = 6000
	c["heartbeat.interval.ms"] = 1000
	c["group.protocol"] = "classic"
	c["go.application.rebalance.enable"] = true
	return c
}
func (m *Module) Start(jobStartUnixMs int64) Result {
	age := time.Now().UnixMilli() - jobStartUnixMs
	if m.started || age < 0 || age > 45000 {
		return bad("startup")
	}
	if err := validateInputs(os.ReadFile, time.Now()); err != nil {
		return bad("startup")
	}
	age = time.Now().UnixMilli() - jobStartUnixMs
	if age < 0 || age > 45000 {
		return bad("startup")
	}
	m.anchor = age
	m.born = time.Now()
	m.started = true
	if m.Now() > 45000 {
		return bad("startup")
	}
	return m.Identity()
}
func (m *Module) Identity() Result {
	if m.binarySHA != "" {
		return ok(Result{"mapping_id": "KAAS_R2_CONFLUENT_2_14_V1", "native_version": nativeVersion(), "binary_sha256": m.binarySHA})
	}
	binary, err := os.Executable()
	if err != nil {
		return bad("startup")
	}
	file, err := os.Open(binary)
	if err != nil {
		return bad("startup")
	}
	defer file.Close()
	hash := sha256.New()
	if _, err = io.Copy(hash, file); err != nil {
		return bad("startup")
	}
	m.binarySHA = hex.EncodeToString(hash.Sum(nil))
	return ok(Result{"mapping_id": "KAAS_R2_CONFLUENT_2_14_V1", "native_version": nativeVersion(), "binary_sha256": m.binarySHA})
}
func nativeVersion() string  { _, v := k.LibraryVersion(); return v }
func (m *Module) Now() int64 { return m.anchor + time.Since(m.born).Milliseconds() }
func (m *Module) live() bool { return m.started && !m.faulted && m.Now() < 270000 }
func (m *Module) OpenProducer(principal, topic string) Result {
	if !m.live() || !topicOK(topic) {
		return bad("produce")
	}
	cfg, err := loadConfig(principal)
	if err != nil {
		return failure(err, "produce")
	}
	p, err := k.NewProducer(ptr(producerConfig(cfg)))
	if err != nil {
		return failure(err, "produce")
	}
	m.next++
	m.handles[m.next] = &handle{p: p, topic: topic}
	return ok(Result{"handle": m.next})
}
func ptr(c k.ConfigMap) *k.ConfigMap { return &c }
func (m *Module) OpenConsumer(principal, topic, group string) Result {
	if !m.live() || !topicOK(topic) || !groupOK(group) || !strings.HasSuffix(principal, "-consumer") {
		return bad("consume")
	}
	cfg, err := loadConfig(principal)
	if err != nil {
		return failure(err, "consume")
	}
	c, err := k.NewConsumer(ptr(consumerConfig(cfg, group)))
	if err != nil {
		return failure(err, "consume")
	}
	h := &handle{c: c, topic: topic, group: group, commitAllowed: group == topic+"-group" && strings.HasPrefix(topic, tenant(principal)+"-")}
	err = c.SubscribeTopics([]string{topic}, func(c *k.Consumer, e k.Event) error {
		switch v := e.(type) {
		case k.AssignedPartitions:
			h.resetAssignmentEvidence()
			h.joined = true
			for _, p := range v.Partitions {
				if p.Topic == nil || *p.Topic != topic || p.Partition != 0 {
					h.forbidden = true
				}
			}
			// A cross-group assignment is itself unexpected access, even without data.
			if !strings.HasPrefix(group, tenant(principal)+"-") || !strings.HasPrefix(topic, tenant(principal)+"-") {
				h.forbidden = true
			}
			return c.Assign(v.Partitions)
		case k.RevokedPartitions:
			h.resetAssignmentEvidence()
			return c.Unassign()
		}
		return nil
	})
	if err != nil {
		c.Close()
		return failure(err, "consume")
	}
	m.next++
	m.handles[m.next] = h
	return ok(Result{"handle": m.next})
}
func (m *Module) Produce(id int, key, value string) Result {
	h := m.handles[id]
	if !m.live() || h == nil || h.p == nil || len(value) != 1000 || len(key) > 256 || m.sent[key] || len(m.sent) >= 20 {
		return bad("produce")
	}
	m.sent[key] = true // Never retry this application ID, including failed enqueue.
	ch := make(chan k.Event, 1)
	err := h.p.Produce(&k.Message{TopicPartition: k.TopicPartition{Topic: &h.topic, Partition: 0}, Key: []byte(key), Value: []byte(value)}, ch)
	if err != nil {
		return failure(err, "produce")
	}
	timer := time.NewTimer(6 * time.Second)
	defer timer.Stop()
	select {
	case event := <-ch:
		msg, valid := event.(*k.Message)
		if !valid {
			return bad("produce")
		}
		if msg.TopicPartition.Error != nil {
			return failure(msg.TopicPartition.Error, "produce")
		}
		if msg.TopicPartition.Topic == nil || *msg.TopicPartition.Topic != h.topic || msg.TopicPartition.Partition != 0 || msg.TopicPartition.Offset < 0 {
			return bad("produce")
		}
		return ok(nil) // ACK only from a successful delivery report, never enqueue.
	case <-timer.C:
		return failure(context.DeadlineExceeded, "produce")
	}
}

// The SDK builds PartitionEOF from a partition-level error event. Its normal
// ErrPartitionEOF sentinel is position evidence here, never an ACL denial.
// Do not normalize arbitrary errors or an ErrPartitionEOF outside this type.
func validatedEOF(event k.PartitionEOF, topic string) (k.TopicPartition, bool) {
	part := k.TopicPartition(event)
	if part.Topic == nil || *part.Topic != topic || part.Partition != 0 || part.Offset < 0 {
		return k.TopicPartition{}, false
	}
	if part.Error != nil {
		var nativeError k.Error
		if !errors.As(part.Error, &nativeError) || nativeError.Code() != k.ErrPartitionEOF || nativeError.IsFatal() {
			return k.TopicPartition{}, false
		}
	}
	part.Error = nil // Retain only validated position evidence in the handle.
	return part, true
}

func (m *Module) poll(h *handle, milliseconds int) Result {
	deadline := time.Now().Add(time.Duration(milliseconds) * time.Millisecond)
	for time.Now().Before(deadline) && m.live() {
		event := h.c.Poll(50)
		if h.forbidden {
			return ok(Result{"unexpected_access": true, "messages": []interface{}{}})
		}
		switch v := event.(type) {
		case k.PartitionEOF:
			part, valid := validatedEOF(v, h.topic)
			if !valid {
				return bad("consume")
			}
			h.eof = &part
			return ok(Result{"messages": []interface{}{}}) // EOF is position evidence, never an ACL denial.
		case *k.Message:
			if v.TopicPartition.Error != nil {
				return failure(v.TopicPartition.Error, "consume")
			}
			if v.TopicPartition.Topic == nil || *v.TopicPartition.Topic != h.topic || v.TopicPartition.Partition != 0 || v.TopicPartition.Offset < 0 {
				return bad("consume")
			}
			h.eof = nil
			h.last = v
			return ok(Result{"messages": []Result{{"topic": *v.TopicPartition.Topic, "partition": v.TopicPartition.Partition, "offset": int64(v.TopicPartition.Offset), "key": string(v.Key), "value": string(v.Value)}}})
		case k.Error:
			return failure(v, "consume")
		}
	}
	return ok(Result{"messages": []interface{}{}}) // Empty is never a denial.
}
func (m *Module) Consume(id int) Result {
	h := m.handles[id]
	if h == nil || h.c == nil || !m.live() {
		return bad("consume")
	}
	return m.poll(h, 2000)
}
func (h *handle) resetAssignmentEvidence() { h.joined = false; h.eof = nil }

func (m *Module) Position(id int) Result { return m.positionWithin(id, 6*time.Second) }

func (m *Module) positionWithin(id int, wait time.Duration) Result {
	h := m.handles[id]
	if h == nil || h.c == nil || !m.live() {
		return bad("consume")
	}
	deadline := time.Now().Add(wait)
	for time.Now().Before(deadline) && m.live() {
		pollMs := int(time.Until(deadline).Milliseconds())
		if pollMs > 100 {
			pollMs = 100
		}
		if pollMs < 1 {
			break
		}
		r := m.poll(h, pollMs)
		if r["ok"] != true {
			return r
		}
		if h.last != nil || h.forbidden {
			return bad("consume")
		}
		assignments, err := h.c.Assignment()
		if err != nil {
			return failure(err, "consume")
		}
		if len(assignments) != 1 || !h.joined {
			continue
		}
		if assignments[0].Topic == nil || *assignments[0].Topic != h.topic || assignments[0].Partition != 0 || assignments[0].Error != nil {
			return bad("consume")
		}
		pos, err := h.c.Position(assignments)
		if err != nil {
			return failure(err, "consume")
		}
		if len(pos) != 1 || pos[0].Topic == nil || *pos[0].Topic != h.topic || pos[0].Partition != 0 {
			return bad("consume")
		}
		if pos[0].Error != nil {
			return failure(pos[0].Error, "consume")
		}
		if pos[0].Offset >= 0 {
			return ok(Result{"position": int64(pos[0].Offset)})
		}
		// librdkafka 2.14 Position is INVALID before the first application message.
		// A broker EOF for this still-assigned partition proves its read head
		// without seeding data, seeking, committing or guessing zero.
		if pos[0].Offset == k.OffsetInvalid && h.eof != nil && h.eof.Topic != nil && *h.eof.Topic == h.topic && h.eof.Partition == 0 {
			return ok(Result{"position": int64(h.eof.Offset)})
		}
	}
	return failure(context.DeadlineExceeded, "consume")
}
func (m *Module) ProbeState(id int) Result {
	h := m.handles[id]
	if h == nil || h.quarantined || m.faulted {
		return bad("consume")
	}
	return ok(Result{"broker_confirmed": h.joined, "group_joined": h.joined, "forbidden_assignment": h.forbidden})
}
func (m *Module) Commit(id int) Result {
	h := m.handles[id]
	if !m.live() || h == nil || h.c == nil || h.last == nil || h.forbidden || !h.commitAllowed {
		return bad("commit")
	}
	// Commit exactly the verified record's next offset; no native auto-store.
	p := h.last.TopicPartition
	p.Offset++
	result := m.boundedHandle(h, m.waitLimit(270000*time.Millisecond), "commit", func() Result {
		offsets, err := h.c.CommitOffsets([]k.TopicPartition{p})
		if err != nil {
			return failure(err, "commit")
		}
		if len(offsets) != 1 || offsets[0].Error != nil || offsets[0].Topic == nil || *offsets[0].Topic != h.topic || offsets[0].Partition != p.Partition || offsets[0].Offset != p.Offset {
			return bad("commit")
		}
		return ok(nil)
	})
	if result["ok"] == true {
		h.last = nil
	}
	return result
}
func (m *Module) Close(id int) Result {
	h := m.handles[id]
	if h == nil || h.quarantined {
		return bad("close")
	}
	result := m.boundedHandle(h, m.waitLimit(300000*time.Millisecond), "close", func() Result {
		if h.p != nil {
			h.p.Close()
		}
		if h.c != nil {
			if err := h.c.Close(); err != nil {
				return failure(err, "close")
			}
		}
		return ok(nil)
	})
	if result["ok"] == true {
		delete(m.handles, id)
	}
	return result
}

// Metadata only: no subscription, poll, assignment, offset alteration or payload.
// Group and topic are observed with their OWN permitted identities, never the
// principal under negative test. Fixture ownership is a separate reviewed input.
func (m *Module) Snapshot(topic, group string) Result {
	if !m.live() || !observationOK(topic, group) {
		return bad("observe")
	}
	wait := 8 * time.Second
	if remaining := time.Duration(270000-m.Now()) * time.Millisecond; remaining < wait {
		wait = remaining
	}
	ctx, cancel := context.WithTimeout(context.Background(), wait)
	defer cancel()
	result, timedOut := boundedResult(wait, "observe", func() Result { return snapshot(ctx, topic, group) })
	if timedOut {
		m.faulted = true
	}
	return result
}
func snapshot(ctx context.Context, topic, group string) Result {
	if !observationOK(topic, group) {
		return bad("observe")
	}
	groupTenant := strings.TrimSuffix(strings.TrimSuffix(strings.TrimSuffix(group, "-group"), "-events"), "-audit")
	topicTenant := strings.TrimSuffix(strings.TrimSuffix(topic, "-events"), "-audit")
	gc, err := loadConfig(groupTenant + "-consumer")
	if err != nil {
		return failure(err, "observe")
	}
	ga, err := k.NewAdminClient(&gc)
	if err != nil {
		return failure(err, "observe")
	}
	defer ga.Close()
	// Absent-group DescribeConsumerGroups timed out in the saved Java Admin
	// observation. Require a complete, error-free list before describing only
	// present groups. The tenant must be authorized to describe its own group.
	listed, err := ga.ListConsumerGroups(ctx, k.SetAdminRequestTimeout(2*time.Second))
	if err != nil {
		return failure(err, "observe")
	}
	if len(listed.Errors) != 0 {
		return bad("observe")
	}
	absent := true
	for _, item := range listed.Valid {
		if item.GroupID == group {
			absent = false
		}
	}
	members := 0
	if !absent {
		description, err := ga.DescribeConsumerGroups(ctx, []string{group}, k.SetAdminRequestTimeout(2*time.Second))
		if err != nil {
			return failure(err, "observe")
		}
		if len(description.ConsumerGroupDescriptions) != 1 {
			return bad("observe")
		}
		d := description.ConsumerGroupDescriptions[0]
		if d.GroupID != group || d.Error.Code() != k.ErrNoError {
			return bad("observe")
		}
		members = len(d.Members)
	}
	var committed interface{} = nil
	if !absent {
		offsets, err := ga.ListConsumerGroupOffsets(ctx, []k.ConsumerGroupTopicPartitions{{Group: group, Partitions: []k.TopicPartition{{Topic: &topic, Partition: 0}}}}, k.SetAdminRequestTimeout(2*time.Second))
		if err != nil {
			return failure(err, "observe")
		}
		if len(offsets.ConsumerGroupsTopicPartitions) != 1 {
			return bad("observe")
		}
		item := offsets.ConsumerGroupsTopicPartitions[0]
		if item.Group != group {
			return bad("observe")
		}
		if len(item.Partitions) != 1 {
			return bad("observe")
		}
		p := item.Partitions[0]
		if p.Error != nil {
			return failure(p.Error, "observe")
		}
		if p.Topic == nil || *p.Topic != topic || p.Partition != 0 {
			return bad("observe")
		}
		if p.Offset >= 0 {
			committed = int64(p.Offset)
		} else if p.Offset != k.OffsetInvalid {
			return bad("observe")
		}
	}
	tc, err := loadConfig(topicTenant + "-producer")
	if err != nil {
		return failure(err, "observe")
	}
	ta, err := k.NewAdminClient(&tc)
	if err != nil {
		return failure(err, "observe")
	}
	defer ta.Close()
	partition := k.TopicPartition{Topic: &topic, Partition: 0}
	ends, err := ta.ListOffsets(ctx, map[k.TopicPartition]k.OffsetSpec{partition: k.LatestOffsetSpec}, k.SetAdminRequestTimeout(2*time.Second))
	if err != nil {
		return failure(err, "observe")
	}
	end, exists := findOffset(ends, topic)
	if !exists || end.Error.Code() != k.ErrNoError || end.Offset < 0 {
		return bad("observe")
	}
	starts, err := ta.ListOffsets(ctx, map[k.TopicPartition]k.OffsetSpec{partition: k.EarliestOffsetSpec}, k.SetAdminRequestTimeout(2*time.Second))
	if err != nil {
		return failure(err, "observe")
	}
	start, exists := findOffset(starts, topic)
	if !exists || start.Error.Code() != k.ErrNoError || start.Offset < 0 {
		return bad("observe")
	}
	return ok(Result{"committed_offset": committed, "log_end_offset": int64(end.Offset), "log_start_offset": int64(start.Offset), "members": members, "membership_observed": true, "group_absent": absent})
}
func findOffset(result k.ListOffsetsResult, topic string) (k.ListOffsetsResultInfo, bool) {
	// The library allocates new Topic string pointers in response map keys.
	// Compare topic VALUES, never the pointer-bearing request map key.
	if len(result.ResultInfos) != 1 {
		return k.ListOffsetsResultInfo{}, false
	}
	for p, value := range result.ResultInfos {
		if p.Topic != nil && *p.Topic == topic && p.Partition == 0 {
			return value, true
		}
	}
	return k.ListOffsetsResultInfo{}, false
}
