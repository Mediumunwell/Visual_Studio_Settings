#!/usr/bin/env python3
"""
verify_companion_ai_phasefile_anchors.py — Companion-AI PHASE 1-5 file anchor binder
=====================================================================================
Binds the FIVE companion-AI implementation phase files —

    companion_ai_PHASE1_BRAIN_FLINGFIX.md      (the fling-fix + brain skeleton)
    companion_ai_PHASE2_CLIFF_STUCK_RECOVER.md (cliff / stuck recovery)
    companion_ai_PHASE3_TRAVEL_WAYPOINTS.md    (forward-leg travel waypoints)
    companion_ai_PHASE4_COMBAT_CASTING_RETREAT.md (combat / casting / HP-retreat)
    companion_ai_PHASE5_SHOP_BUYSELL.md        (shop buy/sell)

— to the live `_extract_v050/war3map.j`, BOTH directions. These five docs are the
per-phase build specs: each justifies its paste's integration points by pinning
byte-exact `war3map.j` line cites (the merchant rawcodes Arthur shops at, the
waypoint-rect coords he travels between, the Knockback mover that causes the
post-combat fling, the GetWidgetLife/BlzGetUnitMaxHP HP-fraction idiom the RETREAT
trigger reuses, …).

WHY THIS GATE EXISTS (covered by no other gate)
--------------------------------------------------------------------------------
The companion-AI track already has four binders, but each binds a DIFFERENT
artifact, and NONE reads the PHASE1-5 files' own live cites:
  * verify_companion_ai.py                      -> STAGED_COMBINED.j PARSES (pjass)
  * verify_companion_ai_fidelity.py             -> STAGED_COMBINED.j stays statement-
                                                   faithful to the phase SPECS
  * verify_companion_ai_phase0_recon_anchors.py -> binds PHASE0_RECON.md <-> live
  * verify_companion_ai_runbook_anchors.py      -> binds APPLY_RUNBOOK.md  <-> live
The PHASE1-5 files are the LIVING per-phase specs the runbook's pastes derive from,
yet their byte-exact line cites were machine-checked by nothing. A World-Editor save
renumbers JASS and shifts every cited line (the staleness class that already bit B4b
and the companion recon's GetTriggerPlayer count), silently turning a phase file into
a liar — "the merchant is created at L41011" while L41011 has drifted — and the next
operator pastes against a moved anchor. This binder makes that drift fail LOUD.

A grounding subtlety found while building this gate (2026-06-18, claude-p): PHASE1
cites the cliff STOP at L29066/L29067 (not the `onCliff` guard L29065, which the
PHASE2 doc + recon own), so L29065 is intentionally NOT a PHASE1 anchor here. The
PHASE3 prose renders the L25640 squared-distance idiom as `set dx = dx*dx + dy*dy`,
while the live bytes are `set dx=dx * dx + dy * dy` (spaces around `*`); the idiom is
genuinely at L25640, so the anchor binds the ACTUAL live bytes (not the prose's
reformatted rendering). Same for coords/facing the prose abbreviates (`270.0` vs live
`270.000`): the forward anchor binds the live string; the reverse check binds the
`L<n>` cite the prose must keep.

WHAT IT CHECKS (read-only; touches no .w3x and no shippable .j)
--------------------------------------------------------------------------------
source identity   md5 == 967131658fd8…, lines == 75535 (the canonical v0.50 extract)
For every anchor in ANCHORS, BOTH directions must hold:
  1. FORWARD (live):  the extract's cited 1-based line carries ALL claimed tokens
     byte-exact (a WE re-bake that moves the line is caught); AND
  2. REVERSE (prose): the OWNING phase file still carries that exact `L<n>` cite
     (a doc edit that drops/rewrites the cite is caught).

No phase-file md5 pin: phase files are LIVING paste sources, so line-level cite drift
(not a whole-file hash) is the signal that matters — the live extract IS md5-pinned,
and the phase prose is what is kept honest. Sibling of
verify_hero_inventory_runbook_phasefile_anchors.py (the hero-inv phase-file binder).

Run:        python3 verify_companion_ai_phasefile_anchors.py
Self-test:  python3 verify_companion_ai_phasefile_anchors.py --selftest
            (synthetic extract + phase texts that pass every anchor, then drift one
             live line and drop one prose cite; both must be caught)

EXIT 0 = GREEN, 1 = an anchor drifted, 2 = source/phase file not found, 3 = selftest.
Standalone by design — NOT wired into verify_all.py, so the canonical 178/178 sweep is
unchanged; invoked on its own when a phase file is touched or after any WE re-extract.
"""
import hashlib
import sys
from pathlib import Path

