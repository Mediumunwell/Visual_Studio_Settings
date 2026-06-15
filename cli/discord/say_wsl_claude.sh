#!/usr/bin/env bash
# Actor ③: posts the "WSL Ubuntu claude CLI" message through the KOTR bot.
cd "$(dirname "$0")"
python3 post_via_webhook.py \
  --username "KOTR (WSL-Claude)" \
  --message "③/4 — Claude Code running inside **WSL Ubuntu-24.04** on the laptop (claude CLI v2.1.118), posting through the KOTR bot. Same model as the desktop app, different runtime/shell."
