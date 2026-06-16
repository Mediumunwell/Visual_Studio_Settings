#!/usr/bin/env python3
"""Post a message to Discord via a webhook URL, with a custom username (the
'KOTR' identity that the Claude/Codex actors post through).

Reads the webhook URL from env or cli/discord/.env under --env-key.
Usage: post_via_webhook.py --message "..." [--username KOTR] [--env-key KOTR_WEBHOOK_URL]
Output is JSON (status, message_id); the webhook URL is never printed.
"""
import argparse, json, os, urllib.request, urllib.error
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENV = HERE / ".env"


def load_env_value(key):
    v = os.environ.get(key, "").strip()
    if v:
        return v
    if ENV.exists():
        for ln in ENV.read_text(encoding="utf-8").splitlines():
            if ln.startswith(key + "="):
                return ln.split("=", 1)[1].strip()
    return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--message", required=True,
                    help="Concise, human-scannable summary (problems + solutions + key info).")
    ap.add_argument("--detail", default="",
                    help="Verbose AI-to-AI payload; posted in a ||spoiler|| after the summary. "
                         "Humans see the summary and click to expand; bots reading via the REST "
                         "API get the full text regardless (spoilers are client-side only).")
    ap.add_argument("--username", default="KOTR")
    ap.add_argument("--env-key", default="KOTR_WEBHOOK_URL")
    ap.add_argument("--dry-run", action="store_true",
                    help="Print the message body that WOULD be posted; do not contact Discord.")
    a = ap.parse_args()

    # Build the two-part body: summary in the open, detail tucked in a spoiler.
    # Discord hard-caps content at 2000 chars; keep the summary intact and fit the
    # detail into the remainder. A spoiler can't contain a literal '||', so neutralize it.
    LIMIT = 1990
    content = a.message[:LIMIT]
    if a.detail.strip():
        # Click-to-reveal: a small label + the detail as a spoiler-wrapped code block.
        # Collapsed it's a tidy "click to reveal" chip (not a wall of redacted prose);
        # expanded it's a clean monospace block. Neutralize ``` and || so neither breaks.
        safe = a.detail.replace("```", "ʼʼʼ").replace("||", "‖")
        head, tail = "\n-# 🤖 builder detail — click to reveal ↓\n||```\n", "\n```||"
        budget = LIMIT - len(content) - len(head) - len(tail)
        if budget > 20:
            clipped = safe[:budget]
            if len(safe) > budget:
                clipped = clipped[:-1] + "…"
            content += head + clipped + tail

    if a.dry_run:
        print(json.dumps({"ok": True, "dry_run": True, "username": a.username,
                          "chars": len(content), "content": content}))
        return 0

    url = load_env_value(a.env_key)
    if not url:
        print(json.dumps({"ok": False, "error": f"no_webhook_url[{a.env_key}]"}))
        return 2
    payload = {"content": content, "username": a.username}
    req = urllib.request.Request(
        url + "?wait=true",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": "kotr-webhook/1.0"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            msg = json.loads(raw) if raw else {}
        print(json.dumps({"ok": True, "status": resp.status,
                          "message_id": msg.get("id"), "username": a.username}))
        return 0
    except urllib.error.HTTPError as exc:
        print(json.dumps({"ok": False, "http_status": exc.code}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
