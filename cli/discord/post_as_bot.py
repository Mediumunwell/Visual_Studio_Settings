#!/usr/bin/env python3
"""Post a message to a Discord channel AS a bot, via REST. No gateway, no discord.py.

Reusable posting primitive for the KOTR backend mesh: every actor (Claude Code,
Cowork, WSL claude CLI, Codex, Gir) calls this to write into the shared channel.

Token resolution order (first hit wins):
  1. --token-env NAME  (an env var name you choose)
  2. $DISCORD_BOT_TOKEN, $KOTR_BOT_TOKEN, $GIR_DISCORD_BOT_TOKEN
  3. ~/.clawhip/config.toml  ->  [providers.discord].token

The token is NEVER printed. Output is JSON with the http status / message id /
bot identity so callers (and screenshots/logs) can verify without leaking secrets.

Examples:
  # read-only: confirm the token works + which bot identity it is
  post_as_bot.py --whoami
  # post a message as that bot
  post_as_bot.py --channel 1491016855945613352 --message "hello from LAPTOP"
"""
import argparse, json, os, urllib.request, urllib.error
from pathlib import Path

TOKEN_ENV_NAMES = ["DISCORD_BOT_TOKEN", "KOTR_BOT_TOKEN", "GIR_DISCORD_BOT_TOKEN"]


def load_token(explicit_env=None):
    names = ([explicit_env] if explicit_env else []) + TOKEN_ENV_NAMES
    for n in names:
        v = os.environ.get(n, "").strip()
        if v:
            return v, f"env:{n}"
    cfg = Path.home() / ".clawhip" / "config.toml"
    if cfg.exists():
        try:
            try:
                import tomllib
            except ModuleNotFoundError:  # Python < 3.11 (e.g. Ubuntu 22.04/py3.10)
                import tomli as tomllib
            data = tomllib.loads(cfg.read_text(encoding="utf-8"))
            tok = str(data.get("providers", {}).get("discord", {}).get("token", "")).strip()
            if tok:
                return tok, "clawhip:config.toml"
        except Exception as exc:  # noqa: BLE001
            return "", f"clawhip_parse_error:{exc}"
    return "", "none"


def api(method, path, token, payload=None):
    url = "https://discord.com/api/v10" + path
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Authorization": f"Bot {token}", "User-Agent": "kotr-poster/1.0"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read().decode("utf-8")
        return resp.status, (json.loads(raw) if raw else {})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--channel", help="target channel id (snowflake)")
    ap.add_argument("--message", help="message text; if omitted, only --whoami runs")
    ap.add_argument("--token-env", default=None, help="env var name to read the token from first")
    ap.add_argument("--whoami", action="store_true", help="also report the bot identity (GET /users/@me)")
    a = ap.parse_args()

    token, src = load_token(a.token_env)
    out = {"token_source": src}
    if not token:
        out["ok"] = False
        out["error"] = "no_token_found"
        print(json.dumps(out))
        return 2

    try:
        if a.whoami or not a.message:
            _, me = api("GET", "/users/@me", token)
            out["bot"] = f'{me.get("username")}#{me.get("discriminator")} (id={me.get("id")})'
            out["bot_id"] = me.get("id")
        if a.message:
            if not a.channel:
                out["ok"] = False
                out["error"] = "channel_required_to_post"
                print(json.dumps(out))
                return 2
            status, msg = api("POST", f"/channels/{a.channel}/messages", token,
                              {"content": a.message[:1900]})
            out["ok"] = True
            out["status"] = status
            out["message_id"] = msg.get("id")
            out["channel"] = a.channel
        else:
            out["ok"] = True
            out["note"] = "whoami_only_no_post"
        print(json.dumps(out))
        return 0
    except urllib.error.HTTPError as exc:
        out["ok"] = False
        out["http_status"] = exc.code
        try:
            out["body"] = json.loads(exc.read().decode("utf-8"))
        except Exception:  # noqa: BLE001
            out["body"] = None
        print(json.dumps(out))
        return 1
    except Exception as exc:  # noqa: BLE001
        out["ok"] = False
        out["error"] = str(exc)
        print(json.dumps(out))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
