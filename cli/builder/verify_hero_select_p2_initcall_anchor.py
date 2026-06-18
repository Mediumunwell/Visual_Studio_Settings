#!/usr/bin/env python3
"""
verify_hero_select_p2_initcall_anchor.py
================================================================================
KOTR Hero-Select REDESIGN (Track 4) · P2 STEP-1 INIT-CALL SITE <-> LIVE-EXTRACT binder.
Built 2026-06-18 by KOTR Builder (engine claude-p).

WHY THIS GATE EXISTS (the last un-grounded fact on the P2 apply path)
--------------------------------------------------------------------------------
The hero-select P2 apply path is now grounded end to end EXCEPT one seam:
  * STEP 0 (the 26 `CastleSlot_*` Variable-Editor vars) is gated both ways
    (`verify_castleslot_global_contract.py`, `verify_runbook_step0_coverage.py`),
  * STEP 1 (the `InitCastleSlotData` + announce + `ApplyPick` Map-Header paste) is
    assembled, real-pjass compiled, and runbook-bound
    (`verify_hero_select_p2_loop.py`, `..._runbook_anchors.py`),
  * ...but the runbook then says "call `InitCastleSlotData()` once at map init" and,
    until 2026-06-18, hand-waved the LOCATION as "the map's existing main/config init,
    alongside the other one-time table fills". An operator following that literally
    has NO idea which function or which line — and the ORDER is load-bearing:
    `InitGlobals()` zero-inits every GUI `udg_*` (the 26 `CastleSlot_*` arrays
    included), so `InitCastleSlotData()` MUST run after `InitGlobals()` (else the data
    is clobbered back to defaults) and before `InitCustomTriggers()` /
    `RunInitializationTriggers()` arm the pick triggers (else a pick can fire against
    empty data). Put it in the wrong spot and the redesign silently no-ops or bricks.

The runbook now names the exact site:
    function main:
        call InitGlobals()
        call InitCastleSlotData()   <-- the new line
        call InitCustomTriggers()
        call RunInitializationTriggers()
This gate binds that claim BOTH WAYS against the md5-pinned canonical extract, the
Track-4 twin of the existing runbook/recon/contract binders.

WHAT IT CHECKS (read-only; touches no .w3x and no shippable .j)
--------------------------------------------------------------------------------
  0. md5 pin: the live extract still hashes to the runbook's pinned md5 (a re-bake is
     caught before any per-anchor check can false-pass).
  1. anchor `main-exists`      : exactly one `function main takes nothing returns nothing`.
  2. anchor `initglobals-once` : exactly one whole-word `call InitGlobals()` in the extract
     (the insertion point is unambiguous only if there is a single one).
  3. anchor `init-call-block`  : the contiguous tail block
        call InitGlobals()
        call InitCustomTriggers()
        call RunInitializationTriggers()
     appears (in that order, that adjacency) exactly once, INSIDE main()'s span. This is
     the join the new line is inserted into; if a re-save reorders/splits it the runbook's
     "after InitGlobals, before InitCustomTriggers" instruction would be stale.
  4. anchor `initcastleslot-absent` : token `InitCastleSlotData` occurs 0× in the live
     extract (adding the call cannot double-define an existing symbol).  [SAFE-TO-ADD]
  5. reverse (prose) for each: the runbook STEP-1 body still names `function main`,
     `call InitGlobals()`, `call InitCastleSlotData()`, `call InitCustomTriggers()`, and
     states the "after InitGlobals / before InitCustomTriggers" ordering + the grep-0
     safe-to-add fact. (Binds the operator-facing body the operator actually follows.)

Exit 0 only if md5 matches AND every anchor holds in both directions.

Run:        python3 verify_hero_select_p2_initcall_anchor.py
Self-test:  python3 verify_hero_select_p2_initcall_anchor.py --selftest

Wired into the cli/builder aggregate sweep (verify_builder_gates.py); standalone vs the
fix_specs 178-sweep (touches no shippable paste).
"""
import hashlib
import re
import sys
from pathlib import Path

EXTRACT = Path.home() / "Warcraft III" / "KOTR" / "_extract_v050" / "war3map.j"
RUNBOOK = Path.home() / "Warcraft III" / "KOTR" / "_crew" / "hero_select_p2_APPLY_RUNBOOK.md"

# the md5 the runbook pins the canonical extract to (Grounding header)
RUNBOOK_CLAIMED_MD5 = "967131658fd8d4fb27ee0d7f74e4bd22"

MAIN_HDR = "function main takes nothing returns nothing"
MAIN_END = "\nendfunction"

# The three contiguous init calls main() ends with, in the order the runbook documents.
# The new `call InitCastleSlotData()` goes between calls[0] and calls[1].
INIT_CALLS = ["InitGlobals", "InitCustomTriggers", "RunInitializationTriggers"]
# adjacency block: each call on its own line, only whitespace around them, in order
BLOCK_RE = re.compile(
    r"call InitGlobals\(\)\s*\n\s*call InitCustomTriggers\(\)\s*\n\s*call RunInitializationTriggers\(\)"
)

