#!/usr/bin/env python3
"""KOTR<->Gir bidirectional handshake gateway.

A tiny mirror of ~/Gir/tools/discord_operator_listener.py, scoped to ONE job:
prove a bidirectional KOTR<->Gir loop in `#kotr-ai-builders` ---
    KOTR posts a handshake  ->  Gir acks it  ->  KOTR acks back.

Two identities are in play:
  * KOTR posts AS the webhook ("KOTR (builder:...)") via post_via_webhook.py.
  * KOTR *listens* AS its own bot, using KOTR_BOT_TOKEN. A webhook is write-only
    and cannot read a channel, so the listen half needs a real bot token. That
    token comes from the (desktop-only) "Standalone KOTR bot app" queue item;
    until it exists, `run-loop`/`once` gate cleanly with a clear message and the
    handshake STATE MACHINE is still fully exercisable offline via `selftest`,
    and the live poll path is provable read-only via `probe`.

Token resolution (first hit wins): --token-env NAME, then $KOTR_BOT_TOKEN,
then $DISCORD_BOT_TOKEN. The clawhip GIR token is deliberately NOT a fallback for
the live loop (wrong identity) but MAY be passed explicitly to `probe`/`whoami`
for read-only verification.

Subcommands:
  selftest                 offline handshake state-machine assertions (no network)
  probe   [--channel ID]   read-only: poll the channel, print HTTP status + ids
  whoami                   confirm which bot identity the token is (read-only)
  initiate [--channel ID]  post a KOTR->Gir handshake (via webhook) and record nonce
  once    [--channel ID]   one poll pass: detect Gir acks, post KOTR ack-backs
  run-loop                 poll forever (needs KOTR_BOT_TOKEN)
  status                   print persisted handshake state

The webhook URL / token are NEVER printed. Output is JSON for screenshots+logs.
"""
from __future__ import annotations

import argparse
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
STATE_PATH = HERE / ".run" / "kotr_gateway_state.json"
AUDIT_LOG = HERE / ".run" / "kotr_gateway_audit.jsonl"

# Identities / channels (see KOTR_BACKEND.md).
KOTR_BUILDERS_CHANNEL = "1515624584815181905"
GIR_BOT_ID = "1491019273085124678"  # GIR#3756

HANDSHAKE_TAG = "kotr->gir handshake"   # what KOTR posts to start a round
ACKBACK_TAG = "kotr<-gir ack confirmed"  # what KOTR posts once Gir has acked
GIR_ACK_MARKERS = ("ack", "gir command menu", "menu:")  # signals a Gir reply


# ---- token / env helpers (mirror post_as_bot.py) ----------------------------

def load_token(explicit_env: str | None = None) -> tuple[str, str]:
    names = ([explicit_env] if explicit_env else []) + ["KOTR_BOT_TOKEN", "DISCORD_BOT_TOKEN"]
    for n in names:
        v = os.environ.get(n, "").strip()
        if v:
            return v, f"env:{n}"
    return "", "none"


def load_clawhip_token() -> tuple[str, str]:
    """Read-only fallback for probe/whoami ONLY (GIR identity)."""
    cfg = Path.home() / ".clawhip" / "config.toml"
    if not cfg.exists():
        return "", "none"
    try:
        try:
            import tomllib
        except ModuleNotFoundError:  # Python < 3.11 (e.g. Ubuntu 22.04/py3.10)
            import tomli as tomllib
        data = tomllib.loads(cfg.read_text(encoding="utf-8"))
        tok = str(data.get("providers", {}).get("discord", {}).get("token", "")).strip()
        return (tok, "clawhip:config.toml") if tok else ("", "none")
    except Exception as exc:  # noqa: BLE001
        return "", f"clawhip_parse_error:{exc}"


# ---- persistence ------------------------------------------------------------

def load_state() -> dict[str, Any]:
    if not STATE_PATH.exists():
        return {"last_seen": {}, "pending": {}, "completed": []}
    return json.loads(STATE_PATH.read_text(encoding="utf-8"))


