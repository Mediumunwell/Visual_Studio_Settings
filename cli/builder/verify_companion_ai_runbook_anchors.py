#!/usr/bin/env python3
"""
verify_companion_ai_runbook_anchors.py
================================================================================
KOTR Companion-AI · APPLY-RUNBOOK PROSE <-> LIVE-EXTRACT binder.

WHY THIS GATE EXISTS (a real, uncovered seam — the companion-AI twin of the
hero-inv runbook binders #1/#2/#3 + the companion-AI Phase-0 recon binder)
--------------------------------------------------------------------------------
`companion_ai_APPLY_RUNBOOK.md` is the single ordered checklist Evan follows to
land Arthur's autonomous brain in one World-Editor sitting. To justify each
paste's integration point it pins ~25 BYTE-EXACT `war3map.j` line cites — the
Arthur globals it depends on, the Knockback duration=0 stop-idiom the fling fix
copies, the cliff-level idiom, the three patrol rects, the move/attack order
precedents, the HP natives, the four ability rawcodes behind the cooldown gate,
the merchant units, and the pawn/gold precedents.

Those are LIVE-MAP facts but they live in **prose no gate parses**:

  * `verify_companion_ai.py` proves the assembled `STAGED_COMBINED.j` PARSES.
  * `verify_companion_ai_fidelity.py` proves it stays statement-faithful to the
    phase specs. Neither reads the runbook .md.
  * `verify_companion_ai_phase0_recon_anchors.py` binds the **recon** prose <->
    live — NOT this runbook's copies of the same/adjacent cites.
  * pjass / the 178-sweep compile the pastes; they never read the runbook prose.

So the moment the live extract drifts (a WE re-save renumbers JASS — the exact
staleness class that already bit B4b, see `STALE_RUNBOOK_B4B_RECONCILED_CERT`,
and that this very runbook had ALREADY suffered on two cites, below), the runbook
would keep telling the operator "the mover's stop-idiom is at L29044/L29061" or
"patrol rect gg_rct_Camelot_1 at (4656,10160)" while the live map disagrees — a
SILENT stale-runbook brick on the integration path. This binder closes that seam.

TWO CITES WERE STALE AT FIRST BIND (corrected in the runbook, dated 2026-06-18):
  * Knockback duration=0 **stop-idiom**: runbook said L29044/L29061 (those are
    `GroupEnumUnitsInRange`/`SetRect`) -> corrected to **L29022/L29051**, the real
    `set s__Knockback_duration[this]=0` lines the proven Phase-0 recon already cites.
  * third patrol rect: runbook named the NONEXISTENT `gg_rct_Camelot_1` ->
    corrected to **`gg_rct_Arthur_Move_to_Camelot_1`** (L42920); per the PHASE3
    source-of-truth the ring is Appear(L42919)->Camelot_2(L42921)->Camelot_1(L42920).
The other 23 cites verified byte-exact unchanged.

WHAT IT CHECKS (read-only; touches no .w3x and no shippable .j)
--------------------------------------------------------------------------------
  1. The live canonical extract still hashes to the md5 the runbook pins
     (a re-bake is caught immediately, before any per-cite check can false-pass).
  2. For each of the 25 line anchors: every claimed token is present on the cited
     live line BYTE-EXACT (forward), AND the runbook prose still carries the
     anchor's cite string (reverse) — binding prose <-> live-extract BOTH ways.

Exit 0 only if md5 matches AND all 25 anchors hold in both directions.

Run:        python3 verify_companion_ai_runbook_anchors.py
Self-test:  python3 verify_companion_ai_runbook_anchors.py --selftest

STANDALONE by design: prints RESULT and exits 1 on any drift, but is NOT wired
into verify_all.py, so the 178/178 static sweep is unchanged. Sibling of the
hero-inv runbook binders + the companion-AI Phase-0 recon binder; same
EXTRACT / md5 / both-ways-binding contract.
"""
import hashlib
import sys
from pathlib import Path

EXTRACT = Path.home() / "Warcraft III" / "KOTR" / "_extract_v050" / "war3map.j"
RUNBOOK = Path.home() / "Warcraft III" / "KOTR" / "_crew" / "companion_ai_APPLY_RUNBOOK.md"

# the md5 the runbook pins the canonical extract to (Grounding header)
RUNBOOK_CLAIMED_MD5 = "967131658fd8d4fb27ee0d7f74e4bd22"

