package r2native

import (
	"bytes"
	"crypto/x509"
	"encoding/pem"
	"errors"
	"time"
)

// Validates all mounted inputs before any native constructor. No values or
// digests leave Go. Leaf SAN/chain/network validation still occurs at TLS time.
func validateInputs(read func(string) ([]byte, error), now time.Time) error {
	for _, principal := range []string{"kaas-sbx-a-producer", "kaas-sbx-a-consumer", "kaas-sbx-b-producer", "kaas-sbx-b-consumer"} {
		value, err := read("/credentials/" + principal + "/password")
		if err != nil || len(value) > 1024 {
			return errors.New("credential")
		}
		if _, err = config(principal, string(value)); err != nil {
			return errors.New("credential")
		}
	}
	raw, err := read("/credentials/cluster-ca/ca.crt")
	if err != nil || len(raw) > 65536 {
		return errors.New("trust")
	}
	found := false
	for len(bytes.TrimSpace(raw)) > 0 {
		block, rest := pem.Decode(raw)
		if block == nil || block.Type != "CERTIFICATE" {
			return errors.New("trust")
		}
		cert, err := x509.ParseCertificate(block.Bytes)
		if err != nil || !cert.IsCA || now.Before(cert.NotBefore) || now.After(cert.NotAfter) {
			return errors.New("trust")
		}
		found = true
		raw = rest
	}
	if !found {
		return errors.New("trust")
	}
	return nil
}
