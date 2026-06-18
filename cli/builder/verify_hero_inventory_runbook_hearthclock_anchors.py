#!/usr/bin/env python3
"""
verify_hero_inventory_runbook_hearthclock_anchors.py
================================================================================
KOTR Hero-Inventory · runbook PROSE <-> LIVE-EXTRACT binder for **Integration-
correction #1 — the Hearthstone cooldown clock (`udg_GameClock` does not exist).**

WHY THIS GATE EXISTS (a real, uncovered seam — the LAST unbound twin of #2/#3)
--------------------------------------------------------------------------------
`hero_inventory_APPLY_RUNBOOK.md` (Integration-correction re-verification log)
carries THREE grounded corrections. Two already have machine-checking binders:

  * #2 (menu-item rawcode collision) -> verify_hero_inventory_runbook_menuitem_collision.py
  * #3 (Phase 5 co-ships DESYNC2)    -> verify_hero_inventory_runbook_desync2_anchors.py

Correction **#1** was the ODD ONE OUT: it is re-verified IN PROSE (runbook L84-90,
"RESOLVED 2026-06-15") but NO gate parses its live anchors. #1 says PHASE7's
Hearthstone recall stamped its 120 s cooldown off `TimerGetElapsed(udg_GameClock)`,
but `udg_GameClock` **does not exist** in `war3map.j` (`grep -c = 0`) — a silently
broken clock. The fix: a self-contained one-shot `udg_HearthClock`; the runbook
proves the choice is safe by citing live facts about the timers it WON'T reuse:

  * `udg_GameClock`  grep -c **0**  (the non-existent broken clock — the whole bug)
  * `udg_HearthClock` grep -c **0** (no collision -> the chosen replacement is free)
  * `DDLib__GameElapsedTimer` decl L867, lazy `CreateTimer()` L25145, one-shot
    3-hour `TimerStart(...,10800.,false,null)` L25146, monotonic reads L25083 /
    throttle idiom L25126 (the *correct-reuse* alternative the runbook offers).
  * `udg_KOTR_StateTimer` **periodic** start L43541 (`...,30.00,true,...`) — the
    timer the runbook explicitly forbids reusing (its elapsed resets every 30 s).

Those are LIVE-MAP facts but they live in **prose no gate parses**:

  * `verify_anchors.py` machine-checks the structured CURRENT anchors inside the
    PASTEREADY fix files — NOT these runbook clock cites.
  * pjass / the 178-sweep compile the pastes; they never read the runbook prose.
  * the sibling gates cover #2 (rawcodes) and #3 (DESYNC2 lines) — neither touches
    #1's timer anchors.

So the moment the live extract drifts (a WE re-bake shifts line numbers, or a
re-save introduces a real `udg_GameClock`/`udg_HearthClock` global — the exact
staleness class that already bit B4b, see `STALE_RUNBOOK_B4B_RECONCILED_CERT`),
the runbook would keep telling the operator "use HearthClock, GameClock is absent,
DDLib timer is at L25146" while the live map disagrees — a SILENT stale-runbook
brick on the cooldown-correctness path. This binder closes that seam, making the
runbook's correction-#1 advice an EXECUTABLE gate. With #1+#2+#3 all bound, the
runbook's entire integration-correction log is now machine-checked end-to-end.

WHAT IT CHECKS (read-only; touches no .w3x and no shippable .j)
--------------------------------------------------------------------------------
  1. The live canonical extract still hashes to the md5 the runbook pins
     (a re-bake is caught immediately, before any per-cite check can false-pass).
  2. grep -c counts: `udg_GameClock` and `udg_HearthClock` each == claimed (0/0).
  3. For each of the 6 timer line anchors: the cited live line carries the claimed
     token BYTE-EXACT, AND the runbook prose still cites that exact `L<n>` —
     binding prose <-> live-extract in BOTH directions.

Exit 0 only if md5 matches AND both grep counts AND all 6 anchors hold both ways.

Run:        python3 verify_hero_inventory_runbook_hearthclock_anchors.py
Self-test:  python3 verify_hero_inventory_runbook_hearthclock_anchors.py --selftest
            (introduces a live udg_HearthClock collision + drifts one live line +
             drops one runbook cite in in-memory copies; all three must be caught)

STANDALONE by design: prints RESULT and exits 1 on any drift, but is NOT wired
into verify_all.py, so the 178/178 static sweep is unchanged. Sibling of the
two existing runbook binders; same EXTRACT/RUNBOOK/md5 constants.
"""
import hashlib
import sys
from pathlib import Path

