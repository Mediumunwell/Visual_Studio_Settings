#!/usr/bin/env python3
"""List text channels in the guild that owns a seed channel (name -> id). Read-only.

Usage: discord_channels.py [seed_channel_id]
Reuses post_as_bot.load_token (clawhip / env) so no token handling here.
"""
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from post_as_bot import load_token, api  # noqa: E402


def main():
    seed = sys.argv[1] if len(sys.argv) > 1 else "1491016855945613352"
    token, src = load_token(None)
    if not token:
        print(json.dumps({"ok": False, "error": "no_token", "src": src}))
        return 2
    _, ch = api("GET", f"/channels/{seed}", token)
    guild = ch.get("guild_id")
    _, chans = api("GET", f"/guilds/{guild}/channels", token)
    text = [
        {"name": c.get("name"), "id": c.get("id"), "type": c.get("type")}
        for c in chans
        if c.get("type") in (0, 5)
    ]
    print(json.dumps({
        "ok": True,
        "guild_id": guild,
        "seed_name": ch.get("name"),
        "channels": sorted(text, key=lambda x: x["name"] or ""),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
