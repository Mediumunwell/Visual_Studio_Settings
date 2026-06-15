#!/usr/bin/env bash
# KOTR Builder — Engine A: the claude -p loop (least likely to block). Launch detached:
#   tmux new -ds kotr-builder 'bash ~/Visual_Studio_Settings/cli/builder/kotr_builder_loop.sh'
# Halt: create the file KOTR_BUILDER.OFF in this folder (or: tmux kill-session -t kotr-builder).
set -uo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"; cd "$DIR"
SLEEP="${BUILDER_SLEEP:-180}"
say() { python3 "$DIR/../discord/post_via_webhook.py" --username "KOTR (builder:claude-p)" --message "$1" >/dev/null 2>&1 || true; }
say "🛠️ builder:claude-p loop online on $(hostname); cycle ~${SLEEP}s; halt via KOTR_BUILDER.OFF"
while [ ! -f "$DIR/KOTR_BUILDER.OFF" ]; do
  bash "$DIR/run_one_cycle.sh" claude-p >> "$DIR/loop.log" 2>&1 || echo "cycle rc=$? $(date -u +%FT%TZ)" >> "$DIR/loop.log"
  sleep "$SLEEP"
done
say "builder:claude-p loop stopped (KOTR_BUILDER.OFF present)"
