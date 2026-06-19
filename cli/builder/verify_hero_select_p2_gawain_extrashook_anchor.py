#!/usr/bin/env python3
r"""
verify_hero_select_p2_gawain_extrashook_anchor.py
================================================================================
KOTR Hero-Select REDESIGN (Track 4) · P2 **Gawain ExtrasHook polymorph cluster**
<-> handler header authority <-> live extract binder.

WHY THIS GATE EXISTS (a real, uncovered seam on the STEP-2 apply path)
--------------------------------------------------------------------------------
`hero_select_p2_APPLY_RUNBOOK.md` STEP 2 tells the WE operator to *create the 2
ExtrasHook triggers* before deleting the 10 old `Trig_<Hero>_Actions` bodies. The
Merlin one was bound 3-ways on 2026-06-18 (verify_hero_select_p2_merlin_extrashook
_anchor.py). Its TWIN — Gawain's `'h012'` polymorph cluster — STEP-2 describes
coarsely:

    "**Gawain** -> the `'h012'` polymorph cluster (spawn neutral `'h012'`, order it
     to polymorph the two pedestal placeholders, 5s `'BTLF'` timed life, remove the
     two placeholders)"

and the handler header (`hero_select_p2_loop_handler.j`) describes precisely:

    "GAWAIN — the full h012-polymorph extras-caster cluster: spawn a neutral 'h012'
     caster, order it to polymorph the two pedestal placeholders (gg_unit_H014_0610
     / gg_unit_Yuln_0448), give that caster a 5s timed life ('BTLF'), then remove
     the two polymorphed placeholders. (Audit: this whole cluster — CreateNUnits
     ('h012') + 2x IssueTargetOrderBJ + UnitApplyTimedLifeBJ + the 2 pedestal
     RemoveUnits — is DEFERRED to this hook, NOT the data-uniform spine.)"

That ExtrasHook is what the operator must hand-rebuild in STEP 2 (the data-uniform
`CastleSlot_ApplyPick(i)` spine deliberately does NOT collapse it). If the prose
ever drifts from the live Gawain body — a polymorph target renamed, the timed-life
duration retimed, a pedestal-remove dropped, or the polymorph count changed — the
operator would rebuild the wrong cluster, OR (worse) move a deferred op onto the
data-uniform spine. Yet NO gate binds this STRUCTURE 3-ways today:

  * `verify_hero_select_divergence_catalog_anchors.py` binds Gawain's §5 catalog
    tokens ('h012' / gg_unit_H014_0610 / gg_unit_Yuln_0448 / h__RemoveUnit) both
    ways, but reads the DIVERGENCE_CATALOG .md — never the runbook STEP-2 prose,
    never the handler header, and never the cluster's op-count/ordering structure.
  * `verify_hero_select_p2_runbook_anchors.py` only proves the irregular-tail
    rawcodes ('LInf'/'h012'/'BTLF') are PRESENT somewhere in the 10-body range +
    ref counts — it cannot catch a renamed polymorph target, a retimed timed-life,
    a dropped pedestal-remove, or a polymorph-count change.
  * `audit_hero_select_p2_equivalence.py` (fix_specs) proves each Gawain op is
    DEFERRED via the extras-caster rule, but it reads no runbook/handler PROSE, so
    it cannot catch a runbook or handler header that drifts from the body.

So Gawain's "spawn 'h012' / 2 named polymorphs / 5s BTLF timed life / 2 pedestal
removes" structure is an unbound live-map claim. This binder closes that seam:
runbook prose <-> handler authority <-> live extract, the same both-ways contract
as its Track-4 sibling (the Merlin ExtrasHook gate). The PRECISE anchors (the two
named placeholders, the 'BTLF' rawcode) are bound handler<->live only — they carry
prose_required=False and report PROSE as 'n/a'; the COARSE cluster shape (spawn,
polymorph the two, timed life, remove the two) is required in BOTH prose sources.

WHAT IT CHECKS (read-only; touches no .w3x and no shippable .j)
--------------------------------------------------------------------------------
  1. The live canonical extract still hashes to the md5 the runbook pins.
  2. The live Gawain body (function Trig_Sir_Gawain_Actions ... endfunction):
       - spawns exactly one neutral 'h012' caster (CreateNUnitsAtLoc 'h012'),
       - issues exactly 2 "polymorph" target orders,
       - to gg_unit_H014_0610 and gg_unit_Yuln_0448,
       - gives a 5.00s timed life with rawcode 'BTLF' (UnitApplyTimedLifeBJ),
       - and removes exactly those 2 pedestal placeholders (h__RemoveUnit).
  3. Each anchor agrees with the handler header, and the COARSE anchors agree
     with the runbook STEP-2 Gawain clause.

Exit 0 only if md5 matches AND every required direction holds for every anchor.

Run:        python3 verify_hero_select_p2_gawain_extrashook_anchor.py
Self-test:  python3 verify_hero_select_p2_gawain_extrashook_anchor.py --selftest

Registered in verify_builder_gates.py (the cli/builder aggregate sweep). Sibling
of the Merlin ExtrasHook binder; same EXTRACT / md5 / both-ways-binding contract.
"""
import hashlib
import re
import sys
from pathlib import Path

