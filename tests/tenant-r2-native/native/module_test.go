package r2native

import (
	"encoding/json"
	k "github.com/confluentinc/confluent-kafka-go/v2/kafka"
	"strings"
	"testing"
)

// No producer, consumer or AdminClient is constructed in these checks.
func TestExplicitConfiguration(t *testing.T) {
	c, e := config("kaas-sbx-a-producer", "synthetic-canary")
	if e != nil {
		t.Fatal("configuration")
	}
	p := producerConfig(c)
	for key, want := range map[string]interface{}{"enable.idempotence": false, "message.send.max.retries": 0, "acks": "all", "compression.type": "none", "message.max.bytes": 3145728, "message.timeout.ms": 5000, "enable.ssl.certificate.verification": true, "ssl.endpoint.identification.algorithm": "https", "allow.auto.create.topics": false, "log_level": 0} {
		if p[key] != want {
			t.Fatalf("setting %s", key)
		}
	}
	c, e = config("kaas-sbx-a-consumer", "synthetic-canary")
	if e != nil {
		t.Fatal("configuration")
	}
	c = consumerConfig(c, "kaas-sbx-a-events-group")
	if c["enable.auto.commit"] != false || c["enable.auto.offset.store"] != false {
		t.Fatal("implicit commits")
	}
}
func TestBindingRejectsFallback(t *testing.T) {
	for _, principal := range []string{"kaas-smoke-client", "../password", "", "kaas-sbx-c-producer"} {
		if _, err := config(principal, "canary"); err == nil {
			t.Fatal("accepted principal")
		}
	}
	for _, password := range []string{"", "canary\n", "canary\x00"} {
		if _, err := config("kaas-sbx-b-consumer", password); err == nil {
			t.Fatal("accepted password")
		}
	}
	if groupOK("kaas-sbx-a-events-group-extra") || topicOK("kaas-sbx-a-events-x") {
		t.Fatal("roster")
	}
}
func TestTypedCodeStageAndRedaction(t *testing.T) {
	for _, sample := range []struct {
		code     k.ErrorCode
		category string
	}{{k.ErrTopicAuthorizationFailed, "topic_authorization_denied"}, {k.ErrGroupAuthorizationFailed, "group_authorization_denied"}, {k.ErrClusterAuthorizationFailed, "cluster_authorization_denied"}, {k.ErrSaslAuthenticationFailed, "authentication_failed"}, {k.ErrSsl, "tls_failed"}, {k.ErrTransport, "network_failed"}, {k.ErrTimedOut, "timeout"}} {
		r := failure(k.NewError(sample.code, "synthetic-secret-canary", false), "consume")
		if r["category"] != sample.category || r["stage"] != "consume" || r["native_code"] != int(sample.code) {
			t.Fatal("typed mapping")
		}
		raw, _ := json.Marshal(r)
		if strings.Contains(string(raw), "canary") {
			t.Fatal("redaction")
		}
	}
	if failure(nil, "consume")["category"] != "unknown" {
		t.Fatal("unknown")
	}
}
func TestMetadataOffsetUsesTopicValueNotPointer(t *testing.T) {
	topic := strings.Clone("kaas-sbx-a-events")
	result := k.ListOffsetsResult{ResultInfos: map[k.TopicPartition]k.ListOffsetsResultInfo{{Topic: &topic, Partition: 0}: {Offset: 7}}}
	got, ok := findOffset(result, "kaas-sbx-a-events")
	if !ok || got.Offset != 7 {
		t.Fatal("offset lookup")
	}
	if _, ok = findOffset(result, "kaas-sbx-b-events"); ok {
		t.Fatal("topic mismatch")
	}
}
func TestLinkedLibraryVersionWithoutClientConstruction(t *testing.T) {
	version := nativeVersion()
	if !strings.HasPrefix(version, "2.14.0") {
		t.Fatal("unexpected linked library version")
	}
	t.Log("linked librdkafka", version)
}
