#!/usr/bin/env bash
# Post a message to the shared Discord channel. Usage: ./notify.sh "your message"
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
[ -f "$HERE/.env" ] && . "$HERE/.env"
: "${DISCORD_WEBHOOK:?Set DISCORD_WEBHOOK in cli/discord/.env (copy .env.example)}"
HOST="$(hostname)"; MSG="${*:-(no message)}"
PAYLOAD="$(python3 -c 'import json,sys; print(json.dumps({"content": f"[{sys.argv[1]}] {sys.argv[2]}"}))' "$HOST" "$MSG")"
curl -fsS -H "Content-Type: application/json" -d "$PAYLOAD" "$DISCORD_WEBHOOK" >/dev/null \
  && echo "posted to Discord as [$HOST]"
