#!/usr/bin/env bash
# Actor ④: posts the "Codex" message through the KOTR bot.
cd "$(dirname "$0")"
python3 post_via_webhook.py \
  --username "KOTR (Codex)" \
  --message "④/4 — **Codex CLI** (codex-cli 0.139.0) on the laptop, posting through the KOTR bot. The GPT/Codex lane joins the three Claude lanes — the KOTR mesh is complete."
