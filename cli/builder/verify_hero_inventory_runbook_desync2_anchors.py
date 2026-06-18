#!/usr/bin/env python3
"""
verify_hero_inventory_runbook_desync2_anchors.py
================================================================================
KOTR Hero-Inventory · runbook PROSE ↔ LIVE-EXTRACT anchor binder for the single
most safety-critical integration correction in the whole track: **#3 — Phase 5
must co-ship the DESYNC2 load-path fix.**

WHY THIS GATE EXISTS (a real, uncovered seam)
--------------------------------------------------------------------------------
`hero_inventory_APPLY_RUNBOOK.md` (Integration-correction re-verification log,
bullet #3) tells the WE operator that 7 live-source `war3map.j` anchors were
"re-read BYTE-EXACT" — these anchors are the entire argument for shipping
Phase 5 *together with* `DESYNC2_loadslot_localization_PASTEREADY.j` (the ungated
file-read that desyncs on load). But those cites live in **prose** that no gate
parses:

  * `verify_anchors.py` machine-checks the 2 structured CURRENT anchors inside
    `DESYNC2_loadslot_localization_PASTEREADY.j` — NOT these 7 runbook cites.
  * pjass/the 178-sweep compile the pastes; they never read the runbook prose.

So the moment the live extract drifts (a WE re-bake / re-save shifts line
numbers — exactly the staleness class that already bit B4b, see
`STALE_RUNBOOK_B4B_RECONCILED_CERT`), the runbook would keep telling the operator
"L26874 = the gated BlzSendSyncData" while L26874 now points at something else —
a SILENT stale-runbook brick on the desync-critical path.

WHAT IT CHECKS (read-only; touches no .w3x and no shippable .j)
--------------------------------------------------------------------------------
  1. The live canonical extract still hashes to the md5 the runbook claims
     (a re-bake is caught immediately, before any per-line check can false-pass).
  2. For each of the 7 DESYNC2 integration anchors: the cited live line carries
     the claimed token BYTE-EXACT, AND the runbook prose still cites that exact
     `L<n>` — binding prose ↔ live-extract in BOTH directions.

Exit 0 only if md5 matches AND all 7 anchors hold on both sides.

Run:        python3 verify_hero_inventory_runbook_desync2_anchors.py
Self-test:  python3 verify_hero_inventory_runbook_desync2_anchors.py --selftest
            (drifts one live line + drops one runbook cite in in-memory copies,
             proves each is caught — teeth are non-vacuous)
"""
import hashlib
import sys
from pathlib import Path

EXTRACT = Path.home() / "Warcraft III" / "KOTR" / "_extract_v050" / "war3map.j"
RUNBOOK = Path.home() / "Warcraft III" / "KOTR" / "_crew" / "hero_inventory_APPLY_RUNBOOK.md"

# the md5 the runbook pins the canonical extract to (Integration log header)
RUNBOOK_CLAIMED_MD5 = "967131658fd8d4fb27ee0d7f74e4bd22"

# Each anchor: (label, 1-based live line, exact substring that MUST be on that
# line, the `L<n>` cite token the runbook prose MUST still carry). These are the
# 7 anchors enumerated in Integration-correction #3.
ANCHORS = [
    ("LoadSaveSlot gated sync-send",   26874, "call BlzSendSyncData",                        "L26874"),
    ("LoadSaveSlot range header",      26867, "else",                                        "L26867-26875"),
    ("GetTitle unguarded read",        45178, "s__SaveFile_getLines",                        "L45176-45186"),
    ("SaveCharToSlot local-only write",26896, "if ( GetLocalPlayer() == p ) then",           "L26896-26898"),
    ("OnLoad BlzGetTriggerSyncData",   26839, "BlzGetTriggerSyncData()",                     "L26839"),
    ("OnLoad SaveLoadEvent_Code set",  26845, "set udg_SaveLoadEvent_Code=data",             "L26845"),
    ("File_ReadEnabled global decl",    4068, "boolean s__File_ReadEnabled= false",          "L4068"),
    ("sibling safe= read-gate expr",   45193, "local boolean safe= ( s__File_ReadEnabled and GetLocalPlayer() == p )", "L45193"),
    ("-load self-gate calls LoadSaveSlot", 47098, "call LoadSaveSlot(GetTriggerPlayer()",    "L47095-47098"),
]


def audit(extract_lines, runbook_text):
    """Return list of (label, live_ok, prose_ok, detail)."""
    rows = []
    for label, lineno, token, cite in ANCHORS:
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


def report(rows):
    print(f"{'ANCHOR':<38}{'LIVE':<7}{'PROSE':<7}")
    for label, live_ok, prose_ok, detail in rows:
        print(f"{label:<38}{'OK' if live_ok else 'DRIFT':<7}{'OK' if prose_ok else 'DRIFT':<7}"
              + (f"  -> {detail}" if detail else ""))


def selftest():
    print("=== SELFTEST: drift one live line + drop one runbook cite, prove both caught ===")
    # synthetic in-memory copies that satisfy every anchor...
    lines = ["x"] * 50000
    runbook = ""
    for _, lineno, token, cite in ANCHORS:
        lines[lineno - 1] = "    " + token + " // INLINED!!"
        runbook += cite + " "
    rows = audit(lines, runbook)
    assert all(r[1] and r[2] for r in rows), "baseline synthetic copy should pass all anchors"

    # 1) DRIFT a live line (simulate a re-bake shifting BlzSendSyncData off L26874)
    bad_lines = list(lines)
    bad_lines[26874 - 1] = "            endif // re-bake shifted the sync-send away"
    rows1 = audit(bad_lines, runbook)
    caught_live = any((not r[1]) and "BlzSendSyncData" in r[3] for r in rows1)

    # 2) DROP a runbook cite (operator edited the prose, live unchanged)
    bad_runbook = runbook.replace("L45193 ", "")
    rows2 = audit(lines, bad_runbook)
    caught_prose = any((not r[2]) and "L45193" in r[3] for r in rows2)

    print(f"  live-drift caught : {caught_live}")
    print(f"  prose-drop caught : {caught_prose}")
    ok = caught_live and caught_prose
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
              "every per-line cite below is now suspect. Re-ground #3 against the new bake.")
        return 1

    extract_lines = raw.decode("latin-1").split("\n")
    runbook_text = RUNBOOK.read_text()
    rows = audit(extract_lines, runbook_text)
    report(rows)
    failures = [(label, detail) for label, lo, po, detail in rows if not (lo and po)]
    print(f"\nanchors checked={len(rows)}  failures={len(failures)}  md5=OK")
    if failures:
        print("RESULT: FAIL — runbook DESYNC2 integration-correction #3 has drifted:")
        for label, detail in failures:
            print(f"  - {label}: {detail}")
        return 1
    print(f"RESULT: GREEN — all {len(rows)} line-level checks (covering the 7 named DESYNC2 #3 "
          "anchors) hold BYTE-EXACT vs live extract AND the runbook prose still cites every one. "
          "Phase-5 co-ship argument is intact.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
