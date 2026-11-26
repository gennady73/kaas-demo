#!/bin/sh
set -eu
[ "$(cat /arming/enabled 2>/dev/null || true)" = true ] || { printf '%s\n' 'R2_CLIENT_DISABLED' >&2; exit 78; }
# Independent process containment; startup is additionally charged by runtime.json.
# Forced termination is incomplete/uncertain, never a clean delivery result.
exec timeout --signal=TERM --kill-after=5s 285s /usr/local/bin/k6 run /r2/entrypoint.js