EXTRACT = Path.home() / "Warcraft III" / "KOTR" / "_extract_v050" / "war3map.j"
RUNBOOK = Path.home() / "Warcraft III" / "KOTR" / "_crew" / "hero_inventory_APPLY_RUNBOOK.md"

# the md5 the runbook pins the canonical extract to (Integration log header)
RUNBOOK_CLAIMED_MD5 = "967131658fd8d4fb27ee0d7f74e4bd22"

# grep -c claims for correction #1: (needle, claimed matching-line count).
# Both clocks must be ABSENT (0): udg_GameClock = the broken non-existent clock
# (the whole bug); udg_HearthClock = the chosen self-contained replacement, which
# must stay collision-free or the operator's STEP-0 declare would double-declare.
GREP_CLAIMS = [
    ("udg_GameClock", 0),
    ("udg_HearthClock", 0),
]

# The 6 timer line anchors correction #1's prose cites to justify the clock choice.
# Each: (label, 1-based live line, exact substring on that line, the `L<n>` cite
# the prose must carry).
CLOCK_ANCHORS = [
    ("DDLib clock decl",        867,   "timer DDLib__GameElapsedTimer=null",                                   "L867"),
    ("DDLib clock read",        25083, "return TimerGetElapsed(DDLib__GameElapsedTimer)",                      "L25083"),
    ("DDLib throttle idiom",    25126, "TimerGetElapsed(DDLib__GameElapsedTimer)) - DDLib__RndElapsedTime",    "L25126"),
    ("DDLib lazy CreateTimer",  25145, "set DDLib__GameElapsedTimer=CreateTimer()",                            "L25145"),
    ("DDLib one-shot 3h start", 25146, "call TimerStart(DDLib__GameElapsedTimer, 10800., false, null)",        "L25146"),
    ("StateTimer periodic",     43541, "call TimerStart(udg_KOTR_StateTimer, 30.00, true, function KOTR_StateWriter_Tick)", "L43541"),
]


def count_lines(extract_lines, needle):
    """grep -c semantics: number of lines that contain the needle."""
    return sum(1 for ln in extract_lines if needle in ln)


def audit_greps(extract_lines):
    """Return list of (needle, claimed, actual, ok)."""
    rows = []
    for needle, claimed in GREP_CLAIMS:
        actual = count_lines(extract_lines, needle)
        rows.append((needle, claimed, actual, actual == claimed))
    return rows


def audit_anchors(extract_lines, runbook_text):
    """Return list of (label, live_ok, prose_ok, detail)."""
    rows = []
    for label, lineno, token, cite in CLOCK_ANCHORS:
        live = extract_lines[lineno - 1] if 0 < lineno <= len(extract_lines) else "<<EOF>>"
        live_ok = token in live
        prose_ok = cite in runbook_text
        detail = ""
        if not live_ok:
            detail = f"live L{lineno} = {live.strip()!r} (missing {token!r})"
        elif not prose_ok:
            detail = f"runbook prose no longer cites {cite}"
        rows.append((label, live_ok, prose_ok, detail))
    return rows


def report(grep_rows, anc_rows):
    print(f"{'GREP NEEDLE':<20}{'CLAIM':<7}{'LIVE':<7}{'OK'}")
    for needle, claimed, actual, ok in grep_rows:
        print(f"{needle:<20}{claimed:<7}{actual:<7}{'OK' if ok else 'DRIFT'}")
    print()
    print(f"{'CLOCK ANCHOR':<26}{'LIVE':<7}{'PROSE':<7}")
    for label, live_ok, prose_ok, detail in anc_rows:
        print(f"{label:<26}{'OK' if live_ok else 'DRIFT':<7}{'OK' if prose_ok else 'DRIFT':<7}"
              + (f"  -> {detail}" if detail else ""))


