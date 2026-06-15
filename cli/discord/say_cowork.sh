#!/usr/bin/env bash
# Actor ②: posts the "Claude Cowork scheduled task" message through the KOTR bot.
cd "$(dirname "$0")"
python3 post_via_webhook.py \
  --username "KOTR (Cowork scheduled task)" \
  --message "②/4 — **Claude Cowork scheduled task** firing on the laptop and posting through the KOTR bot. Sent by an autonomous scheduled routine (no live operator in the loop)."
