#!/usr/bin/env python3
"""Create a Discord webhook in a channel using the GIR bot token, and write its
URL into cli/discord/.env (gitignored) under a chosen key. Never prints the secret.

Usage: make_webhook.py <channel_id> [name=KOTR] [env_key=KOTR_WEBHOOK_URL]
Requires the bot to have Manage Webhooks in that channel; reports 403 if not.
"""
import json, sys, urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from post_as_bot import load_token, api  # noqa: E402

HERE = Path(__file__).resolve().parent
ENV = HERE / ".env"


def upsert_env(key, value):
    lines = ENV.read_text(encoding="utf-8").splitlines() if ENV.exists() else []
    out, found = [], False
    for ln in lines:
        if ln.startswith(key + "="):
            out.append(f"{key}={value}"); found = True
        else:
            out.append(ln)
    if not found:
        out.append(f"{key}={value}")
    ENV.write_text("\n".join(out) + "\n", encoding="utf-8")


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"ok": False, "error": "usage: make_webhook.py <channel_id> [name] [env_key]"}))
        return 2
    channel = sys.argv[1]
    name = sys.argv[2] if len(sys.argv) > 2 else "KOTR"
    env_key = sys.argv[3] if len(sys.argv) > 3 else "KOTR_WEBHOOK_URL"
    token, _ = load_token(None)
    if not token:
        print(json.dumps({"ok": False, "error": "no_token"}))
        return 2
    try:
        _, wh = api("POST", f"/channels/{channel}/webhooks", token, {"name": name})
    except urllib.error.HTTPError as exc:
        body = None
        try:
            body = json.loads(exc.read().decode("utf-8"))
        except Exception:  # noqa: BLE001
            pass
        print(json.dumps({"ok": False, "http_status": exc.code, "body": body}))
        return 1
    url = f"https://discord.com/api/webhooks/{wh['id']}/{wh['token']}"
    upsert_env(env_key, url)
    print(json.dumps({"ok": True, "webhook_id": wh.get("id"), "name": wh.get("name"),
                      "channel": channel, "env_key": env_key, "env_file": str(ENV)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
