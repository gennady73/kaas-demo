#!/bin/sh
set -eu
[ "$(cat /arming/enabled 2>/dev/null || true)" = true ] || { printf '%s\n' 'R2_SINK_DISABLED' >&2; exit 78; }
exec python3 -u /opt/r2-sink/server.py --config /etc/r2-sink/config.json