ROOT = Path("/mnt/c/Users/Morph/OneDrive/Documents/Warcraft III/Maps/KOTR")
SRC = ROOT / "_extract_v050" / "war3map.j"
CREW = ROOT / "_crew"

CANON_MD5 = "967131658fd8d4fb27ee0d7f74e4bd22"
CANON_LINES = 75535

PHASE_FILES = {
    "P1": CREW / "companion_ai_PHASE1_BRAIN_FLINGFIX.md",
    "P2": CREW / "companion_ai_PHASE2_CLIFF_STUCK_RECOVER.md",
    "P3": CREW / "companion_ai_PHASE3_TRAVEL_WAYPOINTS.md",
    "P4": CREW / "companion_ai_PHASE4_COMBAT_CASTING_RETREAT.md",
    "P5": CREW / "companion_ai_PHASE5_SHOP_BUYSELL.md",
}

# Each anchor: (cid, phase-key, 1-based live line, [tokens ALL byte-exact on that
# live line], the `L<n>` cite literal the OWNING phase file's prose must carry).
ANCHORS = [
    # ---- PHASE 1: fling-fix root cause in the Knockback mover -----------------
    ("p1.kbtimer",   "P1",  5009, ["s__Knockback_timer"],                                  "L5009"),
    ("p1.kbperiod",  "P1",  5011, ["s__Knockback_period"],                                 "L5011"),
    ("p1.kbdur",     "P1",  5021, ["real array s__Knockback_duration"],                    "L5021"),
    ("p1.onperiod",  "P1", 29027, ["s__Knockback_onPeriod"],                               "L29027"),
    ("p1.guard",     "P1", 29038, ["s__Knockback_duration[this] > 0 and UnitAlive("],      "L29038"),
    ("p1.cliffidiom","P1", 29066, ["GetTerrainCliffLevel"],                                "L29066"),
    ("p1.stopcoll",  "P1", 29051, ["set s__Knockback_duration[this]=0"],                   "L29051"),
    ("p1.stopcliff", "P1", 29067, ["set s__Knockback_duration[this]=0"],                   "L29067"),
    ("p1.stopdest",  "P1", 29022, ["set s__Knockback_duration[this]=0"],                   "L29022"),
    # ---- PHASE 2: stop/move/teleport order precedents + cooldown + spawn rect --
    ("p2.stop1",     "P2", 10963, ["IssueImmediateOrder", '"stop"'],                       "L10963"),
    ("p2.stop2",     "P2", 29192, ["IssueImmediateOrder", '"stop"'],                       "L29192"),
    ("p2.move1",     "P2", 12442, ["IssuePointOrder", '"move"'],                           "L12442"),
    ("p2.move2",     "P2", 29226, ["IssuePointOrder", '"move"'],                           "L29226"),
    ("p2.cdmissile", "P2", 29914, ["BlzGetUnitAbilityCooldownRemaining"],                  "L29914"),
    ("p2.setpos",    "P2", 28400, ["SetUnitPosition"],                                     "L28400"),
    ("p2.dash",      "P2",  1140, ["'DDas'"],                                              "L1140"),
    ("p2.spawnset",  "P2", 42919, ["set gg_rct_Arthur_Kay_Lancelot_Appear=Rect(4288.0, 10272.0, 4704.0, 10560.0)"], "L42919"),
    ("p2.spawnuse",  "P2", 45264, ["gg_rct_Arthur_Kay_Lancelot_Appear"],                   "L45264"),
    ("p2.skillloca", "P2",  2022, ["location array udg_skill_loca"],                       "L2022"),
    ("p2.cdflurry",  "P2", 32043, ["BlzGetUnitAbilityCooldownRemaining(udg_Arthur"],       "L32043"),
    ("p2.cddrachen", "P2", 32054, ["BlzGetUnitAbilityCooldownRemaining(udg_Arthur"],       "L32054"),
    # ---- PHASE 3: forward-leg waypoint rects (decl + set coords) + arrival idiom
    ("p3.dapp",      "P3",  2939, ["rect gg_rct_Arthur_Kay_Lancelot_Appear= null"],        "L2939"),
    ("p3.dc1",       "P3",  2940, ["rect gg_rct_Arthur_Move_to_Camelot_1= null"],          "L2940"),
    ("p3.dc2",       "P3",  2941, ["rect gg_rct_Arthur_Move_to_Camelot_2= null"],          "L2941"),
    ("p3.dgal",      "P3",  2963, ["rect gg_rct_Galahad= null"],                           "L2963"),
    ("p3.drka",      "P3",  3038, ["rect gg_rct_Red_Knight_Arena= null"],                  "L3038"),
    ("p3.daoc",      "P3",  3061, ["rect gg_rct_Assault_On_Camelot_Spawn= null"],          "L3061"),
    ("p3.sapp",      "P3", 42919, ["set gg_rct_Arthur_Kay_Lancelot_Appear=Rect(4288.0, 10272.0, 4704.0, 10560.0)"], "L42919"),
    ("p3.sc2",       "P3", 42921, ["set gg_rct_Arthur_Move_to_Camelot_2=Rect(4352.0, 10080.0, 4448.0, 10176.0)"],    "L42921"),
    ("p3.sc1",       "P3", 42920, ["set gg_rct_Arthur_Move_to_Camelot_1=Rect(4608.0, 10112.0, 4704.0, 10208.0)"],    "L42920"),
    ("p3.saoc",      "P3", 43057, ["set gg_rct_Assault_On_Camelot_Spawn=Rect(4352.0, 7168.0, 4736.0, 7392.0)"],      "L43057"),
    ("p3.srka",      "P3", 43034, ["set gg_rct_Red_Knight_Arena=Rect(5344.0, - 9120.0, 6944.0, - 8192.0)"],          "L43034"),
    ("p3.sgal",      "P3", 42951, ["set gg_rct_Galahad=Rect(- 6080.0, 5696.0, - 5952.0, 5824.0)"],                   "L42951"),
    ("p3.sqdist",    "P3", 25640, ["set dx=dx * dx + dy * dy"],                             "L25640"),
    ("p3.sqrt",      "P3", 26208, ["SquareRoot(dx * dx + dy * dy)"],                        "L26208"),
    ("p3.movefear1", "P3", 29269, ["IssuePointOrder", '"move"'],                           "L29269"),
    ("p3.movefear2", "P3", 29283, ["IssuePointOrder", '"move"'],                           "L29283"),
    # ---- PHASE 4: ability ids, spell-event cond, attack/HP/retreat idioms ------
    ("p4.spsu",      "P4",  1369, ["constant integer SpiritSurge___ABILITY= 'SPSU'"],      "L1369"),
    ("p4.flurry",    "P4",  1373, ["'A003'"],                                              "L1373"),
    ("p4.drachen",   "P4",  1375, ["'A01F'"],                                              "L1375"),
    ("p4.dash",      "P4",  1140, ["'DDas'"],                                              "L1140"),
    ("p4.spellcond", "P4", 52291, ["GetSpellAbilityId() == 'A01F'"],                       "L52291"),
    ("p4.cdmissile", "P4", 29914, ["BlzGetUnitAbilityCooldownRemaining"],                  "L29914"),
    ("p4.cdarthur",  "P4", 32043, ["BlzGetUnitAbilityCooldownRemaining(udg_Arthur"],       "L32043"),
    ("p4.attacktgt", "P4", 61280, ["IssueTargetOrderBJ", '"attack"'],                      "L61280"),
    ("p4.attackpt",  "P4", 59218, ["IssuePointOrderLocBJ", '"attack"'],                    "L59218"),
    ("p4.life1",     "P4",  6207, ["GetWidgetLife"],                                       "L6207"),
    ("p4.life2",     "P4",  6439, ["GetWidgetLife"],                                       "L6439"),
    ("p4.maxhp",     "P4", 24186, ["BlzGetUnitMaxHP"],                                     "L24186"),
    # ---- PHASE 5: shop merchants (rawcode + coords), pawn, gold, range idiom ---
    ("p5.ngme",      "P5", 41011, ["'ngme', 5824.0, 6144.0"],                              "L41011"),
    ("p5.nmrk",      "P5", 41032, ["'nmrk', 4928.0, 6208.0"],                              "L41032"),
    ("p5.mkt0250",   "P5", 42610, ["set gg_unit_nmrk_0250=BlzCreateUnitWithSkin(p, 'nmrk', 8064.0, - 10560.0"], "L42610"),
    ("p5.pawn",      "P5", 70181, ["EVENT_PLAYER_UNIT_PAWN_ITEM"],                         "L70181"),
    ("p5.sold",      "P5", 70100, ["GetItemTypeId(GetSoldItem()) == 'I00D'"],              "L70100"),
    ("p5.additem",   "P5", 41089, ["UnitAddItemToSlotById"],                               "L41089"),
    ("p5.gold",      "P5", 48696, ["AdjustPlayerStateBJ"],                                 "L48696"),
    ("p5.setgold",   "P5", 27458, ["SetPlayerState(whichPlayer, PLAYER_STATE_RESOURCE_GOLD"], "L27458"),
    ("p5.readgold",  "P5", 45488, ["GetPlayerState(GetTriggerPlayer(), PLAYER_STATE_RESOURC"], "L45488"),
    ("p5.dist",      "P5", 48024, ["DistanceBetweenPoints"],                               "L48024"),
]