EXTRACT = Path.home() / "Warcraft III" / "KOTR" / "_extract_v050" / "war3map.j"
RUNBOOK = Path.home() / "Warcraft III" / "KOTR" / "_crew" / "hero_select_p2_APPLY_RUNBOOK.md"
HANDLER = (Path.home() / "Systems_Migration" / "kotr" / "fix_specs"
           / "hero_select_p2_loop_handler.j")

# the md5 the runbook pins the canonical extract to (Grounding header) — same pin
# the sibling Track-4 binders use, so a re-bake trips them all together.
RUNBOOK_CLAIMED_MD5 = "967131658fd8d4fb27ee0d7f74e4bd22"

GAWAIN_FUNC = re.compile(
    r"function Trig_Sir_Gawain_Actions takes nothing returns nothing(.*?)\nendfunction",
    re.DOTALL,
)
# spawn of the neutral 'h012' extras-caster
H012_SPAWN = re.compile(r"call CreateNUnitsAtLoc\(\s*\d+,\s*'h012'")
# ordered polymorph target units
POLY_TARGET = re.compile(
    r'call IssueTargetOrderBJ\([^,]+,\s*"polymorph",\s*(gg_unit_\w+)\)')
# the timed-life applied to the caster: (duration, rawcode)
TIMED_LIFE = re.compile(r"call UnitApplyTimedLifeBJ\(\s*([\d.]+),\s*'(\w+)'")
# pedestal placeholder removals
REMOVE_UNIT = re.compile(r"call h__RemoveUnit\((gg_unit_\w+)\)")


def gawain_body(extract_text):
    """The Trig_Sir_Gawain_Actions body text, or None if the function is gone."""
    m = GAWAIN_FUNC.search(extract_text)
    return m.group(1) if m else None


def live_facts(body):
    """Structural facts from the live Gawain body. Every value is independently
    checkable so a single mutation trips exactly one anchor."""
    if body is None:
        return None
    poly = POLY_TARGET.findall(body)                  # [gg_unit_H014_0610, gg_unit_Yuln_0448]
    tl = TIMED_LIFE.search(body)
    removed = REMOVE_UNIT.findall(body)               # includes the 2 pedestals
    # the pedestal removes that match a polymorph target (excludes the villager remove
    # of GetTriggerUnit, which is not a gg_unit_* handle and so never matches here)
    pedestal_removes = [u for u in removed if u in poly]
    return {
        "n_h012": len(H012_SPAWN.findall(body)),
        "poly_targets": poly,
        "n_poly": len(poly),
        "timed_life": (tl.group(1), tl.group(2)) if tl else None,
        "pedestal_removes": sorted(set(pedestal_removes)),
        "n_pedestal_removes": len(set(pedestal_removes)),
    }


def runbook_gawain_clause(runbook_text):
    """The STEP-2 Gawain ExtrasHook clause, or '' if gone. Collapses the wrapped
    multi-line clause to single-spaced text for contiguous token matching."""
    m = re.search(r"\*\*Gawain\*\*.*?remove the two placeholders\)",
                  runbook_text, re.DOTALL)
    return re.sub(r"\s+", " ", m.group(0)) if m else ""


