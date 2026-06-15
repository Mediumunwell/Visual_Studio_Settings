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
    ap.add_argument("--message", required=True)
    ap.add_argument("--username", default="KOTR")
    ap.add_argument("--env-key", default="KOTR_WEBHOOK_URL")
    a = ap.parse_args()
    url = load_env_value(a.env_key)
    if not url:
        print(json.dumps({"ok": False, "error": f"no_webhook_url[{a.env_key}]"}))
        return 2
    payload = {"content": a.message[:1900], "username": a.username}
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