# Each anchor: (label, 1-based live line, [tokens that must ALL be on that line
# byte-exact], cite string the runbook prose must still carry).
# Only LIVE `war3map.j` cites are bound here; cites into the assembled
# companion_ai_STAGED_COMBINED.j (the AI_sell* decls/reads, L55/56/57/249/...)
# belong to the compile/fidelity gates and are deliberately excluded.
ANCHORS = [
    # --- Arthur globals (STEP 0 / Phase 1 deps) ---
    ("udg_group Tornado clobber", 52880, ["set udg_group=GetUnitsInRangeOfLocMatching", "Trig_Tornado_Damage"], "L52880"),
    ("udg_Arthur decl",            1901, ["unit udg_Arthur= null"], "L1901"),
    ("udg_Arthur set #1",         46472, ["set udg_Arthur=GetLastCreatedUnit()"], "L46472"),
    ("udg_Arthur set #2",         49282, ["set udg_Arthur=GetLastCreatedUnit()"], "L49282"),
    # --- fling fix: the mover's duration=0 stop-idiom (CORRECTED 29044/29061 -> 29022/29051) ---
    ("Knockback stop-idiom A",    29022, ["set s__Knockback_duration[this]=0"], "L29022"),
    ("Knockback stop-idiom B",    29051, ["set s__Knockback_duration[this]=0"], "L29051"),
    # --- Phase 2 cliff-level idiom ---
    ("cliff-level idiom",         29066, ["GetTerrainCliffLevel(GetUnitX(s__Knockback_unit[this])"], "L29066"),
    # --- Phase 3 patrol rects (CORRECTED third name gg_rct_Camelot_1 -> gg_rct_Arthur_Move_to_Camelot_1) ---
    ("rect Appear (WP0)",         42919, ["set gg_rct_Arthur_Kay_Lancelot_Appear=Rect(4288.0, 10272.0, 4704.0, 10560.0)"], "L42919"),
    ("rect Camelot_1 (WP2)",      42920, ["set gg_rct_Arthur_Move_to_Camelot_1=Rect(4608.0, 10112.0, 4704.0, 10208.0)"], "gg_rct_Arthur_Move_to_Camelot_1"),
    ("rect Camelot_2 (WP1)",      42921, ["set gg_rct_Arthur_Move_to_Camelot_2=Rect(4352.0, 10080.0, 4448.0, 10176.0)"], "gg_rct_Arthur_Move_to_Camelot_2"),
    # --- Phase 3 move idioms ---
    ("squared-distance idiom",    25640, ["set dx=dx * dx + dy * dy"], "L25640"),
    ("IssuePointOrder move",      29226, ["IssuePointOrder(", '"move"'], "L29226"),
    # --- Phase 4 combat / retreat ---
    ("IssueTargetOrder attack",   61280, ["IssueTargetOrderBJ(", '"attack"'], "L61280"),
    ("GetWidgetLife",              6207, ["GetWidgetLife(GetFilterUnit())"], "L6207"),
    ("BlzGetUnitMaxHP",           24186, ["BlzGetUnitMaxHP(s__BurningSpirit_unit[this])"], "L24186"),
    ("ability rawcode SPSU",       1369, ["'SPSU'"], "L1369"),
    ("ability rawcode A003",       1373, ["'A003'"], "L1373"),
    ("ability rawcode A01F",       1375, ["'A01F'"], "L1375"),
    ("ability rawcode DDas",       1140, ["'DDas'"], "L1140"),
    ("cooldown gate",             32043, ["BlzGetUnitAbilityCooldownRemaining(udg_Arthur"], "L32043"),
    # --- Phase 5 shop ---
    ("merchant ngme",             41011, ["'ngme'", "5824.0, 6144.0"], "L41011"),
    ("merchant nmrk",             41032, ["'nmrk'", "4928.0, 6208.0"], "L41032"),
    ("merchant nmrk_0250",        42610, ["gg_unit_nmrk_0250", "8064.0, - 10560.0"], "L42610"),
    ("pawn-item event",           70181, ["EVENT_PLAYER_UNIT_PAWN_ITEM"], "L70181"),
    ("gold AdjustPlayerStateBJ",  48696, ["AdjustPlayerStateBJ", "PLAYER_STATE_RESOURCE_GOLD"], "L48696"),
]


# The dated audit note this binder appends to the runbook redundantly mentions
# the corrected cites; counting it would make the reverse check VACUOUS against a
# body edit (it would still "find" the cite in our own note). The reverse
# direction must bind the integration BODY the operator actually follows, so we
# strip the note before searching prose.
NOTE_MARKER = "**Re-ground note —"


def runbook_body(runbook_text):
    """The operator-facing body, excluding this binder's own audit note."""
    return runbook_text.split(NOTE_MARKER, 1)[0]


def audit_anchors(extract_lines, runbook_text):
    """Return list of (label, live_ok, prose_ok, detail)."""
    body = runbook_body(runbook_text)
    rows = []
    for label, lineno, tokens, cite in ANCHORS:
        live = extract_lines[lineno - 1] if 0 < lineno <= len(extract_lines) else "<<EOF>>"
        missing = [t for t in tokens if t not in live]
        live_ok = not missing
        prose_ok = cite in body
        detail = ""
        if not live_ok:
            detail = f"live L{lineno} = {live.strip()!r} (missing {missing!r})"
        elif not prose_ok:
            detail = f"runbook prose no longer carries cite {cite!r}"
        rows.append((label, live_ok, prose_ok, detail))
    return rows