def all_rows(extract_text, runbook_text, handler_text):
    """Per-anchor rows: (label, live_ok, handler_ok, prose_ok, prose_required, detail)."""
    f = live_facts(gawain_body(extract_text))
    rb = runbook_gawain_clause(runbook_text)
    # normalize the handler COMMENT text: strip `//` line-markers + collapse
    # whitespace so wrapped claims ("the 2 pedestal\n//   RemoveUnits") match contiguously.
    hd = re.sub(r"\s+", " ", re.sub(r"//+", " ", handler_text))
    rows = []

    def row(label, live_ok, handler_ok, prose_ok, prose_required, detail=""):
        rows.append((label, live_ok, handler_ok, prose_ok, prose_required, detail))

    if f is None:
        row("gawain-body:present", False,
            "function Trig_Sir_Gawain_Actions" in handler_text or "GAWAIN" in hd,
            "Gawain" in rb, True,
            "function Trig_Sir_Gawain_Actions ... endfunction not found in live extract")
        return rows

    # 1) exactly one neutral 'h012' caster spawned (COARSE — both prose name 'h012')
    live_ok = f["n_h012"] == 1
    row("h012-spawn:count=1", live_ok,
        "h012" in hd and ("CreateNUnits" in hd or "caster" in hd),
        "'h012'" in rb, True,
        "" if live_ok else f"live Gawain body has {f['n_h012']} 'h012' spawns, not 1")

    # 2) exactly two "polymorph" target orders (COARSE — both prose say polymorph the two)
    live_ok = f["n_poly"] == 2
    row("polymorph:count=2", live_ok,
        ("2x IssueTargetOrderBJ" in hd) or ("2× IssueTargetOrderBJ" in hd),
        ("polymorph" in rb and "two pedestal placeholders" in rb), True,
        "" if live_ok else f"live Gawain body has {f['n_poly']} polymorph orders, not 2")

    # 3/4) the two polymorph targets are gg_unit_H014_0610 + gg_unit_Yuln_0448 (PRECISE — handler)
    for unit in ("gg_unit_H014_0610", "gg_unit_Yuln_0448"):
        live_ok = unit in f["poly_targets"]
        row(f"polymorph-target:{unit}", live_ok, unit in hd, False, False,
            "" if live_ok else f"{unit} not among live polymorph targets {f['poly_targets']}")

    # 5) timed life duration 5.00 (COARSE — both prose say "5s ... timed life")
    live_ok = f["timed_life"] is not None and f["timed_life"][0] == "5.00"
    row("timed-life:5s", live_ok,
        "5s timed life" in hd,
        ("5s" in rb and "timed" in rb and "life" in rb), True,
        "" if live_ok
        else f"live timed-life duration = {f['timed_life'][0] if f['timed_life'] else None} (expected 5.00)")

    # 6) the timed-life rawcode is 'BTLF' (PRECISE — handler only)
    live_ok = f["timed_life"] is not None and f["timed_life"][1] == "BTLF"
    row("timed-life:BTLF", live_ok, "BTLF" in hd, False, False,
        "" if live_ok
        else f"live timed-life rawcode = {f['timed_life'][1] if f['timed_life'] else None} (expected BTLF)")

    # 7) exactly the 2 pedestal placeholders are removed (COARSE — both prose "remove the two")
    live_ok = (f["n_pedestal_removes"] == 2
               and f["pedestal_removes"] == sorted(["gg_unit_H014_0610", "gg_unit_Yuln_0448"]))
    row("pedestal-removes:count=2", live_ok,
        ("2 pedestal RemoveUnits" in hd) or ("2 pedestal RemoveUnit" in hd),
        "remove the two placeholders" in rb, True,
        "" if live_ok
        else f"live pedestal removes = {f['pedestal_removes']} (expected both placeholders)")
    return rows


def _passed(live_ok, handler_ok, prose_ok, prose_required):
    return bool(live_ok) and bool(handler_ok) and (bool(prose_ok) or not prose_required)


def report(rows):
    print(f"{'ANCHOR':<34}{'LIVE':<8}{'HANDLER':<10}{'PROSE':<8}")
    for label, live_ok, handler_ok, prose_ok, prose_required, detail in rows:
        prose_cell = ("OK" if prose_ok else "DRIFT") if prose_required else "n/a"
        print(f"{label:<34}{'OK' if live_ok else 'DRIFT':<8}"
              f"{'OK' if handler_ok else 'DRIFT':<10}"
              f"{prose_cell:<8}"
              + (f"  -> {detail}" if detail else ""))