def line_at(lines, lineno):
    return lines[lineno - 1] if 0 < lineno <= len(lines) else "<<EOF>>"


def audit(extract_lines, phase_texts, src_md5=None):
    """Return (rows, failures). rows=[(cid, phase, live_ok, prose_ok, detail)]."""
    rows, failures = [], []

    if src_md5 is not None:
        ok = src_md5 == CANON_MD5
        rows.append(("src.md5", "-", ok, True, "" if ok else f"md5 {src_md5} != {CANON_MD5}"))
        if not ok:
            failures.append(f"src.md5: extract md5 {src_md5} != pinned {CANON_MD5}")
    nlines = len(extract_lines) - 1 if extract_lines and extract_lines[-1] == "" else len(extract_lines)
    if src_md5 is not None:
        ok = nlines == CANON_LINES
        rows.append(("src.lines", "-", ok, True, "" if ok else f"{nlines} != {CANON_LINES}"))
        if not ok:
            failures.append(f"src.lines: extract has {nlines} lines, pinned {CANON_LINES}")

    for cid, pkey, lineno, tokens, cite in ANCHORS:
        live = line_at(extract_lines, lineno)
        missing = [t for t in tokens if t not in live]
        live_ok = not missing
        prose_ok = cite in phase_texts[pkey]
        detail = ""
        if not live_ok:
            detail = f"{pkey} live L{lineno} missing {missing!r} -> {live.strip()[:70]!r}"
        elif not prose_ok:
            detail = f"{pkey} prose no longer cites {cite!r}"
        rows.append((cid, pkey, live_ok, prose_ok, detail))
        if not (live_ok and prose_ok):
            failures.append(f"{cid}: {detail}")
    return rows, failures


