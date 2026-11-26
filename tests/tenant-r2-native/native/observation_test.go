package r2native

import (
	"context"
	"testing"
)

func TestObservationBindingAllFixturePairs(t *testing.T) {
	topics := []string{"kaas-sbx-a-events", "kaas-sbx-a-audit", "kaas-sbx-b-events", "kaas-sbx-b-audit"}
	for _, topic := range topics {
		for _, ownerTopic := range topics {
			if got := observationOK(topic, ownerTopic+"-group"); got != (topic == ownerTopic) {
				t.Fatal("observation binding", topic, ownerTopic, got)
			}
		}
	}
	for _, group := range []string{"", "kaas-sbx-a-events", "kaas-sbx-a-events-group-extra"} {
		if observationOK(topics[0], group) {
			t.Fatal("invalid group accepted")
		}
	}
}
func TestMixedSnapshotRejectedBeforeCredentialOrAdminAccess(t *testing.T) {
	// This path has no credential fixtures and must not construct any SDK client.
	r := snapshot(context.Background(), "kaas-sbx-b-events", "kaas-sbx-a-events-group")
	if r["ok"] != false || r["stage"] != "observe" || r["native_code"] != 0 {
		t.Fatal("mixed observation accepted", r)
	}
}
