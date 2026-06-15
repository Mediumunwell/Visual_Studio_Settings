#!/usr/bin/env bash
# KOTR Builder — ONE cycle, shared by all engines. Arg1 = engine name.
set -uo pipefail
ENGINE="${1:-scheduled}"
DIR="$(cd "$(dirname "$0")" && pwd)"; cd "$DIR"
[ -f "$DIR/KOTR_BUILDER.OFF" ] && { echo "OFF"; exit 0; }
FREEMB=$(free -m 2>/dev/null | awk '/^Mem:/{print $7}')
[ "${FREEMB:-9999}" -lt 1500 ] && { echo "RAM-gate ${FREEMB}MB"; exit 0; }
exec env ENGINE="$ENGINE" claude -p --dangerously-skip-permissions \
  "You are running as engine '$ENGINE'. Read $DIR/BUILDER_PROMPT.md in full and execute exactly ONE cycle as specified (acquire LOCK, do one matching QUEUE item, verify with evidence, append + post the scoreboard line to #kotr-ai-builders, commit, release LOCK). Working folder: $DIR. Engine-affinity: skip QUEUE items tagged for an engine you are not — e.g. browser-only items if you have no Chrome MCP."
