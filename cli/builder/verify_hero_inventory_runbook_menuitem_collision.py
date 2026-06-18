#!/usr/bin/env python3
"""
verify_hero_inventory_runbook_menuitem_collision.py
================================================================================
KOTR Hero-Inventory · runbook PROSE ↔ LIVE-EXTRACT binder for **Integration-
correction #2 — the menu-item rawcode collision sweep (`I200`–`I204` / `I100` /
`I005`).**

WHY THIS GATE EXISTS (a real, uncovered seam — the twin of the #3 binder)
--------------------------------------------------------------------------------
`hero_inventory_APPLY_RUNBOOK.md` (Integration-correction re-verification log,
bullet #2) tells the WE operator which menu-item rawcodes are FREE to create in
the Object Editor and which are already live:

  * `'I200'`…`'I204'` (the production hub set) and `'I100'` (the P1-spike throwaway)
    are claimed `grep -c` = **0** in the live map → safe for Evan to create.
  * `'I005'` is claimed **3 live uses** — a real gameplay item (Arthur's, on the
    save-whitelist) → it must NOT be reused for the hub, or the Object-Editor
    create silently collides with a shipping item.

Those are LIVE-MAP collision facts, but they live in **prose no gate parses**:

  * `verify_anchors.py` machine-checks the structured CURRENT anchors inside the
    PASTEREADY fix files — NOT these runbook collision cites.
  * pjass / the 178-sweep compile the pastes; they never read the runbook prose.
  * the sibling gate `verify_hero_inventory_runbook_desync2_anchors.py` covers
    correction **#3** (DESYNC2 line anchors) — it does NOT touch #2's rawcodes.

So the moment the live extract drifts (a WE re-bake adds/removes an item, or
re-stamps a rawcode — the exact staleness class that already bit B4b, see
`STALE_RUNBOOK_B4B_RECONCILED_CERT`), the runbook would keep telling the operator
"`I005` is taken, the rest are free" while the live map disagrees — a SILENT
stale-runbook brick that either collides a real item or wastes a free slot.

WHAT IT CHECKS (read-only; touches no .w3x and no shippable .j)
--------------------------------------------------------------------------------
  1. The live canonical extract still hashes to the md5 the runbook pins
     (a re-bake is caught immediately, before any per-cite check can false-pass).
  2. Collision counts: each rawcode's live `grep -c` (matching-line count, the
     same semantics the runbook quotes) equals the runbook-claimed count
     (`I200`–`I204`/`I100` = 0, `I005` = 3).
  3. For each of the 3 `'I005'` live uses: the cited live line carries the claimed
     token BYTE-EXACT, AND the runbook prose still cites that exact `L<n>` —
     binding prose ↔ live-extract in BOTH directions.

Exit 0 only if md5 matches AND every collision count AND every I005 line anchor
holds on both sides.

Run:        python3 verify_hero_inventory_runbook_menuitem_collision.py
Self-test:  python3 verify_hero_inventory_runbook_menuitem_collision.py --selftest
            (flips one collision count + drifts one live line + drops one runbook
             cite in in-memory copies, proves each is caught — teeth non-vacuous)
"""
import hashlib
import sys
from pathlib import Path

EXTRACT = Path.home() / "Warcraft III" / "KOTR" / "_extract_v050" / "war3map.j"
RUNBOOK = Path.home() / "Warcraft III" / "KOTR" / "_crew" / "hero_inventory_APPLY_RUNBOOK.md"

# the md5 the runbook pins the canonical extract to (Integration log header)
RUNBOOK_CLAIMED_MD5 = "967131658fd8d4fb27ee0d7f74e4bd22"

# Collision-sweep claims: (rawcode-as-it-appears-in-source, claimed grep -c count).
# grep -c counts MATCHING LINES, which is exactly the figure the runbook quotes.
COLLISIONS = [
    ("'I200'", 0),
    ("'I201'", 0),
    ("'I202'", 0),
    ("'I203'", 0),
    ("'I204'", 0),
    ("'I100'", 0),
    ("'I005'", 3),
]

# The 3 live 'I005' uses the runbook enumerates. Each:
# (label, 1-based live line, exact substring on that line, the `L<n>` cite the prose must carry).
I005_ANCHORS = [
    ("I005 save-whitelist",   44983, "set udg_SaveItemType[1]='I005'",            "L44983"),
    ("I005 given to Arthur",  49284, "call UnitAddItemByIdSwapped('I005'",        "L49284"),
    ("I005 removed",          65523, "call RemoveItem(GetItemOfTypeFromUnitBJ(udg_Arthur, 'I005')", "L65523"),
]