def save_state(state: dict[str, Any]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def append_audit(payload: dict[str, Any]) -> None:
    AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
    with AUDIT_LOG.open("a", encoding="utf-8") as h:
        h.write(json.dumps(payload, ensure_ascii=True) + "\n")


# ---- discord REST -----------------------------------------------------------

def discord_api(method: str, path: str, token: str,
                query: dict[str, str] | None = None,
                payload: dict[str, Any] | None = None) -> tuple[int, Any]:
    url = "https://discord.com/api/v10" + path
    if query:
        url += "?" + urllib.parse.urlencode(query)
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Authorization": f"Bot {token}", "User-Agent": "kotr-gir-gateway/0.1"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read().decode("utf-8")
        return resp.status, (json.loads(raw) if raw else {})


def fetch_recent(channel_id: str, token: str, after: str = "") -> list[dict[str, Any]]:
    q = {"limit": "20"}
    if after:
        q["after"] = after
    _, data = discord_api("GET", f"/channels/{channel_id}/messages", token, query=q)
    return list(reversed(data)) if isinstance(data, list) else []


# ---- KOTR posting (via the existing webhook identity) -----------------------

def post_as_kotr(message: str, username: str = "KOTR (gateway)") -> dict[str, Any]:
    import subprocess
    cp = subprocess.run(
        ["python3", str(HERE / "post_via_webhook.py"),
         "--username", username, "--message", message],
        cwd=HERE, text=True, capture_output=True,
    )
    try:
        return json.loads((cp.stdout or "").strip().splitlines()[-1])
    except Exception:  # noqa: BLE001
        return {"ok": False, "raw": (cp.stdout or cp.stderr or "")[:300]}


# ---- pure handshake state machine (network-free; unit-testable) -------------

def is_kotr_self(msg: dict[str, Any]) -> bool:
    """KOTR's own webhook/gateway posts — must be ignored to avoid loops."""
    author = msg.get("author", {}) or {}
    if msg.get("webhook_id"):
        return True
    name = str(author.get("username", "")).lower()
    return name.startswith("kotr")


def is_gir(msg: dict[str, Any]) -> bool:
    author = msg.get("author", {}) or {}
    return str(author.get("id", "")) == GIR_BOT_ID


def gir_ack_nonce(msg: dict[str, Any]) -> str | None:
    """If this is a Gir message that acknowledges a KOTR handshake, return its nonce."""
    if not is_gir(msg):
        return None
    content = str(msg.get("content", "")).lower()
    if not any(m in content for m in GIR_ACK_MARKERS):
        return None
    # nonce echoed back by Gir, or carried in a reply reference we matched upstream
    for tok in content.replace("`", " ").split():
        if tok.startswith("hs-"):
            return tok
    return "hs-unscoped"  # Gir acked but echoed no nonce -> still a valid ack signal


def plan_ackbacks(messages: list[dict[str, Any]], pending: dict[str, Any]) -> list[dict[str, Any]]:
    """Given new messages + pending handshakes, return the KOTR ack-backs to post.

    Pure: no I/O. Each result = {"nonce": ..., "message": ...}. A nonce is acked at
    most once. An unscoped Gir ack closes the oldest still-pending handshake.
    """
    out: list[dict[str, Any]] = []
    remaining = dict(pending)
    for msg in messages:
        if is_kotr_self(msg):
            continue
        nonce = gir_ack_nonce(msg)
        if nonce is None:
            continue
        if nonce == "hs-unscoped":
            if not remaining:
                continue
            nonce = sorted(remaining)[0]
        if nonce in remaining:
            del remaining[nonce]
            out.append({"nonce": nonce,
                        "message": f"{ACKBACK_TAG} {nonce} (KOTR<-GIR loop closed)"})
    return out


# ---- subcommands ------------------------------------------------------------

def cmd_selftest(_a: argparse.Namespace) -> int:
    checks: list[tuple[str, bool]] = []

    # self / webhook posts are ignored
    checks.append(("ignore_webhook_self",
                   is_kotr_self({"webhook_id": "123", "author": {"username": "KOTR (builder)"}})))
    checks.append(("ignore_named_self",
                   is_kotr_self({"author": {"username": "KOTR (gateway)"}})))
    checks.append(("human_not_self",
                   not is_kotr_self({"author": {"username": "Evan", "id": "207836507480784896"}})))

    # gir detection + nonce extraction
    gir_ack = {"author": {"id": GIR_BOT_ID, "username": "GIR"},
               "content": "ack hs-abc123 menu: ..."}
    checks.append(("gir_detected", is_gir(gir_ack)))
    checks.append(("nonce_extracted", gir_ack_nonce(gir_ack) == "hs-abc123"))
    checks.append(("nonbot_no_nonce",
                   gir_ack_nonce({"author": {"id": "999"}, "content": "ack hs-abc123"}) is None))

    # full round: one pending handshake, Gir acks it -> exactly one ack-back
    pending = {"hs-abc123": {"ts": 1}}
    msgs = [
        {"author": {"username": "KOTR (builder)"}, "webhook_id": "w",
         "content": f"{HANDSHAKE_TAG} hs-abc123"},          # KOTR's own initiate (ignored)
        {"author": {"id": "207836507480784896"}, "content": "chatter"},  # noise
        gir_ack,                                            # Gir ack -> should close
    ]
    plans = plan_ackbacks(msgs, pending)
    checks.append(("one_ackback", len(plans) == 1))
    checks.append(("ackback_nonce", plans and plans[0]["nonce"] == "hs-abc123"))
    checks.append(("ackback_text", plans and ACKBACK_TAG in plans[0]["message"]))

    # idempotency: no pending -> no ack-back even if Gir re-acks
    checks.append(("no_double_ack", plan_ackbacks([gir_ack], {}) == []))

    # unscoped Gir ack closes the oldest pending
    plans2 = plan_ackbacks(
        [{"author": {"id": GIR_BOT_ID}, "content": "ack (menu:)"}],
        {"hs-002": {"ts": 2}, "hs-001": {"ts": 1}},
    )
    checks.append(("unscoped_closes_oldest", plans2 and plans2[0]["nonce"] == "hs-001"))

    passed = all(ok for _, ok in checks)
    print(json.dumps({
        "ok": passed,
        "mode": "selftest",
        "checks": {name: bool(ok) for name, ok in checks},
        "passed": sum(1 for _, ok in checks if ok),
        "total": len(checks),
    }, indent=2))
    return 0 if passed else 1


def _resolve_read_token(args: argparse.Namespace) -> tuple[str, str]:
    tok, src = load_token(getattr(args, "token_env", None))
    if tok:
        return tok, src
    if getattr(args, "allow_clawhip", False):
        return load_clawhip_token()
    return "", "none"


def cmd_probe(args: argparse.Namespace) -> int:
    tok, src = _resolve_read_token(args)
    if not tok:
        print(json.dumps({"ok": False, "error": "no_read_token",
                          "hint": "pass --allow-clawhip for read-only GIR-token probe, "
                                  "or set KOTR_BOT_TOKEN"}))
        return 2
    ch = args.channel
    try:
        st, msgs = discord_api("GET", f"/channels/{ch}/messages", tok, query={"limit": "3"})
    except urllib.error.HTTPError as exc:
        print(json.dumps({"ok": False, "http_status": exc.code, "token_src": src}))
        return 1
    latest = msgs[0] if isinstance(msgs, list) and msgs else {}
    print(json.dumps({
        "ok": st == 200,
        "mode": "probe",
        "channel": ch,
        "http_status": st,
        "token_src": src,
        "msg_count": len(msgs) if isinstance(msgs, list) else None,
        "latest_id": latest.get("id"),
        "latest_author": (latest.get("author") or {}).get("username"),
    }, indent=2))
    return 0 if st == 200 else 1


def cmd_whoami(args: argparse.Namespace) -> int:
    tok, src = _resolve_read_token(args)
    if not tok:
        print(json.dumps({"ok": False, "error": "no_token", "src": src}))
        return 2
    try:
        st, me = discord_api("GET", "/users/@me", tok)
    except urllib.error.HTTPError as exc:
        print(json.dumps({"ok": False, "http_status": exc.code}))
        return 1
    print(json.dumps({"ok": st == 200, "mode": "whoami", "token_src": src,
                      "bot": f"{me.get('username')}#{me.get('discriminator')}",
                      "bot_id": me.get("id")}))
    return 0 if st == 200 else 1


def cmd_initiate(args: argparse.Namespace) -> int:
    nonce = "hs-" + uuid.uuid4().hex[:8]
    res = post_as_kotr(f"{HANDSHAKE_TAG} {nonce} (awaiting Gir ack)")
    if res.get("ok"):
        state = load_state()
        state.setdefault("pending", {})[nonce] = {"ts": int(time.time()),
                                                   "msg_id": res.get("message_id")}
        save_state(state)
        append_audit({"event": "kotr_initiate", "nonce": nonce, "msg_id": res.get("message_id")})
    print(json.dumps({"ok": bool(res.get("ok")), "mode": "initiate",
                      "nonce": nonce, "post": res}))
    return 0 if res.get("ok") else 1


def _one_pass(args: argparse.Namespace, token: str) -> dict[str, Any]:
    state = load_state()
    ch = args.channel
    after = str(state.get("last_seen", {}).get(ch, "")).strip()
    messages = fetch_recent(ch, token, after=after)
    if messages:
        state.setdefault("last_seen", {})[ch] = str(messages[-1].get("id", "") or after)
    plans = plan_ackbacks(messages, state.get("pending", {}))
    posted = []
    for plan in plans:
        res = post_as_kotr(plan["message"])
        if res.get("ok"):
            state.get("pending", {}).pop(plan["nonce"], None)
            state.setdefault("completed", []).append(
                {"nonce": plan["nonce"], "ts": int(time.time()), "ack_msg_id": res.get("message_id")})
            append_audit({"event": "kotr_ackback", "nonce": plan["nonce"],
                          "msg_id": res.get("message_id")})
            posted.append({"nonce": plan["nonce"], "msg_id": res.get("message_id")})
    save_state(state)
    return {"scanned": len(messages), "ackbacks": posted,
            "pending": list(state.get("pending", {}).keys())}


def cmd_once(args: argparse.Namespace) -> int:
    tok, src = _resolve_read_token(args)
    if not tok:
        print(json.dumps({"ok": False, "error": "KOTR_BOT_TOKEN not found",
                          "gated_on": "Standalone KOTR bot app (desktop) -> KOTR_BOT_TOKEN",
                          "hint": "pass --allow-clawhip only for read-only experiments"}))
        return 2
    out = _one_pass(args, tok)
    out.update({"ok": True, "mode": "once", "token_src": src})
    print(json.dumps(out, indent=2))
    return 0


def cmd_run_loop(args: argparse.Namespace) -> int:
    tok, _ = _resolve_read_token(args)
    if not tok:
        print(json.dumps({"ok": False, "error": "KOTR_BOT_TOKEN not found",
                          "gated_on": "Standalone KOTR bot app (desktop) -> KOTR_BOT_TOKEN"}))
        return 2
    interval = max(2, int(args.interval_seconds))
    while True:
        try:
            _one_pass(args, tok)
        except urllib.error.HTTPError as exc:
            append_audit({"event": "kotr_gateway_http_error", "status": exc.code})
        except Exception as exc:  # noqa: BLE001
            append_audit({"event": "kotr_gateway_error", "error": str(exc)})
        time.sleep(interval)


def cmd_status(_a: argparse.Namespace) -> int:
    state = load_state()
    print(json.dumps({"ok": True, "mode": "status", "state_path": str(STATE_PATH),
                      "last_seen": state.get("last_seen", {}),
                      "pending": state.get("pending", {}),
                      "completed_count": len(state.get("completed", []))}, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="KOTR<->Gir bidirectional handshake gateway")
    sub = p.add_subparsers(dest="cmd", required=True)

    def add_common(sp: argparse.ArgumentParser, channel: bool = True) -> None:
        sp.add_argument("--token-env", default=None, help="env var name holding the bot token")
        sp.add_argument("--allow-clawhip", action="store_true",
                        help="read-only fallback to the clawhip GIR token (probe/whoami/experiments)")
        if channel:
            sp.add_argument("--channel", default=KOTR_BUILDERS_CHANNEL)

    sp = sub.add_parser("selftest"); sp.set_defaults(func=cmd_selftest)
    sp = sub.add_parser("probe"); add_common(sp); sp.set_defaults(func=cmd_probe)
    sp = sub.add_parser("whoami"); add_common(sp, channel=False); sp.set_defaults(func=cmd_whoami)
    sp = sub.add_parser("initiate"); add_common(sp); sp.set_defaults(func=cmd_initiate)
    sp = sub.add_parser("once"); add_common(sp); sp.set_defaults(func=cmd_once)
    sp = sub.add_parser("run-loop"); add_common(sp)
    sp.add_argument("--interval-seconds", type=int, default=6); sp.set_defaults(func=cmd_run_loop)
    sp = sub.add_parser("status"); sp.set_defaults(func=cmd_status)
    return p


def main() -> int:
    args = build_parser().parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
