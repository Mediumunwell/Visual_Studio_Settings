#!/usr/bin/env python3
"""Read recent messages from a Discord channel AS the bot (the read half the
webhook can't do). Companion to post_as_bot.py / post_via_webhook.py.

Token resolution (first hit wins): --token-env NAME, then $DISCORD_BOT_TOKEN /
$KOTR_BOT_TOKEN / $GIR_DISCORD_BOT_TOKEN, then ~/.clawhip/config.toml. (On
Python <3.11 the clawhip TOML path needs tomli; the env vars always work — do
`set -a; . ./.env; set +a` first so KOTR_BOT_TOKEN is exported.) Token never printed.

Usage: read_channel.py [--channel ID] [--limit N] [--json]
Default channel = #kotr-ai-builders (1515624584815181905, verified via
discord_channels.py; NOTE the 2026-06-16 Drive credentials note mislabeled
1491016855945613352 as kotr-ai-builders — that id is gir-ops-private).
"""
import argparse, json, os, urllib.request, urllib.error

DEFAULT_CHANNEL = "1515624584815181905"  # #kotr-ai-builders
TOKEN_ENV_NAMES = ["DISCORD_BOT_TOKEN", "KOTR_BOT_TOKEN", "GIR_DISCORD_BOT_TOKEN"]


def load_token(explicit_env=None):
    for n in ([explicit_env] if explicit_env else []) + TOKEN_ENV_NAMES:
        v = os.environ.get(n, "").strip()
        if v:
            return v
    cfg = os.path.expanduser("~/.clawhip/config.toml")
    if os.path.exists(cfg):
        try:
            try:
                import tomllib
            except ModuleNotFoundError:  # Python < 3.11 (e.g. Ubuntu 22.04/py3.10)
                import tomli as tomllib
            with open(cfg, "rb") as fh:
                data = tomllib.load(fh)
            return str(data.get("providers", {}).get("discord", {}).get("token", "")).strip()
        except Exception:
            return ""
    return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--channel", default=DEFAULT_CHANNEL)
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--token-env", default=None)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    tok = load_token(a.token_env)
    if not tok:
        print(json.dumps({"ok": False, "error": "no_token_found"}))
        return 2
    req = urllib.request.Request(
        f"https://discord.com/api/v10/channels/{a.channel}/messages?limit={a.limit}",
        headers={"Authorization": f"Bot {tok}", "User-Agent": "kotr-reader/1.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            msgs = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        print(json.dumps({"ok": False, "http_status": exc.code}))
        return 1
    if a.json:
        print(json.dumps(msgs))
        return 0
    for m in reversed(msgs):  # oldest -> newest
        who = m.get("author", {}).get("username", "?")
        ts = (m.get("timestamp") or "")[:19].replace("T", " ")
        txt = " ".join((m.get("content") or "").split())
        if len(txt) > 280:
            txt = txt[:277] + "..."
        print(f"[{ts}] {who}: {txt or '(no text)'}")
    print(f"\n--- {len(msgs)} messages (channel {a.channel}) ---")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
