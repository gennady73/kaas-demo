# Verified custom extension build, 2026-11-24

The original Docker Hub digest used by the failed run lacked the custom file/environment reader. This directory records the minimal corrections applied to an **isolated copy** of `/home/gunger/Projects/xk6-kafka`; that checkout was not edited. Its upstream HEAD was `85fb8f25cecd85506d078b75219ce3a82f18791a`, with pre-existing uncommitted custom edits in three Go files. The GitHub workload project HEAD was `f7ea2a3496362214db6b44ff9d37b853244b5c9d`; it imports a local extension build context and does not contain those custom Go edits.

Patches are relative to the inspected local working copy, not directly to pristine upstream. Complete original diff, corrected source archive, source-file hashes, resolved Go dependency files, commands, image BuildConfig and runtime receipts are preserved in the coordinator workspace at `docs/testing/runs/xk6-20261124/`. See the result report before reproducing.

The custom reader uses `/script/kafka-client-limits.txt` first, then `XK6_KAFKA_MAX_BYTES`, then 52,428,800 bytes, once per process. A different setting requires a new client process. The selected run uses 3,145,728 transport bytes for values up to 2,097,152 bytes. The framework's `CLIENT_MAX_BYTES`/`extraConfig` path is not equivalent: inspected WriterConfig has no extraConfig field.

Build corrections restore the missing fmt import, remove Java-only max.request.size, disable native debug logging, and add a narrowly allowlisted effective-size/acks line. No connection configuration or credentials are printed. Producer configuration is message.max.bytes for librdkafka; Java uses a different property. Source: [librdkafka 2.14 configuration](https://github.com/confluentinc/librdkafka/blob/v2.14.0/CONFIGURATION.md).

Selected toolchain is Go1.26.4, CGO enabled, k6 v1.7.1 pinned to the extension go.mod. This deliberately replaces the mutable image's k6 v1.8.1 build; it is not a bit-for-bit recreation of that old image. The runtime probe verifies the new binary hash and file precedence with no Kafka credentials. A sandbox-only image build retains the pinned UBI image as its base and replaces k6; nothing was pushed to Docker Hub.

Configurable size support is bounded by client/broker/topic limits, protocol limits and available resources; this test does not demonstrate arbitrary sizes.

## Rebuild from versioned inputs

The original custom working-tree changes are now included as `original-local-changes.patch`; apply them before the three correction patches. `build/` contains the resolved dependency graph and generated main/extension imports from the executed build, with only the local replacement path changed to a relative path. These instructions reproduce the source/dependency selection; binary equality on another host is not guaranteed. No image push or Kafka traffic occurs in these commands.

From the kaas-demo repository root, with Git, patch, Go1.26.4, a C compiler and Podman installed:

```sh
cp -R tests/dev-smoke/custom-extension /tmp/kaas-xk6-rebuild
cd /tmp/kaas-xk6-rebuild
git clone https://github.com/mostafa/xk6-kafka.git extension
git -C extension checkout --detach 85fb8f25cecd85506d078b75219ce3a82f18791a
git -C extension apply --check ../original-local-changes.patch
git -C extension apply ../original-local-changes.patch
patch --dry-run -d extension/pkg/kafka -p1 < writer.go.patch
patch -d extension/pkg/kafka -p1 < writer.go.patch
patch --dry-run -d extension/pkg/kafka -p1 < confluent_config.go.patch
patch -d extension/pkg/kafka -p1 < confluent_config.go.patch
patch --dry-run -d extension/pkg/kafka -p1 < producer.go.patch
patch -d extension/pkg/kafka -p1 < producer.go.patch
cd build
env GOTOOLCHAIN=go1.26.4 GOEXPERIMENT= CGO_ENABLED=1 go build -mod=readonly -buildvcs=false -trimpath -ldflags='-s -w' -o ../k6 .
cd ..
./k6 version
sha256sum k6
podman build -f Dockerfile -t localhost/kaas-xk6-verified:local .
```

Use a fresh temporary directory if that destination already exists. The original upstream checkout is not modified. The container base is retained from the audited image; its k6 executable is replaced by the new binary. Verify the executable hash inside the resulting container before use; do not assume the historical sandbox image digest applies to a rebuild. The original upstream license remains in `extension/LICENSE`; retain it when redistributing source/binaries.

Build preparation may download Go modules/toolchains and images. Runtime probe and smoke execution require the reviewed manifests/credentials described in the result report; rebuilding an image alone is not evidence of delivery. The build module is a recipe, not a Go module to run tests against during normal repository checks.