def report(rows):
    print(f"{'ANCHOR':<28}{'LINE':<8}{'LIVE':<7}{'PROSE':<7}")
    for (label, lineno, _, _), (_, live_ok, prose_ok, detail) in zip(ANCHORS, rows):
        print(f"{label:<28}{('L'+str(lineno)):<8}{'OK' if live_ok else 'DRIFT':<7}"
              f"{'OK' if prose_ok else 'DRIFT':<7}" + (f"  -> {detail}" if detail else ""))


def selftest():
    print("=== SELFTEST: token-match unit test + live-drift + prose-drop (teeth) ===")
    # synthetic in-memory copies that satisfy every claim...
    lines = ["x"] * 76000
    runbook = ""
    for _, lineno, tokens, cite in ANCHORS:
        lines[lineno - 1] = "    " + " ".join(tokens) + " // synthetic"
        runbook += cite + " "
    base = audit_anchors(lines, runbook)
    assert all(r[1] and r[2] for r in base), "baseline anchors should all pass both ways"

    # multi-token anchor must require ALL tokens (drop one of the merchant_0250 pair)
    mt_lines = list(lines)
    mt_lines[42610 - 1] = "    gg_unit_nmrk_0250 // coords dropped"
    mt = audit_anchors(mt_lines, runbook)
    caught_multitoken = any(lbl == "merchant nmrk_0250" and not lo for lbl, lo, po, d in mt)

    # 1) DRIFT a live anchor line (re-bake moved the stop-idiom off L29022)
    bad_lines = list(lines)
    bad_lines[29022 - 1] = "    call GroupEnumUnitsInRange(s__Knockback_group[this], x, y) // re-stamped"
    drift = audit_anchors(bad_lines, runbook)
    caught_live = any((not r[1]) and "L29022" in r[3] for r in drift)

    # 2) DROP a runbook cite (operator edited prose, live unchanged) — use the
    #    rect-name cite that was the real rot we fixed
    bad_runbook = runbook.replace("gg_rct_Arthur_Move_to_Camelot_1 ", "")
    drop = audit_anchors(lines, bad_runbook)
    caught_prose = any((not r[2]) and "gg_rct_Arthur_Move_to_Camelot_1" in r[3] for r in drop)

    print(f"  multi-token all-required caught : {caught_multitoken}")
    print(f"  live-drift caught               : {caught_live}")
    print(f"  prose-drop caught               : {caught_prose}")
    ok = caught_multitoken and caught_live and caught_prose
    print(f"\nSELFTEST {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 3


def main():
    if "--selftest" in sys.argv:
        return selftest()
    if not EXTRACT.exists():
        print(f"FATAL: live extract not found: {EXTRACT}")
        return 2
    if not RUNBOOK.exists():
        print(f"FATAL: companion-AI runbook not found: {RUNBOOK}")
        return 2

    raw = EXTRACT.read_bytes()
    md5 = hashlib.md5(raw).hexdigest()
    print(f"live extract : {EXTRACT}")
    print(f"  md5={md5}  (runbook pins {RUNBOOK_CLAIMED_MD5})")
    if md5 != RUNBOOK_CLAIMED_MD5:
        print("RESULT: FAIL — live extract md5 DRIFTED from the runbook-pinned hash; "
              "every line cite below is now suspect. Re-ground the runbook against the new bake.")
        return 1

    extract_lines = raw.decode("latin-1").split("\n")
    runbook_text = RUNBOOK.read_text()
    rows = audit_anchors(extract_lines, runbook_text)
    report(rows)

    fail = [(lbl, d) for lbl, lo, po, d in rows if not (lo and po)]
    fwd_ok = sum(1 for _, lo, _, _ in rows if lo)
    rev_ok = sum(1 for _, _, po, _ in rows if po)
    print(f"\nanchors={len(rows)}  forward(live)={fwd_ok}/{len(rows)}  "
          f"reverse(prose)={rev_ok}/{len(rows)}  md5=OK")
    if fail:
        print("RESULT: FAIL — companion-AI runbook live cites have drifted:")
        for lbl, d in fail:
            print(f"  - {lbl}: {d}")
        return 1
    print(f"RESULT: GREEN — all {len(rows)} live `war3map.j` line cites in "
          "companion_ai_APPLY_RUNBOOK.md hold BYTE-EXACT vs the md5-pinned extract "
          "AND the runbook prose still carries every cite (Arthur globals, the "
          "L29022/L29051 stop-idiom, the cliff idiom, the 3 patrol rects, move/attack "
          "precedents, HP natives, 4 ability rawcodes + cooldown gate, merchants, "
          "pawn/gold precedents). The companion-AI apply runbook is bound both ways.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
