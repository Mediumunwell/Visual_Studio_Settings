#!/usr/bin/env python3
r"""
verify_hero_select_p2_spawnability_anchor.py
================================================================================
KOTR Hero-Select REDESIGN (Track 4) · P2 **per-slot SPAWN-ABILITY scalar transfer-op**
<-> handler authority <-> live extract binder.
Built 2026-06-19 by KOTR Builder (engine claude-p).

WHY THIS GATE EXISTS (a real, uncovered seam on the P2 apply path)
--------------------------------------------------------------------------------
`hero_select_p2_APPLY_RUNBOOK.md`'s STEP-0 var table reserves the *scalar*
`CastleSlot_SpawnAbility` array for the per-slot ability added to the freshly-spawned
hero ("per-slot ability rawcode added to the hero (Yvain `'LInf'`); 0 = none"). The
handler then collapses the bodies' spawn-ability adds into ONE guarded scalar op,
positioned immediately AFTER the hero spawn and BEFORE SaveHero:
    if udg_CastleSlot_SpawnAbility[i] != 0 then
        call UnitAddAbilityBJ(udg_CastleSlot_SpawnAbility[i], hero)
    endif
i.e. only the ability rawcode is per-slot data; the 2nd arg is uniform (the just-spawned
hero == GetLastCreatedUnit() live == `hero` in the spine). Unlike the item/ally/avail
families this op is NOT a windowed sub-table loop — it is a SPARSE SCALAR guarded on
`!= 0`: only Yvain ('LInf') sets one; the other 9 slots have SpawnAbility==0 (the guard
skips, zero cost). The handler header makes several checkable claims the WE operator
relies on before deleting the 10 old bodies:
  1. EXACTLY Yvain carries a spawn-ability add (the other 9 slots carry none),
  2. Yvain adds exactly 1 ability ('LInf'; 1 spawn-ability add total),
  3. every spawn-ability add is the arg-UNIFORM UnitAddAbilityBJ(<id>, <just-spawned hero>) —
     only the ability rawcode is per-slot data.
If any of those drift, the operator could bake a SpawnAbility row onto the wrong slot,
drop Yvain's 'LInf' (the table compiles fine with SpawnAbility==0 — a SILENT no-ability
Yvain), or mistake the uniform call for per-slot logic — and no other gate would catch it:
  * `verify_hero_select_p2_generated_j.py` / `verify_hero_select_p2_datatable.py` bind the
    MATERIALIZED SpawnAbility scalar column vs the catalog JSON — they prove the BAKED
    column is internally consistent, NOT that it matches the live bodies' spawn-ability op
    nor the handler header's natural-language claims (a header/table that drifts from the
    bodies the table is baked from goes uncaught there).
  * `verify_hero_select_p2_item_loadout_anchor.py` / `_avail_anchor.py` /
    `_allyrescueinvuln_anchor.py` bind the windowed-loop op families on the spine; none
    reads the scalar SpawnAbility add (a DIFFERENT, earlier op — right after the spawn).
  * `verify_hero_select_p2_spawnloc_faceloc_anchor.py` binds the hero-spawn spine (the op
    SpawnAbility immediately follows); it never reads the ability add.
  * `verify_hero_select_p2_loop.py` / `audit_hero_select_p2_equivalence.py` compile +
    op-equivalence-prove the handler; they never read the runbook .md, so a runbook/header
    spawn-ability claim that drifts from the spine they prove goes uncaught.

So this gate closes the seam the established Track-4 way: it binds the runbook
spawn-ability claim <-> handler header + spine authority <-> live extract spawn-ability op,
both ways, against the md5-pinned canonical extract — the scalar-guard twin of the
item-loadout / avail / ally-rescue-invuln windowed-loop binders. CRUCIAL TEETH: the live
extract has MANY more UnitAddAbilityBJ calls OUTSIDE the 10 pick bodies (the talent-tree
arm, the Avul placeholders, dragon/portal/barrel systems, the deferred newArthur re-pick
triggers, …). Counting those would inflate the family; this gate BODY-SCOPES to the 10
hand-written Trig_<Hero>_Actions pick bodies (L49272-50811 per the runbook's corrected
span) so only the real pick-path ability add counts.

WHAT IT CHECKS (read-only; touches no .w3x and no shippable .j)
--------------------------------------------------------------------------------
  0. md5 pin: the live extract still hashes to the runbook-pinned md5 (a re-bake trips it).
  1. all 10 hand-written hero pick bodies are present in the live extract.
  2. occupant: EXACTLY {Yvain} carries an in-body spawn-ability add (the other 9 carry
     none) (live, body-scoped) <-> handler "Only Yvain sets one ('LInf')" <-> runbook
     "per-slot ability rawcode added to the hero (Yvain `'LInf'`); 0 = none".
  3. spawn-ability distribution: live in-body counts == {Yvain:1, rest:0} (live) <->
     handler "1 'LInf' ... the other 9 slots have SpawnAbility==0" <-> runbook
     `CastleSlot_SpawnAbility` row.
  4. spawn-ability rawcode: Yvain adds 'LInf' (live) <-> handler header
     UnitAddAbilityBJ('LInf', GetLastCreatedUnit()) <-> runbook spawn-ability rawcode cite.
  5. spawn-ability uniform: every in-body add = UnitAddAbilityBJ(<id>, GetLastCreatedUnit())
     (live) <-> handler spine UnitAddAbilityBJ(udg_CastleSlot_SpawnAbility[i], hero) +
     "only the ability rawcode is per-slot data" <-> runbook `CastleSlot_SpawnAbility`.

Run:        python3 verify_hero_select_p2_spawnability_anchor.py
Self-test:  python3 verify_hero_select_p2_spawnability_anchor.py --selftest
            (parser unit-tests + a per-direction RED-catch so the gate has teeth,
             incl. body-scoped exclusion of out-of-body UnitAddAbilityBJ calls)
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

# the 10 hand-written hero pick bodies, in catalog order.
HERO_FUNCS = [
    ("Trig_King_Arthur_Actions", "Arthur"),
    ("Trig_Lady_Guinevere_Actions", "Guinevere"),
    ("Trig_Lady_of_the_Lake_Actions", "Nimue"),
    ("Trig_Merlin_Actions", "Merlin"),
    ("Trig_Sir_Kay_Actions", "Kay"),
    ("Trig_Sir_Percival_Actions", "Percival"),
    ("Trig_Sir_Galahad_Actions", "Galahad"),
    ("Trig_Sir_Lancelot_Actions", "Lancelot"),
    ("Trig_Sir_Yvain_Actions", "Yvain"),
    ("Trig_Sir_Gawain_Actions", "Gawain"),
]

# the catalog/handler spawn-ability distribution the runbook claim is filled against.
# SPARSE-SCALAR: only Yvain adds an ability ('LInf'); the other 9 slots carry none.
EXPECTED_SPAWNABILITY = {
    "Yvain": ["LInf"],
}
EXPECTED_SPAWNABILITY_COUNTS = {h: 1 for h in EXPECTED_SPAWNABILITY}   # {Yvain:1}
EXPECTED_SPAWNABILITY_TOTAL = sum(len(v) for v in EXPECTED_SPAWNABILITY.values())  # 1
EXPECTED_OCCUPANTS = set(EXPECTED_SPAWNABILITY)                        # {Yvain}

# the exact, arg-uniform call signature the live pick bodies use (canonicalized: the
# ability rawcode collapsed to '<id>'). The 2nd arg is literally GetLastCreatedUnit()
# (the just-spawned hero) in a live body.
SPAWNABILITY_SIG = "call UnitAddAbilityBJ('<id>', GetLastCreatedUnit())"

# the handler spine line (post // strip + whitespace collapse). The spine's 2nd arg is the
# `hero` local (== GetLastCreatedUnit(), set just above) — the documented uniform form.
SPAWNABILITY_SPINE = "UnitAddAbilityBJ(udg_CastleSlot_SpawnAbility[i], hero)"


def body_of(extract_text, func):
    """The body text of one Trig_<Hero>_Actions function, or None if gone. Anchored on the
    exact `function <name> takes nothing returns nothing` ... `endfunction` span so the
    abundant out-of-body UnitAddAbilityBJ calls can never leak in."""
    m = re.search(
        r"function " + re.escape(func) + r" takes nothing returns nothing(.*?)\nendfunction",
        extract_text, re.DOTALL)
    return m.group(1) if m else None


def _ability_rawcodes(body):
    """Ordered ability rawcodes from `call UnitAddAbilityBJ('<id>', ...)` in a body.
    Only the rawcode-literal form is a spawn-ability add — variable-arg UnitAddAbilityBJ
    (udg_*/non-literal) is a different op and is excluded by the `'...'` anchor."""
    out = []
    for raw in re.findall(r"call UnitAddAbilityBJ\('([^']*)'", body):
        out.append(raw)
    return out


def _ability_calls(body):
    """All literal-rawcode `call UnitAddAbilityBJ('...', ...)` one-liners in a body,
    rawcode -> '<id>'."""
    out = []
    for raw in re.findall(r"call UnitAddAbilityBJ\('[^']*'[^\n]*\)", body):
        out.append(re.sub(r"'[^']*'", "'<id>'", raw.strip()))
    return out


def live_facts(extract_text):
    """Per-body spawn-ability facts, BODY-SCOPED to the 10 pick bodies. Every value
    independently checkable so a single mutation trips exactly one anchor."""
    rawcodes = {}  # hero -> [ability rawcodes]
    calls = {}     # hero -> [canonicalized UnitAddAbilityBJ calls]
    missing = []
    for func, hero in HERO_FUNCS:
        b = body_of(extract_text, func)
        if b is None:
            missing.append(hero)
            continue
        rawcodes[hero] = _ability_rawcodes(b)
        calls[hero] = _ability_calls(b)
    return {
        "n_found": len(rawcodes),
        "missing": missing,
        "rawcodes": rawcodes,
        "calls": calls,
    }


def _occupants(d):
    return {h for h, v in d.items() if v}


def _counts(d):
    return {h: len(v) for h, v in d.items() if v}


def _all_match(d, sig):
    """True iff every call across every body equals the uniform signature (and >=1 exists)."""
    seen = False
    for calls in d.values():
        for c in calls:
            seen = True
            if c != sig:
                return False
    return seen


def all_rows(extract_text, runbook_text, handler_text):
    """Per-anchor rows: (label, live_ok, handler_ok, prose_ok, prose_required, detail)."""
    f = live_facts(extract_text)
    rbf = re.sub(r"\s+", " ", runbook_text)         # full runbook, normalized
    # normalize the handler: strip `//` line-markers + collapse whitespace so wrapped
    # header claims AND the real spine calls both match contiguously.
    hd = re.sub(r"\s+", " ", re.sub(r"//+", " ", handler_text))
    rows = []

    def row(label, live_ok, handler_ok, prose_ok, prose_required, detail=""):
        rows.append((label, live_ok, handler_ok, prose_ok, prose_required, detail))

    # 1) all 10 hero pick bodies present
    live_ok = f["n_found"] == 10 and not f["missing"]
    row("bodies:present=10", live_ok,
        "10 hand-written Trig_<Hero>_Actions" in hd,
        "10 hand-written pick bodies" in rbf, True,
        "" if live_ok else f"missing/!=10: found={f['n_found']} missing={f['missing']}")

    # 2) occupant: EXACTLY {Yvain} carries an in-body spawn-ability add
    occ = _occupants(f["rawcodes"])
    live_ok = occ == EXPECTED_OCCUPANTS
    row("spawnability:occupant={Yvain}", live_ok,
        "Only Yvain sets one ('LInf'); the other 9 slots have SpawnAbility==0" in hd,
        "per-slot ability rawcode added to the hero (Yvain `'LInf'`); 0 = none" in rbf, True,
        "" if live_ok else f"in-body spawn-ability occupants={sorted(occ)} (expected {sorted(EXPECTED_OCCUPANTS)})")

    # 3) spawn-ability distribution: {Yvain:1}, total 1
    counts = _counts(f["rawcodes"])
    total = sum(len(v) for v in f["rawcodes"].values())
    live_ok = counts == EXPECTED_SPAWNABILITY_COUNTS and total == EXPECTED_SPAWNABILITY_TOTAL
    row("spawnability:distribution+total=1", live_ok,
        "the other 9 slots have SpawnAbility==0" in hd,
        "`CastleSlot_SpawnAbility`" in rbf, True,
        "" if live_ok else f"live spawn-ability counts={counts} total={total} (expected {EXPECTED_SPAWNABILITY_COUNTS}, total {EXPECTED_SPAWNABILITY_TOTAL})")

    # 4) spawn-ability rawcode: Yvain 'LInf'
    live_ok = {h: v for h, v in f["rawcodes"].items() if v} == EXPECTED_SPAWNABILITY
    row("spawnability:rawcode", live_ok,
        "Yvain's UnitAddAbilityBJ('LInf', GetLastCreatedUnit())" in hd,
        "spawn-ability/extras rawcodes `'LInf'`" in rbf, True,
        "" if live_ok else f"live spawn-ability rawcodes={ {h: v for h, v in f['rawcodes'].items() if v} } (expected {EXPECTED_SPAWNABILITY})")

    # 5) spawn-ability uniform: every add = UnitAddAbilityBJ(<id>, GetLastCreatedUnit())
    live_ok = _all_match(f["calls"], SPAWNABILITY_SIG)
    row("spawnability:uniform-spine", live_ok,
        SPAWNABILITY_SPINE in hd
        and "only the ability rawcode is per-slot data, carried as the scalar udg_CastleSlot_SpawnAbility[i]" in hd,
        "`CastleSlot_SpawnAbility`" in rbf, True,
        "" if live_ok else "a live spawn-ability add is not the uniform UnitAddAbilityBJ(<id>,GetLastCreatedUnit())")
    return rows


def _passed(live_ok, handler_ok, prose_ok, prose_required):
    return bool(live_ok) and bool(handler_ok) and (bool(prose_ok) or not prose_required)


def report(rows):
    print(f"{'ANCHOR':<38}{'LIVE':<8}{'HANDLER':<10}{'PROSE':<8}")
    for label, live_ok, handler_ok, prose_ok, prose_required, detail in rows:
        prose_cell = ("OK" if prose_ok else "DRIFT") if prose_required else "n/a"
        print(f"{label:<38}{'OK' if live_ok else 'DRIFT':<8}"
              f"{'OK' if handler_ok else 'DRIFT':<10}"
              f"{prose_cell:<8}"
              + (f"  -> {detail}" if detail else ""))


def _synth_ok():
    """A synthetic (extract, runbook, handler) triple satisfying every anchor — the
    selftest baseline + the fixtures each RED-catch mutates. Encodes the real sparse
    spawn-ability distribution (only Yvain 'LInf') so the count/occupant anchors have
    teeth, AND plants OUT-OF-BODY UnitAddAbilityBJ calls so the body-scope exclusion is
    exercised."""
    bodies = []
    for func, hero in HERO_FUNCS:
        head = f"function {func} takes nothing returns nothing\n"
        lines = []
        for rc in EXPECTED_SPAWNABILITY.get(hero, []):
            lines.append(f"    call UnitAddAbilityBJ('{rc}', GetLastCreatedUnit())\n")
        bodies.append(head + "".join(lines) + "endfunction\n")
    # out-of-body UnitAddAbilityBJ calls (talent arm / placeholders / re-pick triggers) —
    # MUST NOT be counted.
    bodies.append(
        "function Trig_newYvain_Actions takes nothing returns nothing\n"
        "    call UnitAddAbilityBJ('LInf', GetLastCreatedUnit())\n"
        "endfunction\n")
    bodies.append(
        "function InitTalentArm takes nothing returns nothing\n"
        "    call UnitAddAbilityBJ('Avul', gg_unit_hfoo_0648)\n"
        "endfunction\n")
    extract = "\n".join(bodies)
    handler = (
        "//  Replaces the SHARED mechanics of the 10 hand-written Trig_<Hero>_Actions pick bodies.\n"
        "    // --- per-slot SPAWN ABILITY (v2 2026-06-17) ---\n"
        "    // faithful to Yvain's UnitAddAbilityBJ('LInf', GetLastCreatedUnit()) at this exact position\n"
        "    // (immediately AFTER the hero spawn, BEFORE SaveHero). The 2nd arg is uniform (the just-spawned\n"
        "    // hero == GetLastCreatedUnit()) so only the ability rawcode is per-slot data, carried as the\n"
        "    // scalar udg_CastleSlot_SpawnAbility[i]. Only Yvain sets one ('LInf'); the other 9 slots have\n"
        "    // SpawnAbility==0 -> the guard skips, zero cost (audit SpawnAbility dimension).\n"
        "    if udg_CastleSlot_SpawnAbility[i] != 0 then\n"
        "        call UnitAddAbilityBJ(udg_CastleSlot_SpawnAbility[i], hero)\n"
        "    endif\n"
    )
    runbook = (
        "## STEP 2 — Wire the pedestals ... disable the 10 hand-written pick bodies\n"
        "| `CastleSlot_SpawnAbility` | integer **array** | 0 | P2 | per-slot ability rawcode added to "
        "the hero (Yvain `'LInf'`); 0 = none |\n"
        "All other cites verified byte-exact unchanged: ... and the spawn-ability/extras rawcodes "
        "`'LInf'` / `'h012'` / `'BTLF'`.\n"
    )
    return extract, runbook, handler


def selftest():
    print("=== SELFTEST: parser unit-tests + per-direction RED-catch (teeth) ===")
    extract, runbook, handler = _synth_ok()

    # parser sanity (body-scoped: the 2 out-of-body funcs are NOT in HERO_FUNCS)
    f = live_facts(extract)
    assert f["n_found"] == 10 and not f["missing"], f
    assert _occupants(f["rawcodes"]) == EXPECTED_OCCUPANTS, _occupants(f["rawcodes"])
    assert {h: v for h, v in f["rawcodes"].items() if v} == EXPECTED_SPAWNABILITY, f["rawcodes"]
    assert sum(len(v) for v in f["rawcodes"].values()) == EXPECTED_SPAWNABILITY_TOTAL
    assert _all_match(f["calls"], SPAWNABILITY_SIG), f["calls"]

    base = all_rows(extract, runbook, handler)
    base_ok = all(_passed(l, h, p, pr) for _, l, h, p, pr, _ in base)
    print(f"  baseline all-green             : {base_ok}")
    assert base_ok, [r for r in base if not _passed(r[1], r[2], r[3], r[4])]

    def caught(rows, label):
        for lbl, l, h, p, pr, d in rows:
            if lbl == label:
                return not _passed(l, h, p, pr)
        return False

    # 1) LIVE: a hero body deleted -> bodies count trips
    bad = extract.replace("function Trig_Sir_Yvain_Actions takes nothing returns nothing",
                          "function Trig_GONE_Actions takes nothing returns nothing")
    c_bodies = caught(all_rows(bad, runbook, handler), "bodies:present=10")

    # 2) LIVE: give a non-occupant (Arthur) a spawn-ability add -> occupant + distribution trip
    bad = extract.replace(
        "function Trig_King_Arthur_Actions takes nothing returns nothing\n",
        "function Trig_King_Arthur_Actions takes nothing returns nothing\n"
        "    call UnitAddAbilityBJ('Afoo', GetLastCreatedUnit())\n")
    c_occ = caught(all_rows(bad, runbook, handler), "spawnability:occupant={Yvain}")
    c_dist_add = caught(all_rows(bad, runbook, handler), "spawnability:distribution+total=1")

    # 3) LIVE: drop Yvain's only spawn-ability add -> occupant + distribution + rawcode trip
    bad = extract.replace(
        "    call UnitAddAbilityBJ('LInf', GetLastCreatedUnit())\n", "", 1)
    c_dist_drop = caught(all_rows(bad, runbook, handler), "spawnability:distribution+total=1")
    c_raw_drop = caught(all_rows(bad, runbook, handler), "spawnability:rawcode")
    c_occ_drop = caught(all_rows(bad, runbook, handler), "spawnability:occupant={Yvain}")

    # 4) LIVE: wrong rawcode (Yvain 'LInf'->'Lxxx') -> rawcode trips
    bad = extract.replace("UnitAddAbilityBJ('LInf', GetLastCreatedUnit())",
                          "UnitAddAbilityBJ('Lxxx', GetLastCreatedUnit())", 1)
    c_raw = caught(all_rows(bad, runbook, handler), "spawnability:rawcode")

    # 5) LIVE: an add loses its uniform 2nd arg (hero local instead of GetLastCreatedUnit()) -> uniform trips
    bad = extract.replace(
        "    call UnitAddAbilityBJ('LInf', GetLastCreatedUnit())\n",
        "    call UnitAddAbilityBJ('LInf', udg_SomeOtherUnit)\n", 1)
    c_uni = caught(all_rows(bad, runbook, handler), "spawnability:uniform-spine")

    # 6) BODY-SCOPE TEETH: plant ANOTHER out-of-body ability add (a func NOT in HERO_FUNCS).
    #    A correctly body-scoped gate must IGNORE it — distribution/occupant stay GREEN. (If
    #    scoping regressed to a flat grep, this extra 'LInf' would inflate the family and trip.)
    bad = extract + (
        "\nfunction Trig_One_Flying_Yvain_Actions takes nothing returns nothing\n"
        "    call UnitAddAbilityBJ('LInf', GetLastCreatedUnit())\n"
        "endfunction\n")
    c_scope = (not caught(all_rows(bad, runbook, handler), "spawnability:occupant={Yvain}")
               and not caught(all_rows(bad, runbook, handler), "spawnability:distribution+total=1"))

    # 7) HANDLER drift: spine drops the SpawnAbility scalar -> uniform trips
    bad_h = handler.replace("udg_CastleSlot_SpawnAbility[i], hero", "udg_WRONG_SpawnAbility[i], hero")
    c_huni = caught(all_rows(extract, runbook, bad_h), "spawnability:uniform-spine")

    # 8) HANDLER drift: header drops the occupant claim -> occupant trips
    bad_h = handler.replace("Only Yvain sets one", "Only Lancelot sets one")
    c_hocc = caught(all_rows(extract, runbook, bad_h), "spawnability:occupant={Yvain}")

    # 9) HANDLER drift: header drops the rawcode -> rawcode trips
    bad_h = handler.replace("Yvain's UnitAddAbilityBJ('LInf', GetLastCreatedUnit())",
                            "Yvain's UnitAddAbilityBJ('Lzzz', GetLastCreatedUnit())")
    c_hraw = caught(all_rows(extract, runbook, bad_h), "spawnability:rawcode")

    # 10) PROSE drift: runbook drops the SpawnAbility occupant claim -> occupant trips
    bad_rb = runbook.replace("per-slot ability rawcode added to the hero (Yvain `'LInf'`); 0 = none",
                             "per-slot ability rawcode added to nobody")
    c_prose = caught(all_rows(extract, bad_rb, handler), "spawnability:occupant={Yvain}")

    # 11) PROSE drift: runbook drops the CastleSlot_SpawnAbility table row -> uniform (table cite) trips
    bad_rb = runbook.replace("`CastleSlot_SpawnAbility`", "`CastleSlot_GONE`")
    c_prtab = caught(all_rows(extract, bad_rb, handler), "spawnability:uniform-spine")

    for name, val in [
        ("live body deleted", c_bodies), ("live extra occupant", c_occ),
        ("live extra occ dist", c_dist_add), ("live drop occupant dist", c_dist_drop),
        ("live drop occupant raw", c_raw_drop), ("live drop occupant occ", c_occ_drop),
        ("live wrong rawcode", c_raw), ("live non-uniform arg", c_uni),
        ("body-scope holds (out-of-body ignored)", c_scope),
        ("handler SpawnAbility-scalar drift", c_huni), ("handler occupant drift", c_hocc),
        ("handler rawcode drift", c_hraw), ("prose spawn-ability-claim drop", c_prose),
        ("prose CastleSlot_SpawnAbility drop", c_prtab),
    ]:
        print(f"  {name:<40}caught : {val}")
    ok = base_ok and all([c_bodies, c_occ, c_dist_add, c_dist_drop, c_raw_drop, c_occ_drop,
                          c_raw, c_uni, c_scope, c_huni, c_hocc, c_hraw, c_prose, c_prtab])
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
              "the spawn-ability op cites are now suspect. Re-ground vs the new bake.")
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
        print("RESULT: FAIL — hero-select P2 spawn-ability op drifted:")
        for lbl, d in fail:
            print(f"  - {lbl}: {d}")
        return 1
    print("RESULT: GREEN — the per-slot spawn-ability add is bound vs the md5-pinned extract: all "
          "10 live pick bodies are present; EXACTLY Yvain carries an in-body spawn-ability add "
          "(the other 9 carry none — body-scoped past the many out-of-body UnitAddAbilityBJ calls); "
          "Yvain adds 1 ability ('LInf' = 1 total) via the uniform UnitAddAbilityBJ(<id>, "
          "GetLastCreatedUnit()) — matching the handler spine (UnitAddAbilityBJ("
          "udg_CastleSlot_SpawnAbility[i], hero) guarded on != 0) + header occupant/rawcode claims "
          "AND the runbook spawn-ability claim. The operator's STEP-1 SpawnAbility column cannot "
          "silently drift from the bodies it replaces (no mis-slotted row, no no-ability Yvain).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