def _synth_ok():
    """A synthetic (extract, runbook, handler) triple satisfying every anchor — the
    selftest baseline + the fixtures each RED-catch mutates."""
    body = (
        "function Trig_Sir_Gawain_Actions takes nothing returns nothing\n"
        "    call CreateNUnitsAtLoc(1, 'h012', Player(PLAYER_NEUTRAL_AGGRESSIVE), GetRectCenter(gg_rct_Gawain), bj_UNIT_FACING)\n"
        "    call IssueTargetOrderBJ(GetLastCreatedUnit(), \"polymorph\", gg_unit_H014_0610)\n"
        "    call IssueTargetOrderBJ(GetLastCreatedUnit(), \"polymorph\", gg_unit_Yuln_0448)\n"
        "    call UnitApplyTimedLifeBJ(5.00, 'BTLF', GetLastCreatedUnit())\n"
        "    call h__RemoveUnit(GetTriggerUnit())\n"
        "    call h__RemoveUnit(gg_unit_H014_0610)\n"
        "    call h__RemoveUnit(gg_unit_Yuln_0448)\n"
        "endfunction\n"
    )
    handler = (
        "//  GAWAIN — the full h012-polymorph extras-caster cluster: spawn a neutral 'h012' "
        "caster, order it to polymorph the two pedestal placeholders (gg_unit_H014_0610 / "
        "gg_unit_Yuln_0448), give that caster a 5s timed life ('BTLF'), then remove the two "
        "polymorphed placeholders. (Audit: CreateNUnits('h012') + 2x IssueTargetOrderBJ + "
        "UnitApplyTimedLifeBJ + the 2 pedestal RemoveUnits — DEFERRED to this hook.)\n"
    )
    runbook = (
        "STEP 2 ... **Gawain** -> the `'h012'` polymorph cluster (spawn neutral `'h012'`, "
        "order it to polymorph the two pedestal placeholders, 5s `'BTLF'` timed life, "
        "remove the two placeholders)\n"
    )
    return body, runbook, handler