def count_lines(extract_lines, needle):
    """grep -c semantics: number of lines that contain the needle."""
    return sum(1 for ln in extract_lines if needle in ln)


def audit_collisions(extract_lines):
    """Return list of (rawcode, claimed, actual, ok)."""
    rows = []
    for code, claimed in COLLISIONS:
        actual = count_lines(extract_lines, code)
        rows.append((code, claimed, actual, actual == claimed))
    return rows


def audit_anchors(extract_lines, runbook_text):
    """Return list of (label, live_ok, prose_ok, detail)."""
    rows = []
    for label, lineno, token, cite in I005_ANCHORS:
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


def report(col_rows, anc_rows):
    print(f"{'RAWCODE':<10}{'CLAIM':<7}{'LIVE':<7}{'OK'}")
    for code, claimed, actual, ok in col_rows:
        print(f"{code:<10}{claimed:<7}{actual:<7}{'OK' if ok else 'COLLIDE'}")
    print()
    print(f"{'I005 ANCHOR':<24}{'LIVE':<7}{'PROSE':<7}")
    for label, live_ok, prose_ok, detail in anc_rows:
        print(f"{label:<24}{'OK' if live_ok else 'DRIFT':<7}{'OK' if prose_ok else 'DRIFT':<7}"
              + (f"  -> {detail}" if detail else ""))


def selftest():
    print("=== SELFTEST: flip a collision count + drift a live line + drop a runbook cite ===")
    # synthetic in-memory copies that satisfy every claim...
    lines = ["x"] * 70000
    runbook = ""
    # place the I005 anchors
    for _, lineno, token, cite in I005_ANCHORS:
        lines[lineno - 1] = "    " + token + " // INLINED"
        runbook += cite + " "
    # the 3 I005 anchor lines already give 3 'I005' occurrences; I200-I204/I100 stay 0
    base_cols = audit_collisions(lines)
    base_ancs = audit_anchors(lines, runbook)
    assert all(r[3] for r in base_cols), "baseline collision counts should all match"
    assert all(r[1] and r[2] for r in base_ancs), "baseline anchors should all pass"

    # 1) FLIP a collision count (simulate a re-bake that creates an 'I200' item live)
    bad_lines = list(lines)
    bad_lines[100] = "    call UnitAddItemByIdSwapped('I200', u) // re-bake added I200"
    cols1 = audit_collisions(bad_lines)
    caught_collision = any(code == "'I200'" and not ok for code, _, _, ok in cols1)

    # 2) DRIFT a live I005 line (re-bake shifted the save-whitelist off L44983)
    bad_lines2 = list(lines)
    bad_lines2[44983 - 1] = "    set udg_SaveItemType[1]='I006' // re-stamped"
    ancs1 = audit_anchors(bad_lines2, runbook)
    caught_live = any((not r[1]) and "L44983" in r[3] for r in ancs1)

    # 3) DROP a runbook cite (operator edited the prose, live unchanged)
    bad_runbook = runbook.replace("L65523 ", "")
    ancs2 = audit_anchors(lines, bad_runbook)
    caught_prose = any((not r[2]) and "L65523" in r[3] for r in ancs2)

    print(f"  collision-flip caught : {caught_collision}")
    print(f"  live-drift caught     : {caught_live}")
    print(f"  prose-drop caught     : {caught_prose}")
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
              "every collision count + cite below is now suspect. Re-ground #2 against the new bake.")
        return 1

    extract_lines = raw.decode("latin-1").split("\n")
    runbook_text = RUNBOOK.read_text()
    col_rows = audit_collisions(extract_lines)
    anc_rows = audit_anchors(extract_lines, runbook_text)
    report(col_rows, anc_rows)

    col_fail = [(c, claimed, actual) for c, claimed, actual, ok in col_rows if not ok]
    anc_fail = [(label, detail) for label, lo, po, detail in anc_rows if not (lo and po)]
    print(f"\ncollision checks={len(col_rows)} (fail={len(col_fail)})  "
          f"I005 anchors={len(anc_rows)} (fail={len(anc_fail)})  md5=OK")
    if col_fail or anc_fail:
        print("RESULT: FAIL — runbook menu-item integration-correction #2 has drifted:")
        for c, claimed, actual in col_fail:
            print(f"  - collision {c}: runbook claims grep -c={claimed}, live={actual}")
        for label, detail in anc_fail:
            print(f"  - {label}: {detail}")
        return 1
    print(f"RESULT: GREEN — all {len(col_rows)} collision counts (I200-I204/I100=free, I005=3 live) "
          f"and all {len(anc_rows)} I005 line anchors hold BYTE-EXACT vs live extract AND the runbook "
          "prose still cites every one. The Object-Editor create-set advice (#2) is intact.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
