#!/usr/bin/env bash
# Set up venv + run the KOTR bot. Wrap with tmux/systemd to keep it alive.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; cd "$HERE"
[ -f .env ] && { set -a; . .env; set +a; }
python3 -m venv .venv 2>/dev/null || true
. .venv/bin/activate
pip install -q -U -r requirements.txt
exec python3 kotr-bot.py