def selftest():
    print("=== SELFTEST: parser unit-tests + per-direction RED-catch (teeth) ===")
    body, runbook, handler = _synth_ok()

    # parser sanity
    f = live_facts(gawain_body(body))
    assert f is not None and f["n_h012"] == 1, f
    assert f["poly_targets"] == ["gg_unit_H014_0610", "gg_unit_Yuln_0448"], f["poly_targets"]
    assert f["timed_life"] == ("5.00", "BTLF"), f["timed_life"]
    assert f["pedestal_removes"] == ["gg_unit_H014_0610", "gg_unit_Yuln_0448"], f["pedestal_removes"]

    base = all_rows(body, runbook, handler)
    base_ok = all(_passed(l, h, p, pr) for _, l, h, p, pr, _ in base)
    print(f"  baseline all-green             : {base_ok}")
    assert base_ok, [r for r in base if not _passed(r[1], r[2], r[3], r[4])]

    def caught(rows, label):
        for lbl, l, h, p, pr, d in rows:
            if lbl == label:
                return not _passed(l, h, p, pr)
        return False

    # 1) LIVE: the h012 spawn is dropped -> count != 1
    bad = body.replace(
        "    call CreateNUnitsAtLoc(1, 'h012', Player(PLAYER_NEUTRAL_AGGRESSIVE), GetRectCenter(gg_rct_Gawain), bj_UNIT_FACING)\n", "")
    c_spawn = caught(all_rows(bad, runbook, handler), "h012-spawn:count=1")

    # 2) LIVE: a polymorph order dropped -> count != 2
    bad = body.replace(
        "    call IssueTargetOrderBJ(GetLastCreatedUnit(), \"polymorph\", gg_unit_Yuln_0448)\n", "")
    c_polycount = caught(all_rows(bad, runbook, handler), "polymorph:count=2")

    # 3) LIVE: a polymorph target renamed -> named-target anchor trips
    bad = body.replace("\"polymorph\", gg_unit_H014_0610", "\"polymorph\", gg_unit_RENAMED")
    c_target = caught(all_rows(bad, runbook, handler), "polymorph-target:gg_unit_H014_0610")

    # 4) LIVE: timed-life retimed -> duration anchor trips
    bad = body.replace("UnitApplyTimedLifeBJ(5.00,", "UnitApplyTimedLifeBJ(9.00,")
    c_dur = caught(all_rows(bad, runbook, handler), "timed-life:5s")

    # 5) LIVE: timed-life rawcode changed -> BTLF anchor trips
    bad = body.replace("5.00, 'BTLF'", "5.00, 'XXXX'")
    c_btlf = caught(all_rows(bad, runbook, handler), "timed-life:BTLF")

    # 6) LIVE: a pedestal remove dropped -> pedestal-removes count trips
    bad = body.replace("    call h__RemoveUnit(gg_unit_Yuln_0448)\n", "")
    c_remove = caught(all_rows(bad, runbook, handler), "pedestal-removes:count=2")

    # 7) HANDLER drift: header drops the "2x IssueTargetOrderBJ" claim
    bad_h = handler.replace("2x IssueTargetOrderBJ", "some IssueTargetOrderBJ")
    c_hdr = caught(all_rows(body, runbook, bad_h), "polymorph:count=2")

    # 8) PROSE drift: runbook drops the "remove the two placeholders" claim (required prose)
    bad_rb = runbook.replace(", remove the two placeholders", "")
    c_prose = caught(all_rows(body, bad_rb, handler), "pedestal-removes:count=2")

    # 9) BODY gone entirely
    c_gone = caught(all_rows("nothing here", runbook, handler), "gawain-body:present")

    for name, val in [
        ("live h012-spawn drop", c_spawn), ("live polymorph-count drift", c_polycount),
        ("live target-rename drift", c_target), ("live timed-life retimed", c_dur),
        ("live BTLF rawcode drift", c_btlf), ("live pedestal-remove drop", c_remove),
        ("handler 2x drift", c_hdr), ("prose remove-two drop", c_prose),
        ("gawain body gone", c_gone),
    ]:
        print(f"  {name:<26}caught : {val}")
    ok = base_ok and all([c_spawn, c_polycount, c_target, c_dur, c_btlf, c_remove,
                          c_hdr, c_prose, c_gone])
    print(f"\nSELFTEST {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 3


def main():
    if "--selftest" in sys.argv:
        return selftest()
    for label, p in (("live extract", EXTRACT), ("runbook", RUNBOOK), ("handler", HANDLER)):
        if not p.exists():
            print(f"FATAL: {label} not found: {p}")
            return 2

    raw = EXTRACT.read_bytes()
    md5 = hashlib.md5(raw).hexdigest()
    print(f"live extract : {EXTRACT}")
    print(f"  md5={md5}  (runbook pins {RUNBOOK_CLAIMED_MD5})")
    if md5 != RUNBOOK_CLAIMED_MD5:
        print("RESULT: FAIL — live extract md5 DRIFTED from the runbook-pinned hash; "
              "Gawain's ExtrasHook cluster cites are now suspect. Re-ground vs the new bake.")
        return 1

    extract_text = raw.decode("latin-1")
    runbook_text = RUNBOOK.read_text()
    handler_text = HANDLER.read_text()
    rows = all_rows(extract_text, runbook_text, handler_text)
    report(rows)

    fail = [(lbl, d) for lbl, l, h, p, pr, d in rows if not _passed(l, h, p, pr)]
    live_ok = sum(1 for _, l, _, _, _, _ in rows if l)
    hand_ok = sum(1 for _, _, h, _, _, _ in rows if h)
    prose_req = [r for r in rows if r[4]]
    prose_ok = sum(1 for _, _, _, p, pr, _ in rows if pr and p)
    print(f"\nanchors={len(rows)}  live={live_ok}/{len(rows)}  "
          f"handler={hand_ok}/{len(rows)}  prose={prose_ok}/{len(prose_req)}(required)  md5=OK")
    if fail:
        print("RESULT: FAIL — hero-select P2 Gawain ExtrasHook polymorph cluster drifted:")
        for lbl, d in fail:
            print(f"  - {lbl}: {d}")
        return 1
    print("RESULT: GREEN — Gawain's STEP-2 ExtrasHook polymorph cluster is bound vs the "
          "md5-pinned extract: the live Trig_Sir_Gawain_Actions body spawns exactly one "
          "neutral 'h012' caster, issues exactly 2 'polymorph' orders (gg_unit_H014_0610, "
          "gg_unit_Yuln_0448), gives a 5.00s 'BTLF' timed life, and removes exactly those 2 "
          "pedestal placeholders — and that structure matches the handler header AND the "
          "runbook STEP-2 Gawain clause. The operator's hand-rebuilt Gawain cluster cannot "
          "silently drift from the body it replaces.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
