#!/usr/bin/env python3
"""
verify_hero_inventory_runbook_phasefile_anchors.py
================================================================================
KOTR Hero-Inventory · runbook PROSE <-> PHASE-FILE binder for the integration-
correction log's **phase-file line cites** (#2 menu-item raws, #3 Phase-5 co-ship).

WHY THIS GATE EXISTS (the LAST unbound seam — phase files, not the live extract)
--------------------------------------------------------------------------------
Three sibling binders already machine-check the runbook's integration-correction
log against the LIVE v0.50 extract:

  * #1 (Hearthstone clock)        -> verify_hero_inventory_runbook_hearthclock_anchors.py
  * #2 (menu-item raw collision)  -> verify_hero_inventory_runbook_menuitem_collision.py
  * #3 (Phase 5 co-ships DESYNC2) -> verify_hero_inventory_runbook_desync2_anchors.py

But the runbook's integration-correction log ALSO pins line cites into the named
**phase files** — and the runbook's own footer declares "Source of truth for each
paste block is the named phase file." Those phase-file cites were checked by NO
gate (the three siblings bind prose <-> the live *extract*; pjass / the 178-sweep
compile the pastes, never the runbook prose; `verify_anchors.py` reads the
structured CURRENT anchors inside the PASTEREADY fixes, not these phase-file
cites). So a routine edit to a phase file (the living paste source) shifts a cited
line and the runbook keeps telling the operator "PHASE1_SPIKE L143 = the I100
throwaway" while L143 has drifted elsewhere — a SILENT stale-runbook brick on the
copy-paste path, the exact staleness class that already bit B4b (see
`STALE_RUNBOOK_B4B_RECONCILED_CERT`).

GROUNDED FINDING THIS CYCLE (claude-p 2026-06-18): the cites were ALREADY stale.
The runbook said PHASE1_SPIKE L143 / PHASE7 L285 / PHASE5 L152/L161-163/L194; the
true current lines are PHASE1_SPIKE L152 / PHASE7 L418 / PHASE5 L171/L182/L224.
The runbook prose was re-grounded to these and this gate now binds them, so the
next drift fails LOUD instead of silently.

WHAT IT CHECKS (read-only; touches no .w3x and no shippable .j)
--------------------------------------------------------------------------------
For every cite in PHASE_ANCHORS, BOTH directions must hold:
  1. the named phase file at the cited 1-based line carries the claimed token(s)
     BYTE-EXACT (so a phase-file edit that shifts the line is caught); AND
  2. the runbook prose still carries that exact `PHASEx L<n>` cite (so a prose
     edit that drops/changes the cite is caught).

No phase-file md5 pin: phase files are LIVING paste sources, so line-level anchor
drift — not a whole-file hash — is the signal that matters (an md5 pin would red
on every unrelated phase edit). The runbook IS the thing being kept honest.

Exit 0 only if every cite holds in both directions.

Run:        python3 verify_hero_inventory_runbook_phasefile_anchors.py
Self-test:  python3 verify_hero_inventory_runbook_phasefile_anchors.py --selftest
            (drifts one phase line + drops one runbook cite in in-memory copies;
             both must be caught — proves the teeth are non-vacuous)

STANDALONE by design: prints RESULT and exits 1 on any drift, but is NOT wired
into verify_all.py, so the 178/178 static sweep is unchanged. Sibling of the
three existing runbook binders.
"""
import sys
from pathlib import Path

CREW = Path.home() / "Warcraft III" / "KOTR" / "_crew"
RUNBOOK = CREW / "hero_inventory_APPLY_RUNBOOK.md"

PHASE_FILES = {
    "PHASE6": CREW / "hero_inventory_PHASE6_MENUBUTTONS.md",
    "PHASE1_SPIKE": CREW / "hero_inventory_PHASE1_SPIKE.md",
    "PHASE7": CREW / "hero_inventory_PHASE7_ERRANTRY_QUESTLOG_HEARTH.md",
    "PHASE5": CREW / "hero_inventory_PHASE5_SAVELOAD.md",
}

# Each anchor: (label, phase-file key, 1-based line, [tokens that must ALL appear
# on that line byte-exact], the `PHASEx L<n>` cite the runbook prose must carry).
# These are the integration-correction log's phase-file cites, re-grounded to the
# current phase files 2026-06-18.
PHASE_ANCHORS = [
    # --- #2: menu-item rawcodes — production set (PHASE6) vs throwaway (P1) vs consume (P7)
    ("#2 P6 TALENTS=I200 (set top)",  "PHASE6", 84,
     ["constant integer MENU_ITEM_TALENTS", "'I200'"], "PHASE6 L84-88"),
    ("#2 P6 HEARTH=I204 (set end)",   "PHASE6", 88,
     ["constant integer MENU_ITEM_HEARTH", "'I204'"], "PHASE6 L84-88"),
    ("#2 P1-spike EQUIP=I100 throwaway", "PHASE1_SPIKE", 152,
     ["constant integer MENU_ITEM_EQUIPMENT", "'I100'"], "PHASE1_SPIKE L152"),
    ("#2 P7 consumes I203/I204",      "PHASE7", 418,
     ["MENU_ITEM_QUESTLOG='I203'", "MENU_ITEM_HEARTH='I204'"], "PHASE7 L418"),
    # --- #3: Phase-5 co-ship-with-DESYNC2 mandate (PHASE5)
    ("#3 P5 DESYNC2 section hdr",     "PHASE5", 171,
     ["Desync correctness", "DESYNC2"], "L171/L182/L224"),
    ("#3 P5 must be applied WITH",    "PHASE5", 182,
     ["must be applied **with** DESYNC2"], "L171/L182/L224"),
    ("#3 P5 Apply TOGETHER WITH",     "PHASE5", 224,
     ["Apply **together with**", "DESYNC2_loadslot_localization_PASTEREADY.j"], "L171/L182/L224"),
]