def report(rows):
    print(f"{'ANCHOR':<14}{'PH':<4}{'LIVE':<7}{'PROSE':<7}DETAIL")
    for cid, pkey, live_ok, prose_ok, detail in rows:
        print(f"{cid:<14}{pkey:<4}{('OK' if live_ok else 'DRIFT'):<7}"
              f"{('OK' if prose_ok else 'DRIFT'):<7}{detail}")


def _build_synth():
    """Synthetic extract lines + phase texts that PASS every anchor (md5 skipped)."""
    base = ["x"] * CANON_LINES
    for _cid, _pk, lineno, tokens, _cite in ANCHORS:
        base[lineno - 1] = "    " + " ".join(tokens)
    phase_texts = {k: "" for k in PHASE_FILES}
    for _cid, pkey, _ln, _tok, cite in ANCHORS:
        if cite not in phase_texts[pkey]:
            phase_texts[pkey] += cite + " "
    return base, phase_texts


def selftest():
    print("=== SELFTEST: synthetic baseline GREEN, then drift one live line + drop one cite ===")
    ok_all = True

    base, phase_texts = _build_synth()
    _rows, failures = audit(base + [""], phase_texts, src_md5=None)
    clean_ok = (len(failures) == 0)
    print(f"  clean synthetic: ALL anchors GREEN both ways? {clean_ok}")
    if not clean_ok:
        for f in failures[:6]:
            print("   - unexpected:", f)
    ok_all &= clean_ok

    # (A) DRIFT a live line — the merchant moved off L41011
    bad = list(base)
    bad[41011 - 1] = "    set u=BlzCreateUnitWithSkin(p, 'OTHER', 0.0, 0.0)"
    _r1, f1 = audit(bad + [""], phase_texts, src_md5=None)
    caught_live = any(x.startswith("p5.ngme:") and "live" in x for x in f1)
    print(f"  live-drift @L41011 caught? {caught_live}")

    # (B) DROP a prose cite — PHASE3 prose lost its L42920 waypoint cite
    bad_texts = dict(phase_texts)
    bad_texts["P3"] = phase_texts["P3"].replace("L42920 ", "")
    _r2, f2 = audit(base + [""], bad_texts, src_md5=None)
    caught_prose = any(x.startswith("p3.sc1:") and "prose" in x for x in f2)
    print(f"  prose-drop L42920 (P3) caught? {caught_prose}")

    # (C) multi-token anchor: dropping ONE of two tokens must fail (not all-or-nothing slip)
    bad2 = list(base)
    bad2[10963 - 1] = '    call IssueImmediateOrder(s__Missiles_source[this], "go")'  # has IssueImmediateOrder, lost "stop"
    _r3, f3 = audit(bad2 + [""], phase_texts, src_md5=None)
    caught_multi = any(x.startswith("p2.stop1:") for x in f3)
    print(f"  multi-token partial-match @L10963 caught? {caught_multi}")

    # (D) md5 pin engages
    _r4, f4 = audit(base + [""], phase_texts, src_md5="deadbeef")
    caught_md5 = any(x.startswith("src.md5:") for x in f4)
    print(f"  md5 mismatch caught? {caught_md5}")

    ok_all &= caught_live and caught_prose and caught_multi and caught_md5
    print(f"\nSELFTEST {'PASS' if ok_all else 'FAIL'}")
    return 0 if ok_all else 3