NEW_CALL_TOKEN = "InitCastleSlotData"  # must be ABSENT in extract (safe to add)


def whole_word_count(text, token):
    return len(re.findall(r"(?<!\w)" + re.escape(token) + r"(?!\w)", text))


def main_span(extract_text):
    """Return (start_idx, end_idx) char offsets of function main's body, or None."""
    i = extract_text.find(MAIN_HDR)
    if i < 0:
        return None
    j = extract_text.find(MAIN_END, i)
    if j < 0:
        return None
    return (i, j + len(MAIN_END))


def audit(extract_text, runbook_body):
    """Return list of (anchor, live_ok, prose_ok, detail)."""
    rows = []
    span = main_span(extract_text)

    # 1. main exists exactly once
    n_main = extract_text.count(MAIN_HDR)
    live_main = n_main == 1
    rows.append((
        "main-exists",
        live_main,
        MAIN_HDR.replace(" takes nothing returns nothing", "") in runbook_body
        or "function main" in runbook_body,
        "" if live_main else f"`{MAIN_HDR}` count={n_main} (expected 1)",
    ))

    # 2. exactly one `call InitGlobals()`
    n_ig = whole_word_count(extract_text, "InitGlobals")
    # count only the *call* sites, not the function definition
    n_ig_call = len(re.findall(r"call InitGlobals\(\)", extract_text))
    live_ig = n_ig_call == 1
    rows.append((
        "initglobals-once",
        live_ig,
        "call InitGlobals()" in runbook_body,
        "" if live_ig else f"`call InitGlobals()` count={n_ig_call} (expected 1; total InitGlobals refs={n_ig})",
    ))

    # 3. the contiguous init-call block, in order, inside main()
    block_iter = list(BLOCK_RE.finditer(extract_text))
    n_block = len(block_iter)
    inside = False
    if n_block == 1 and span is not None:
        m = block_iter[0]
        inside = span[0] <= m.start() and m.end() <= span[1]
    live_block = n_block == 1 and inside
    # reverse: runbook documents the order (after InitGlobals, before InitCustomTriggers)
    prose_order = (
        "call InitCustomTriggers()" in runbook_body
        and re.search(r"after\s+`?call InitGlobals", runbook_body) is not None
        and re.search(r"before\s+`?call InitCustomTriggers", runbook_body) is not None
    )
    detail3 = ""
    if not live_block:
        if n_block != 1:
            detail3 = f"contiguous InitGlobals->InitCustomTriggers->RunInitializationTriggers block count={n_block} (expected 1)"
        elif span is None:
            detail3 = "function main span not found"
        elif not inside:
            detail3 = "init-call block is NOT inside function main's span"
    rows.append(("init-call-block", live_block, bool(prose_order), detail3))

    # 4. InitCastleSlotData absent in extract (safe to add)
    n_new = whole_word_count(extract_text, NEW_CALL_TOKEN)
    live_absent = n_new == 0
    prose_new = (
        f"call {NEW_CALL_TOKEN}()" in runbook_body
        and ("grep count 0" in runbook_body or "grep-0" in runbook_body
             or "does **not**\nexist" in runbook_body or "does **not** exist" in runbook_body)
    )
    rows.append((
        "initcastleslot-absent",
        live_absent,
        bool(prose_new),
        "" if live_absent else f"`{NEW_CALL_TOKEN}` already occurs {n_new}x in live extract (would double-define)",
    ))

    return rows


def runbook_body(runbook_text):
    """Operator-facing body — strip any trailing dated re-ground note so the reverse
    check binds the instruction the operator follows, not our own annotation."""
    return runbook_text.split("**Re-ground note —", 1)[0]


def report(rows):
    print(f"{'ANCHOR':<26}{'LIVE':<8}{'PROSE':<8}")
    for label, live_ok, prose_ok, detail in rows:
        print(f"{label:<26}{'OK' if live_ok else 'DRIFT':<8}{'OK' if prose_ok else 'DRIFT':<8}"
              + (f"  -> {detail}" if detail else ""))