def line_at(lines, lineno):
    return lines[lineno - 1] if 0 < lineno <= len(lines) else "<<EOF>>"


def audit(phase_lines_by_key, runbook_text):
    """Return list of (label, phase_ok, prose_ok, detail)."""
    rows = []
    for label, pkey, lineno, tokens, cite in PHASE_ANCHORS:
        lines = phase_lines_by_key[pkey]
        live = line_at(lines, lineno)
        missing = [t for t in tokens if t not in live]
        phase_ok = not missing
        prose_ok = cite in runbook_text
        detail = ""
        if not phase_ok:
            detail = f"{pkey} L{lineno} = {live.strip()!r} (missing {missing!r})"
        elif not prose_ok:
            detail = f"runbook prose no longer cites {cite!r}"
        rows.append((label, phase_ok, prose_ok, detail))
    return rows


def report(rows):
    print(f"{'PHASE-FILE ANCHOR':<34}{'PHASE':<7}{'PROSE':<7}")
    for label, phase_ok, prose_ok, detail in rows:
        print(f"{label:<34}{'OK' if phase_ok else 'DRIFT':<7}{'OK' if prose_ok else 'DRIFT':<7}"
              + (f"  -> {detail}" if detail else ""))


def selftest():
    print("=== SELFTEST: drift one phase line + drop one runbook cite (both must be caught) ===")
    # synthetic in-memory copies that satisfy every cite both directions
    phase_lines = {k: ["x"] * 5000 for k in PHASE_FILES}
    runbook = ""
    for _, pkey, lineno, tokens, cite in PHASE_ANCHORS:
        phase_lines[pkey][lineno - 1] = "    " + " ".join(tokens) + " // INLINED"
        if cite not in runbook:
            runbook += cite + " "
    base = audit(phase_lines, runbook)
    assert all(r[1] and r[2] for r in base), "baseline anchors should all pass both ways"

    # 1) DRIFT a phase-file line (a phase edit shifted PHASE1_SPIKE's I100 decl off L152)
    bad_phase = {k: list(v) for k, v in phase_lines.items()}
    bad_phase["PHASE1_SPIKE"][152 - 1] = "    // moved away by an edit"
    rows1 = audit(bad_phase, runbook)
    caught_phase = any((not r[1]) and "PHASE1_SPIKE L152" in r[3] for r in rows1)

    # 2) DROP a runbook cite (operator edited the prose, phase files unchanged)
    bad_runbook = runbook.replace("PHASE7 L418 ", "")
    rows2 = audit(phase_lines, bad_runbook)
    caught_prose = any((not r[2]) and "PHASE7 L418" in r[3] for r in rows2)

    print(f"  phase-drift caught : {caught_phase}")
    print(f"  prose-drop caught  : {caught_prose}")
    ok = caught_phase and caught_prose
    print(f"\nSELFTEST {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 3


def main():
    if "--selftest" in sys.argv:
        return selftest()
    if not RUNBOOK.exists():
        print(f"FATAL: hero-inventory runbook not found: {RUNBOOK}")
        return 2
    phase_lines_by_key = {}
    for key, path in PHASE_FILES.items():
        if not path.exists():
            print(f"FATAL: phase file not found: {path}")
            return 2
        phase_lines_by_key[key] = path.read_text().split("\n")

    runbook_text = RUNBOOK.read_text()
    rows = audit(phase_lines_by_key, runbook_text)
    report(rows)

    fails = [(label, detail) for label, po, pro, detail in rows if not (po and pro)]
    print(f"\nphase-file anchors={len(rows)} (fail={len(fails)})")
    if fails:
        print("RESULT: FAIL — runbook phase-file cites have drifted from the named phase files:")
        for label, detail in fails:
            print(f"  - {label}: {detail}")
        return 1
    print(f"RESULT: GREEN — all {len(rows)} runbook phase-file cites (#2 menu-item raws "
          "PHASE6/PHASE1_SPIKE/PHASE7, #3 Phase-5 co-ship PHASE5) hold BYTE-EXACT at the "
          "cited line AND the runbook prose still cites each. The phase files (the paste "
          "source-of-truth) and the runbook agree.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
