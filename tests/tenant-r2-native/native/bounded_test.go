package r2native

import (
	"crypto/ed25519"
	"crypto/rand"
	"crypto/x509"
	"crypto/x509/pkix"
	"encoding/pem"
	"errors"
	"math/big"
	"runtime"
	"strings"
	"testing"
	"time"
)

func TestBoundedWaitDoesNotClaimCancellation(t *testing.T) {
	release := make(chan struct{})
	finished := make(chan struct{})
	r, timeout := boundedResult(5*time.Millisecond, "commit", func() Result { <-release; close(finished); return ok(nil) })
	if !timeout || r["ok"] != false || r["category"] != "timeout" {
		t.Fatal("timeout not preserved")
	}
	select {
	case <-finished:
		t.Fatal("must not claim SDK was cancelled")
	default:
	}
	close(release)
	select {
	case <-finished:
	case <-time.After(time.Second):
		t.Fatal("fake worker did not settle")
	}
}
func TestBoundedReturnPanicAndNoAdmission(t *testing.T) {
	r, timed := boundedResult(time.Second, "close", func() Result { return ok(nil) })
	if timed || r["ok"] != true {
		t.Fatal("return")
	}
	r, timed = boundedResult(time.Second, "close", func() Result { panic("SECRET_CANARY") })
	if timed || r["ok"] != false {
		t.Fatal("panic")
	}
	called := false
	_, timed = boundedResult(0, "close", func() Result { called = true; return ok(nil) })
	if !timed || called {
		t.Fatal("late call admitted")
	}
	m := &Module{started: true, born: time.Now(), faulted: true}
	if m.live() {
		t.Fatal("fault latch permits new work")
	}
}
func TestAllInputValidationBeforeNativeConstruction(t *testing.T) {
	now := time.Now()
	public, private, err := ed25519.GenerateKey(rand.Reader)
	if err != nil {
		t.Fatal("key")
	}
	template := &x509.Certificate{SerialNumber: big.NewInt(1), Subject: pkix.Name{CommonName: "offline-test-ca"}, NotBefore: now.Add(-time.Hour), NotAfter: now.Add(time.Hour), IsCA: true, BasicConstraintsValid: true, KeyUsage: x509.KeyUsageCertSign}
	der, err := x509.CreateCertificate(rand.Reader, template, template, public, private)
	if err != nil {
		t.Fatal("cert")
	}
	cert := pem.EncodeToMemory(&pem.Block{Type: "CERTIFICATE", Bytes: der})
	read := func(path string) ([]byte, error) {
		if strings.HasSuffix(path, "ca.crt") {
			return cert, nil
		}
		return []byte(path), nil
	}
	if validateInputs(read, now) != nil {
		t.Fatal("synthetic inputs refused")
	}
	sameValues := func(path string) ([]byte, error) {
		if strings.HasSuffix(path, "ca.crt") {
			return cert, nil
		}
		return []byte("same-opaque-value"), nil
	}
	if validateInputs(sameValues, now) != nil {
		t.Fatal("must validate credential references, not invent password-value policy")
	}
	for _, bad := range []string{"missing", "empty_password", "empty_ca", "expired"} {
		t.Run(bad, func(t *testing.T) {
			f := func(path string) ([]byte, error) {
				if strings.HasSuffix(path, "ca.crt") {
					if bad == "empty_ca" {
						return nil, nil
					}
					return cert, nil
				}
				if bad == "missing" && strings.Contains(path, "b-consumer") {
					return nil, errors.New("SECRET_CANARY")
				}
				if bad == "empty_password" {
					return nil, nil
				}
				return []byte(path), nil
			}
			at := now
			if bad == "expired" {
				at = now.Add(2 * time.Hour)
			}
			if validateInputs(f, at) == nil {
				t.Fatal("invalid inputs accepted")
			}
		})
	}
}

func TestTimeoutQuarantineIsLatchedAndPreventsMoreWork(t *testing.T) {
	h := &handle{}
	m := &Module{started: true, born: time.Now(), handles: map[int]*handle{1: h}}
	release := make(chan struct{})
	settled := make(chan struct{})
	r := m.boundedHandle(h, 5*time.Millisecond, "commit", func() Result { <-release; close(settled); return ok(nil) })
	if r["ok"] != false || !m.faulted || !h.quarantined || m.live() {
		t.Fatal("quarantine missing")
	}
	if m.OpenProducer("kaas-sbx-a-producer", "kaas-sbx-a-events")["ok"] != false || m.Close(1)["ok"] != false || m.ProbeState(1)["ok"] != false {
		t.Fatal("new work or unsafe concurrent close admitted")
	}
	close(release)
	<-settled
	if !m.faulted || !h.quarantined {
		t.Fatal("late success silently cleared uncertainty")
	}
}

func TestLateSuccessCannotWinAgainstExpiredTimer(t *testing.T) {
	old := runtime.GOMAXPROCS(1)
	defer runtime.GOMAXPROCS(old)
	for i := 0; i < 8; i++ {
		r, timed := boundedResult(100*time.Microsecond, "commit", func() Result {
			start := time.Now()
			for time.Since(start) < 2*time.Millisecond {
			}
			return ok(nil)
		})
		if !timed || r["ok"] != false {
			t.Fatal("late completion reported success")
		}
	}
}