def selftest():
    print("=== SELFTEST: synthetic baseline + per-anchor RED-catch (teeth) ===")
    # a synthetic extract that satisfies every LIVE anchor
    extract = (
        "function foo takes nothing returns nothing\n"
        "    set x = 1\n"
        "endfunction\n"
        + MAIN_HDR + "\n"
        "    call SetCameraBounds(0,0,0,0,0,0,0,0)\n"
        "    call InitGlobals()\n"
        "    call InitCustomTriggers()\n"
        "    call RunInitializationTriggers()\n"
        "endfunction\n"
        "function config takes nothing returns nothing\n"
        "endfunction\n"
    )
    # a runbook body that satisfies every REVERSE anchor
    runbook = (
        "in `function main`, on the line immediately after `call InitGlobals()` and "
        "before `call InitCustomTriggers()` add `call InitCastleSlotData()`. "
        "`InitCastleSlotData` does **not** exist anywhere in the live extract today "
        "(grep count 0), so adding the call introduces no double-definition. "
        "    call InitGlobals()\n    call InitCustomTriggers()\n"
    )

    base = audit(extract, runbook)
    base_ok = all(lo and po for _, lo, po, _ in base)
    print(f"  baseline all-green             : {base_ok}")
    assert base_ok, [r for r in base if not (r[1] and r[2])]

    # 1) main duplicated -> main-exists DRIFT
    bad = extract + "\n" + MAIN_HDR + "\nendfunction\n"
    caught_main = any(l == "main-exists" and not lo for l, lo, po, d in audit(bad, runbook))

    # 2) a second call InitGlobals() -> initglobals-once DRIFT
    bad = extract.replace("    call InitCustomTriggers()\n",
                          "    call InitGlobals()\n    call InitCustomTriggers()\n", 1)
    caught_ig = any(l == "initglobals-once" and not lo for l, lo, po, d in audit(bad, runbook))

    # 3) block split (a line inserted between the calls) -> init-call-block DRIFT
    bad = extract.replace("    call InitGlobals()\n",
                          "    call InitGlobals()\n    call SomethingElse()\n", 1)
    caught_block = any(l == "init-call-block" and not lo for l, lo, po, d in audit(bad, runbook))

    # 4) InitCastleSlotData already present -> initcastleslot-absent DRIFT
    bad = extract.replace("    call InitGlobals()\n",
                          "    call InitGlobals()\n    call InitCastleSlotData()\n", 1)
    caught_absent = any(l == "initcastleslot-absent" and not lo for l, lo, po, d in audit(bad, runbook))

    # 5) reverse: runbook drops the ordering prose -> init-call-block PROSE DRIFT
    bad_rb = runbook.replace("before `call InitCustomTriggers()`", "somewhere")
    caught_prose = any(l == "init-call-block" and not po for l, lo, po, d in audit(extract, bad_rb))

    print(f"  main-dup caught                : {caught_main}")
    print(f"  second-InitGlobals caught      : {caught_ig}")
    print(f"  block-split caught             : {caught_block}")
    print(f"  InitCastleSlot-present caught  : {caught_absent}")
    print(f"  ordering prose-drop caught     : {caught_prose}")
    ok = all([base_ok, caught_main, caught_ig, caught_block, caught_absent, caught_prose])
    print(f"\nSELFTEST {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 3


def main():
    if "--selftest" in sys.argv:
        return selftest()
    if not EXTRACT.exists():
        print(f"FATAL: live extract not found: {EXTRACT}")
        return 2
    if not RUNBOOK.exists():
        print(f"FATAL: hero-select P2 runbook not found: {RUNBOOK}")
        return 2

    raw = EXTRACT.read_bytes()
    md5 = hashlib.md5(raw).hexdigest()
    print(f"live extract : {EXTRACT}")
    print(f"  md5={md5}  (runbook pins {RUNBOOK_CLAIMED_MD5})")
    if md5 != RUNBOOK_CLAIMED_MD5:
        print("RESULT: FAIL — live extract md5 DRIFTED from the runbook-pinned hash; the "
              "init-call site below is now suspect. Re-ground the runbook against the new bake.")
        return 1

    extract_text = raw.decode("latin-1")
    body = runbook_body(RUNBOOK.read_text())
    rows = audit(extract_text, body)
    report(rows)

    fail = [(lbl, d) for lbl, lo, po, d in rows if not (lo and po)]
    fwd_ok = sum(1 for _, lo, _, _ in rows if lo)
    rev_ok = sum(1 for _, _, po, _ in rows if po)
    print(f"\nanchors={len(rows)}  forward(live)={fwd_ok}/{len(rows)}  "
          f"reverse(prose)={rev_ok}/{len(rows)}  md5=OK")
    if fail:
        print("RESULT: FAIL — hero-select P2 init-call site has drifted:")
        for lbl, d in fail:
            print(f"  - {lbl}: {d}")
        return 1
    print(f"RESULT: GREEN — all {len(rows)} init-call-site anchors hold vs the md5-pinned "
          "extract AND the runbook prose still names the exact site: `call InitCastleSlotData()` "
          "goes in `function main`, after the single `call InitGlobals()` and before the "
          "contiguous `call InitCustomTriggers()`/`call RunInitializationTriggers()` block; "
          "`InitCastleSlotData` is absent today (grep 0 — safe to add). The P2 STEP-1 init-call "
          "site is bound both ways — the apply path is now grounded end to end.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
