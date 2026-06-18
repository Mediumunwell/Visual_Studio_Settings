#!/usr/bin/env python3
"""pulse_ghost_detector.py — is the recurring "kotr-ai pulse (no analysis)" noise
coming from THIS laptop or a stale OFF-laptop clone?  Answer it in one command.

BACKGROUND (the provenance trap)
  The `kotr_ai_pulse.sh` posts on a 45-min cadence as the "KOTR (kotr-ai brain)"
  webhook identity.  A recurring failure variant — `(gir:latest returned no
  analysis — check the server / VRAM / model name.)` — kept polluting
  #kotr-ai-builders even after the LOCAL script was hardened twice, because the
  local script was healthy and never the culprit.  To make the real source
  self-identify, `2026-06-17 21:21Z` (`a571449`) stamped every pulse the current
  script emits with `src=<host>@<short-sha>` in BOTH the log header and the
  channel summary.  See STAGED_FOR_EVAN.md ("kotr-ai pulse … EXTERNAL stale
  source").

WHAT THIS PROVES
  Any "kotr-ai pulse" post that carries NO `src=` tag CANNOT have been produced
  by any current-HEAD script anywhere — it is a PRE-STAMP clone running off this
  laptop (cloud routine that can't reach 127.0.0.1:11434, or another fleet box on
  a 45-min timer).  This detector reads the channel, classifies every pulse post,
  and prints a verdict.  It turns the manual probe-read into a repeatable check so
  the next engine / Evan never has to re-derive it by hand.

CLASSES
  LOCAL        — has `src=<this-host>@…`  (the laptop's own healthy pulse)
  NAMED-OTHER  — has `src=<other-host>@…` (a DIFFERENT but stamped/current clone)
  FOREIGN      — NO `src=` at all         (pre-stamp stale clone = the ghost)

EXIT CODES
  0  no FOREIGN pulse in the window (channel clean of the ghost)
  2  >=1 FOREIGN pulse seen — actionable: the off-laptop ghost is still firing
     (fix lives in STAGED_FOR_EVAN.md: disable / one-time `git pull` on that box)
  3  could not read the channel (token / network) — a skip, not a verdict

POSTURE: read-only; reuses ../discord/read_channel.py for token + channel resolution.
"""
import json
import os
import re
import socket
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
READER = os.path.join(HERE, "..", "discord", "read_channel.py")
PULSE_MARK = "kotr-ai pulse"
SRC_RE = re.compile(r"src[=\s]+([A-Za-z0-9._-]+@[A-Za-z0-9._-]+)", re.IGNORECASE)


def this_host():
    return (socket.gethostname() or "unknown").strip()


def read_messages(limit):
    """Return a list of message dicts via the canonical reader, or None on failure."""
    try:
        out = subprocess.run(
            [sys.executable, READER, "--limit", str(limit), "--json"],
            capture_output=True, text=True, timeout=60,
        )
    except Exception as exc:  # noqa: BLE001 — any spawn failure is a skip
        print(f"SKIP — could not run reader: {exc}", file=sys.stderr)
        return None
    if out.returncode != 0:
        print(f"SKIP — reader exit {out.returncode}: {out.stderr.strip()[:200]}", file=sys.stderr)
        return None
    try:
        data = json.loads(out.stdout)
    except json.JSONDecodeError:
        print("SKIP — reader did not return JSON", file=sys.stderr)
        return None
    if isinstance(data, dict):
        if data.get("ok") is False:
            print(f"SKIP — reader error: {data}", file=sys.stderr)
            return None
        data = data.get("messages", [])
    return data if isinstance(data, list) else []


def classify(content, host):
    m = SRC_RE.search(content or "")
    if not m:
        return "FOREIGN", None
    origin = m.group(1)
    if origin.split("@", 1)[0].lower() == host.lower():
        return "LOCAL", origin
    return "NAMED-OTHER", origin


def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 25
    host = this_host()
    msgs = read_messages(limit)
    if msgs is None:
        return 3

    pulses = [m for m in msgs if PULSE_MARK in (m.get("content", "").lower())]
    if not pulses:
        print(f"GREEN — no 'kotr-ai pulse' posts in the last {limit} messages "
              f"(host={host}). Nothing to classify.")
        return 0

    foreign = 0
    print(f"=== pulse provenance — last {limit} msgs · this host = {host} ===")
    for m in sorted(pulses, key=lambda x: x.get("timestamp", "")):
        cls, origin = classify(m.get("content", ""), host)
        ts = m.get("timestamp", "?")[:19]
        if cls == "FOREIGN":
            foreign += 1
        tag = origin or "(no src= tag)"
        print(f"  {ts}  {cls:<11}  {tag}")

    print("-" * 60)
    if foreign:
        print(f"RED — {foreign} FOREIGN pulse(s) (no src= tag) = an OFF-laptop pre-stamp "
              f"clone is still firing. This laptop is NOT the source.")
        print("  → fix on the other box / cloud routine: see STAGED_FOR_EVAN.md "
              "(disable it, or one-time `git pull` so it self-heals).")
        return 2
    print("GREEN — every pulse post is stamped (LOCAL or NAMED-OTHER). "
          "No pre-stamp ghost in this window.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