def selftest():
    print("=== SELFTEST: HearthClock collision + drift a live line + drop a runbook cite ===")
    # synthetic in-memory copies that satisfy every claim...
    lines = ["x"] * 76000
    runbook = ""
    for _, lineno, token, cite in CLOCK_ANCHORS:
        lines[lineno - 1] = "    " + token + " // INLINED"
        runbook += cite + " "
    # the DDLib/StateTimer anchor lines contain neither udg_GameClock nor
    # udg_HearthClock, so both grep counts are 0 at baseline.
    base_greps = audit_greps(lines)
    base_ancs = audit_anchors(lines, runbook)
    assert all(r[3] for r in base_greps), "baseline grep counts should all match (0/0)"
    assert all(r[1] and r[2] for r in base_ancs), "baseline anchors should all pass"

    # 1) INTRODUCE a live udg_HearthClock collision (re-save declared it for real ->
    #    the "free, safe to declare" claim breaks: grep -c flips 0 -> 1)
    bad_lines = list(lines)
    bad_lines[200] = "    timer udg_HearthClock=null // re-bake declared it live"
    greps1 = audit_greps(bad_lines)
    caught_collision = any(n == "udg_HearthClock" and not ok for n, _, _, ok in greps1)

    # 2) DRIFT a live anchor line (re-bake shifted the DDLib one-shot start off L25146)
    bad_lines2 = list(lines)
    bad_lines2[25146 - 1] = "    call TimerStart(DDLib__GameElapsedTimer, 7200., false, null) // re-stamped"
    ancs1 = audit_anchors(bad_lines2, runbook)
    caught_live = any((not r[1]) and "L25146" in r[3] for r in ancs1)

    # 3) DROP a runbook cite (operator edited the prose, live unchanged)
    bad_runbook = runbook.replace("L867 ", "")
    ancs2 = audit_anchors(lines, bad_runbook)
    caught_prose = any((not r[2]) and "L867" in r[3] for r in ancs2)

    print(f"  HearthClock-collision caught : {caught_collision}")
    print(f"  live-drift caught            : {caught_live}")
    print(f"  prose-drop caught            : {caught_prose}")
    ok = caught_collision and caught_live and caught_prose
    print(f"\nSELFTEST {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 3


def main():
    if "--selftest" in sys.argv:
        return selftest()
    if not EXTRACT.exists():
        print(f"FATAL: live extract not found: {EXTRACT}")
        return 2
    if not RUNBOOK.exists():
        print(f"FATAL: hero-inventory runbook not found: {RUNBOOK}")
        return 2

    raw = EXTRACT.read_bytes()
    md5 = hashlib.md5(raw).hexdigest()
    print(f"live extract : {EXTRACT}")
    print(f"  md5={md5}  (runbook pins {RUNBOOK_CLAIMED_MD5})")
    if md5 != RUNBOOK_CLAIMED_MD5:
        print("RESULT: FAIL — live extract md5 DRIFTED from the runbook-pinned hash; "
              "every grep count + cite below is now suspect. Re-ground #1 against the new bake.")
        return 1

    extract_lines = raw.decode("latin-1").split("\n")
    runbook_text = RUNBOOK.read_text()
    grep_rows = audit_greps(extract_lines)
    anc_rows = audit_anchors(extract_lines, runbook_text)
    report(grep_rows, anc_rows)

    grep_fail = [(n, claimed, actual) for n, claimed, actual, ok in grep_rows if not ok]
    anc_fail = [(label, detail) for label, lo, po, detail in anc_rows if not (lo and po)]
    print(f"\ngrep checks={len(grep_rows)} (fail={len(grep_fail)})  "
          f"clock anchors={len(anc_rows)} (fail={len(anc_fail)})  md5=OK")
    if grep_fail or anc_fail:
        print("RESULT: FAIL — runbook clock integration-correction #1 has drifted:")
        for n, claimed, actual in grep_fail:
            print(f"  - grep {n}: runbook claims grep -c={claimed}, live={actual}")
        for label, detail in anc_fail:
            print(f"  - {label}: {detail}")
        return 1
    print(f"RESULT: GREEN — udg_GameClock/udg_HearthClock both absent (0/0) and all "
          f"{len(anc_rows)} timer line anchors (DDLib decl/read/throttle/CreateTimer/one-shot "
          "start, StateTimer periodic) hold BYTE-EXACT vs live extract AND the runbook prose "
          "still cites every one. The Hearthstone-clock correction-#1 advice is intact.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