def main():
    if "--selftest" in sys.argv:
        return selftest()
    if not SRC.exists():
        print(f"FATAL: live source not found: {SRC}")
        return 2
    phase_texts = {}
    for key, path in PHASE_FILES.items():
        if not path.exists():
            print(f"FATAL: phase file not found: {path}")
            return 2
        phase_texts[key] = path.read_text(encoding="utf-8")

    raw = SRC.read_bytes()
    src_md5 = hashlib.md5(raw).hexdigest()
    text = raw.decode("utf-8", "surrogatepass").replace("\r\n", "\n")
    extract_lines = text.split("\n")

    rows, failures = audit(extract_lines, phase_texts, src_md5=src_md5)
    report(rows)

    n_anchor = len(ANCHORS)
    print(f"\nsource: {SRC}")
    print(f"phase files: {n_anchor} anchors across {len(PHASE_FILES)} phase docs")
    if failures:
        print(f"\nRESULT: FAIL — {len(failures)} anchor(s) drifted (live-extract and/or phase-prose):")
        for f in failures:
            print("  -", f)
        print("Re-ground the named phase file against the current war3map.j (or restore the "
              "dropped L<n> cite) before any paste builds on it.")
        return 1
    print(f"\nRESULT: GREEN — all {n_anchor} companion-AI PHASE1-5 file cites hold BYTE-EXACT at "
          f"the cited live line (md5 {CANON_MD5}, {CANON_LINES} lines) AND every owning phase "
          f"file still carries its L<n> cite (bound BOTH directions).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
