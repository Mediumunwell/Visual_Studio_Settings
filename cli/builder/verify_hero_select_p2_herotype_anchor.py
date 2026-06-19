#!/usr/bin/env python3
r"""
verify_hero_select_p2_herotype_anchor.py
================================================================================
KOTR Hero-Select REDESIGN (Track 4) · P2 APPLY-RUNBOOK **STEP-0 `CastleSlot_HeroType`
per-slot hero-identity** <-> handler spine authority <-> generated data table <-> live
extract binder.
Built 2026-06-19 by KOTR Builder (engine claude-p).

WHY THIS GATE EXISTS (a real, uncovered seam — the hero's IDENTITY itself)
--------------------------------------------------------------------------------
`hero_select_p2_APPLY_RUNBOOK.md` STEP-0 reserves the single most load-bearing data
field of the whole redesign:
    | `CastleSlot_HeroType` | integer **array** | 0 | P2 | per-slot hero unit-type rawcode |
That one row is WHICH HERO each pedestal actually spawns. The handler spine consumes it
verbatim:
    call CreateNUnitsAtLocFacingLocBJ(1, udg_CastleSlot_HeroType[i], picker, ...)
and `InitCastleSlotData` materializes the 10 values byte-exact from the canonical extract
(`set udg_CastleSlot_HeroType[0]='Harf' ... [9]='H014'`). If that per-slot hero-type
distribution drifts, the data-driven collapse spawns the WRONG hero at a pedestal — the
worst-possible silent regression, invisible to a compile.

The trap that makes this its OWN gate: **every pick body spawns TWO picker-owned units**
via `CreateNUnits*` — the real hero FIRST, then a `CastleSlot_TakenVillager` fallback
(`'n00S'/'n00Q'/'n00R'`) in the "already-taken" human-ELSE branch — PLUS Gawain's body
spawns a THIRD, the NEUTRAL `'h012'` polymorph caster. A naive "grab the CreateUnit
rawcode" conflates all three. The hero identity is specifically the FIRST *picker-owned*
spawn; the villager is the deferred ELSE op (a different STEP-0 row, `TakenVillager`); the
`'h012'` caster is neutral-owned and rides the ExtrasHook. This gate proves the data table
captured the HERO and conflated NEITHER.

Why no existing gate closes THIS seam:
  * `verify_castleslot_global_contract.py` binds the STEP-0 var TABLE row's *type +
    array-flag* (HeroType = integer array) — it never checks the per-slot VALUES nor the
    live hero identities, so a wrong rawcode passes it.
  * `verify_hero_select_p2_datatable.py` (fix_specs) does bind live HeroTypeId per body to
    a catalog — but it never reads the RUNBOOK .md, so a runbook STEP-0 row that drifts
    from the spine it proves goes uncaught (same gap the SpawnLoc/FaceLoc binder closed for
    the spawn API).
  * `verify_hero_select_p2_spawnloc_faceloc_anchor.py` binds the spawn *API* (9x
    FacingLocBJ + 1x Kay plain) and the SpawnLoc/FaceLoc loc args — NOT the 2nd-arg hero
    rawcode identity, and not the villager/neutral non-conflation.
  * `verify_hero_select_p2_generated_j.py` checks the materialized .j broadly; it is not a
    runbook<->handler<->live identity binder with the conflation teeth.

So this gate closes the seam the established Track-4 way: runbook prose <-> handler spine
<-> generated data table <-> md5-pinned live extract, both directions — the dense-uniform
(every slot has exactly one, all 10 DISTINCT) sibling of the sparse-scalar SpawnAbility/
EnableTrig binders.

WHAT IT CHECKS (read-only; touches no .w3x and no shippable .j)
--------------------------------------------------------------------------------
  0. md5 pin: the live extract still hashes to the runbook-pinned md5 (a re-bake trips it).
  1. all 10 hand-written hero pick bodies are present in the live extract.
  2. per-slot-faithful: for slot i, the FIRST picker-owned CreateNUnits 2nd arg in body i
     (live) == `set udg_CastleSlot_HeroType[i]='...'` (generated data table), all 10.
  3. 10-distinct: the 10 hero rawcodes are all distinct (a real per-slot identity, not a
     stuck/duplicated fill) <-> handler "BY SLOT INDEX" <-> runbook HeroType row.
  4. spine: handler passes udg_CastleSlot_HeroType[i] as the CreateNUnitsAtLocFacingLocBJ
     2nd arg (handler) <-> runbook "per-slot hero unit-type rawcode" <-> every live body
     spawns the hero as a CreateNUnits 2nd arg.
  5. non-conflation/villager: the SECOND picker-owned spawn per body (TakenVillager) is a
     SET DISJOINT from the hero set (live) AND the generated HeroType values are disjoint
     from the generated TakenVillager values (data table) <-> handler "(taken-villager
     block) is DEFERRED by design" <-> runbook "already-taken fallback ... human-ELSE,
     deferred".
  6. non-conflation/neutral: Gawain's neutral 'h012' caster is the SOLE neutral CreateNUnits
     and is excluded from the hero set (live) <-> handler header names it as the deferred
     neutral polymorph caster.
  7. ordering: every body has exactly [hero, villager] picker-owned spawns in that order —
     the discrimination invariant the data builder relies on (live; handler spine present).

Run:        python3 verify_hero_select_p2_herotype_anchor.py
Self-test:  python3 verify_hero_select_p2_herotype_anchor.py --selftest
            (parser unit-tests + a per-direction RED-catch so the gate has teeth)
"""
import hashlib
import re
import sys
from pathlib import Path

EXTRACT = Path.home() / "Warcraft III" / "KOTR" / "_extract_v050" / "war3map.j"
RUNBOOK = Path.home() / "Warcraft III" / "KOTR" / "_crew" / "hero_select_p2_APPLY_RUNBOOK.md"
HANDLER = (Path.home() / "Systems_Migration" / "kotr" / "fix_specs"
           / "hero_select_p2_loop_handler.j")
GEN_DATA = (Path.home() / "Systems_Migration" / "kotr" / "fix_specs"
            / "hero_select_p2_loop_data.gen.j")

# the md5 the runbook pins the canonical extract to (Grounding header) — same pin
# the sibling Track-4 binders use, so a re-bake trips them all together.
RUNBOOK_CLAIMED_MD5 = "967131658fd8d4fb27ee0d7f74e4bd22"

# the 10 hand-written hero pick bodies, in data-table SLOT order (slot i below ==
# udg_CastleSlot_*[i]). This ordering is itself proven by anchor 2 (per-slot-faithful):
# the live FIRST-picker-spawn of body i must equal the generated HeroType[i].
HERO_FUNCS = [
    ("Trig_King_Arthur_Actions", "Arthur"),         # 0
    ("Trig_Lady_Guinevere_Actions", "Guinevere"),   # 1
    ("Trig_Lady_of_the_Lake_Actions", "Nimue"),     # 2
    ("Trig_Merlin_Actions", "Merlin"),              # 3
    ("Trig_Sir_Kay_Actions", "Kay"),               # 4
    ("Trig_Sir_Percival_Actions", "Percival"),      # 5
    ("Trig_Sir_Galahad_Actions", "Galahad"),        # 6
    ("Trig_Sir_Lancelot_Actions", "Lancelot"),      # 7
    ("Trig_Sir_Yvain_Actions", "Yvain"),           # 8
    ("Trig_Sir_Gawain_Actions", "Gawain"),          # 9
]

# the exact spine 2nd-arg fragment the handler must carry.
SPINE_2ND_ARG = "CreateNUnitsAtLocFacingLocBJ(1, udg_CastleSlot_HeroType[i], picker,"

_RAWCODE = re.compile(r"CreateNUnitsAtLoc(?:FacingLocBJ)?\(1, '([^']+)'")


def body_of(extract_text, func):
    m = re.search(
        r"function " + re.escape(func) + r" takes nothing returns nothing(.*?)\nendfunction",
        extract_text, re.DOTALL)
    return m.group(1) if m else None


def body_spawns(body):
    """Ordered picker-owned + neutral CreateNUnits rawcodes in one pick body.
    picker[0] is the HERO spawn; picker[1] (if any) is the TakenVillager fallback;
    neutral holds Gawain's 'h012' polymorph caster (owned by a non-picker player)."""
    picker, neutral = [], []
    if body is None:
        return picker, neutral
    for raw in body.splitlines():
        s = raw.strip()
        if "CreateNUnits" not in s:
            continue
        m = _RAWCODE.search(s)
        code = m.group(1) if m else "?"
        if "GetOwningPlayer(GetTriggerUnit())" in s:
            picker.append(code)
        else:
            neutral.append(code)
    return picker, neutral


def live_facts(extract_text):
    """Per-slot hero identity facts pulled straight from the live bodies."""
    missing, heroes, villagers, neutrals, orders = [], [], [], [], []
    for func, _hero in HERO_FUNCS:
        body = body_of(extract_text, func)
        if body is None:
            missing.append(func)
            heroes.append(None)
            villagers.append(None)
            neutrals.append([])
            orders.append(None)
            continue
        picker, neutral = body_spawns(body)
        heroes.append(picker[0] if len(picker) >= 1 else None)
        villagers.append(picker[1] if len(picker) >= 2 else None)
        neutrals.append(neutral)
        # the discrimination invariant: exactly [hero, villager], hero first.
        orders.append(len(picker) == 2)
    return {
        "missing": missing,
        "heroes": heroes,            # slot-ordered live hero rawcodes
        "villagers": villagers,      # slot-ordered live TakenVillager rawcodes
        "neutrals": neutrals,        # per-slot neutral rawcodes (only Gawain non-empty)
        "orders": orders,            # per-slot: exactly [hero, villager]
    }


def gen_array(gen_text, name):
    """slot-ordered list of `set udg_<name>[i]='CODE'` values from the generated table."""
    pairs = re.findall(
        r"set udg_" + re.escape(name) + r"\[(\d+)\]\s*=\s*'([^']+)'", gen_text)
    out = {}
    for i, code in pairs:
        out[int(i)] = code
    return [out.get(i) for i in range(len(out))] if out else []


def all_rows(extract_text, runbook_text, handler_text, gen_text):
    """Per-anchor rows: (label, live_ok, handler_ok, prose_ok, prose_required, detail)."""
    f = live_facts(extract_text)
    gen_hero = gen_array(gen_text, "CastleSlot_HeroType")
    gen_vill = gen_array(gen_text, "CastleSlot_TakenVillager")
    rbf = re.sub(r"\s+", " ", runbook_text)
    hd = re.sub(r"\s+", " ", re.sub(r"//+", " ", handler_text))
    rows = []

    def row(label, live_ok, handler_ok, prose_ok, prose_required, detail=""):
        rows.append((label, live_ok, handler_ok, prose_ok, prose_required, detail))

    # 1) all 10 hero pick bodies present
    live_ok = not f["missing"] and all(h is not None for h in f["heroes"])
    row("bodies:present=10", live_ok,
        "10 hand-written Trig_<Hero>_Actions" in hd,
        "10 old `Trig_<Hero>_Actions`" in rbf, True,
        "" if live_ok else f"missing/empty bodies: {f['missing']}")

    # 2) per-slot-faithful: live first-picker-spawn[i] == generated HeroType[i], all 10
    live_ok = (len(gen_hero) == 10 and f["heroes"] == gen_hero)
    mism = [(i, f["heroes"][i], gen_hero[i] if i < len(gen_hero) else None)
            for i in range(10) if (i >= len(gen_hero) or f["heroes"][i] != gen_hero[i])]
    row("herotype:per-slot-faithful", live_ok,
        SPINE_2ND_ARG in hd,
        "per-slot hero unit-type rawcode" in rbf, True,
        "" if live_ok else f"live!=gen per slot {mism[:4]}")

    # 3) 10-distinct: a real per-slot identity, not a stuck/duplicated fill
    live_ok = (len([h for h in f["heroes"] if h]) == 10
               and len(set(h for h in f["heroes"] if h)) == 10)
    row("herotype:10-distinct", live_ok,
        "BY SLOT INDEX" in hd,
        "CastleSlot_HeroType" in rbf, True,
        "" if live_ok else f"hero rawcodes not 10-distinct: {f['heroes']}")

    # 4) spine: handler passes udg_CastleSlot_HeroType[i] as the CreateNUnits 2nd arg
    live_ok = all(h is not None for h in f["heroes"])   # every body spawns a hero
    row("spine:HeroType-2nd-arg", live_ok,
        SPINE_2ND_ARG in hd,
        "per-slot hero unit-type rawcode" in rbf, True,
        "" if live_ok else "a live body has no picker-owned hero spawn")

    # 5) non-conflation/villager: villager set DISJOINT from hero set (live + generated)
    live_heroes = set(h for h in f["heroes"] if h)
    live_vill = set(v for v in f["villagers"] if v)
    gen_disjoint = (bool(gen_hero) and bool(gen_vill)
                    and not (set(gen_hero) & set(gen_vill)))
    live_disjoint = bool(live_vill) and not (live_heroes & live_vill)
    live_ok = live_disjoint and gen_disjoint
    row("non-conflation:villager-disjoint", live_ok,
        "(taken-villager block) is DEFERRED by design" in hd,
        "already-taken fallback unit-type (human-ELSE, deferred)" in rbf, True,
        "" if live_ok
        else f"hero∩villager live={sorted(live_heroes & live_vill)} "
             f"gen={sorted(set(gen_hero) & set(gen_vill))}")

    # 6) non-conflation/neutral: Gawain's 'h012' is the SOLE neutral spawn, excluded from heroes
    all_neutrals = [c for nl in f["neutrals"] for c in nl]
    live_ok = (all_neutrals == ["h012"] and "h012" not in live_heroes)
    row("non-conflation:neutral-h012-excluded", live_ok,
        "h012" in hd and "neutral" in hd,
        False, False,
        "" if live_ok else f"neutral spawns = {all_neutrals} (expected exactly ['h012'])")

    # 7) ordering: every body has exactly [hero, villager], hero first (discrimination invariant)
    live_ok = all(f["orders"])
    bad = [HERO_FUNCS[i][1] for i, ok in enumerate(f["orders"]) if not ok]
    row("ordering:hero-before-villager", live_ok,
        SPINE_2ND_ARG in hd,
        False, False,
        "" if live_ok else f"bodies without exactly [hero,villager]: {bad}")

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
    """A synthetic (extract, runbook, handler, gen) quad satisfying every anchor — the
    selftest baseline + the fixtures each RED-catch mutates. Gawain's body carries the
    neutral 'h012' caster, so the OK fixture passing proves the parser EXCLUDES it."""
    heroes = ["Harf", "Hvwd", "Hjai", "Hant", "Hpb1",
              "Huth", "Hpb2", "Hart", "H013", "H014"]
    vills = ["n00S", "n00Q", "n00Q", "n00R", "n00R",
             "n00R", "n00S", "n00S", "n00R", "n00S"]
    bodies = []
    for idx, (func, _hero) in enumerate(HERO_FUNCS):
        head = f"function {func} takes nothing returns nothing\n"
        pre = ""
        if "Gawain" in func:
            pre = ("    call CreateNUnitsAtLoc(1, 'h012', Player(PLAYER_NEUTRAL_AGGRESSIVE), "
                   "GetRectCenter(gg_rct_Gawain), bj_UNIT_FACING)\n")
        hero = (f"    call CreateNUnitsAtLocFacingLocBJ(1, '{heroes[idx]}', "
                "GetOwningPlayer(GetTriggerUnit()), GetRectCenter(gg_rct_x), GetRectCenter(gg_rct_y))\n")
        vill = (f"        call CreateNUnitsAtLocFacingLocBJ(1, '{vills[idx]}', "
                "GetOwningPlayer(GetTriggerUnit()), GetRectCenter(gg_rct_x), GetUnitLoc(gg_unit_h005_1098))\n")
        bodies.append(head + pre + hero + vill + "endfunction\n")
    extract = "\n".join(bodies)
    gen = "function InitCastleSlotData takes nothing returns nothing\n"
    for i in range(10):
        gen += f"    set udg_CastleSlot_HeroType[{i}]='{heroes[i]}'\n"
    for i in range(10):
        gen += f"    set udg_CastleSlot_TakenVillager[{i}]='{vills[i]}'\n"
    gen += "endfunction\n"
    handler = (
        "//  Replaces the SHARED mechanics of the 10 hand-written Trig_<Hero>_Actions pick\n"
        "//  bodies ... that walks the udg_CastleSlot_* parallel arrays BY SLOT INDEX.\n"
        "//  (a) GAWAIN — spawn a neutral 'h012' caster ... DEFERRED to the ExtrasHook.\n"
        "//  The human-controlled ELSE (taken-villager block) is DEFERRED by design.\n"
        "    call CreateNUnitsAtLocFacingLocBJ(1, udg_CastleSlot_HeroType[i], picker, "
        "udg_CastleSlot_SpawnLoc[i], udg_CastleSlot_FaceLoc[i])\n"
    )
    runbook = (
        "## STEP 0\n"
        "| `CastleSlot_HeroType` | integer **array** | 0 | P2 | per-slot hero unit-type rawcode |\n"
        "| `CastleSlot_TakenVillager` | integer **array** | 0 | P2 | already-taken fallback unit-type (human-ELSE, deferred) |\n"
        "## STEP 2 — disable the 10 old `Trig_<Hero>_Actions`\n"
    )
    return extract, runbook, handler, gen


def selftest():
    print("=== SELFTEST: parser unit-tests + per-direction RED-catch (teeth) ===")
    extract, runbook, handler, gen = _synth_ok()

    f = live_facts(extract)
    assert not f["missing"], f["missing"]
    assert f["heroes"] == ["Harf", "Hvwd", "Hjai", "Hant", "Hpb1",
                           "Huth", "Hpb2", "Hart", "H013", "H014"], f["heroes"]
    assert [c for nl in f["neutrals"] for c in nl] == ["h012"], f["neutrals"]
    assert all(f["orders"]), f["orders"]
    assert gen_array(gen, "CastleSlot_HeroType")[4] == "Hpb1"

    base = all_rows(extract, runbook, handler, gen)
    base_ok = all(_passed(l, h, p, pr) for _, l, h, p, pr, _ in base)
    print(f"  baseline all-green                  : {base_ok}")
    assert base_ok, [r for r in base if not _passed(r[1], r[2], r[3], r[4])]

    def caught(rows, label):
        for lbl, l, h, p, pr, d in rows:
            if lbl == label:
                return not _passed(l, h, p, pr)
        return False

    # 1) LIVE: a hero body deleted -> bodies + per-slot trip
    bad = extract.replace("function Trig_Merlin_Actions takes nothing returns nothing",
                          "function Trig_GONE_Actions takes nothing returns nothing")
    c_bodies = caught(all_rows(bad, runbook, handler, gen), "bodies:present=10")

    # 2) LIVE: a hero rawcode mutated -> per-slot-faithful + distinct trip
    bad = extract.replace("call CreateNUnitsAtLocFacingLocBJ(1, 'Huth',",
                          "call CreateNUnitsAtLocFacingLocBJ(1, 'Hxxx',", 1)
    c_slot = caught(all_rows(bad, runbook, handler, gen), "herotype:per-slot-faithful")

    # 3) LIVE: two slots collapse to the same hero -> distinct trips
    bad = extract.replace("call CreateNUnitsAtLocFacingLocBJ(1, 'Hvwd',",
                          "call CreateNUnitsAtLocFacingLocBJ(1, 'Harf',", 1)
    c_distinct = caught(all_rows(bad, runbook, handler, gen), "herotype:10-distinct")

    # 4) LIVE: villager rawcode rewired to equal a hero (conflation) -> villager-disjoint trips
    bad = extract.replace("call CreateNUnitsAtLocFacingLocBJ(1, 'n00S',",
                          "call CreateNUnitsAtLocFacingLocBJ(1, 'Harf',", 1)
    c_vill = caught(all_rows(bad, runbook, handler, gen), "non-conflation:villager-disjoint")

    # 5) LIVE: Gawain's neutral 'h012' rewired to the picker -> 3 picker spawns; ordering +
    #    neutral-excluded trip (proves the neutral exclusion is load-bearing)
    bad = extract.replace(
        "call CreateNUnitsAtLoc(1, 'h012', Player(PLAYER_NEUTRAL_AGGRESSIVE),",
        "call CreateNUnitsAtLoc(1, 'h012', GetOwningPlayer(GetTriggerUnit()),", 1)
    c_neutral = caught(all_rows(bad, runbook, handler, gen),
                       "non-conflation:neutral-h012-excluded")

    # 6) LIVE: hero/villager order swapped in a body -> ordering still OK (2 picker), but
    #    per-slot-faithful trips because first-picker is now the villager
    bad = extract.replace(
        "    call CreateNUnitsAtLocFacingLocBJ(1, 'Harf', GetOwningPlayer(GetTriggerUnit()), GetRectCenter(gg_rct_x), GetRectCenter(gg_rct_y))\n"
        "        call CreateNUnitsAtLocFacingLocBJ(1, 'n00S', GetOwningPlayer(GetTriggerUnit()), GetRectCenter(gg_rct_x), GetUnitLoc(gg_unit_h005_1098))\n",
        "        call CreateNUnitsAtLocFacingLocBJ(1, 'n00S', GetOwningPlayer(GetTriggerUnit()), GetRectCenter(gg_rct_x), GetUnitLoc(gg_unit_h005_1098))\n"
        "    call CreateNUnitsAtLocFacingLocBJ(1, 'Harf', GetOwningPlayer(GetTriggerUnit()), GetRectCenter(gg_rct_x), GetRectCenter(gg_rct_y))\n", 1)
    c_order = caught(all_rows(bad, runbook, handler, gen), "herotype:per-slot-faithful")

    # 7) GEN drift: a generated HeroType value changed -> per-slot-faithful trips
    bad_g = gen.replace("set udg_CastleSlot_HeroType[7]='Hart'",
                        "set udg_CastleSlot_HeroType[7]='Hzzz'")
    c_gen = caught(all_rows(extract, runbook, handler, bad_g), "herotype:per-slot-faithful")

    # 8) GEN drift: a TakenVillager value set equal to a hero -> gen disjointness trips
    bad_g = gen.replace("set udg_CastleSlot_TakenVillager[0]='n00S'",
                        "set udg_CastleSlot_TakenVillager[0]='Harf'")
    c_gvill = caught(all_rows(extract, runbook, handler, bad_g),
                     "non-conflation:villager-disjoint")

    # 9) HANDLER drift: spine drops the HeroType 2nd arg -> spine + per-slot + distinct trip
    bad_h = handler.replace("udg_CastleSlot_HeroType[i]", "udg_WRONG_HeroType[i]")
    c_hsp = caught(all_rows(extract, runbook, bad_h, gen), "spine:HeroType-2nd-arg")

    # 10) HANDLER drift: header drops the taken-villager DEFERRED claim -> villager-disjoint trips
    bad_h = handler.replace("(taken-villager block) is DEFERRED by design",
                            "(taken-villager block) is on the spine")
    c_hvill = caught(all_rows(extract, runbook, bad_h, gen),
                     "non-conflation:villager-disjoint")

    # 11) PROSE drift: runbook drops the HeroType row description -> per-slot/spine prose trips
    bad_rb = runbook.replace("per-slot hero unit-type rawcode", "something else")
    c_prose = caught(all_rows(extract, bad_rb, handler, gen), "herotype:per-slot-faithful")

    # 12) PROSE drift: runbook drops the TakenVillager deferral cite -> villager-disjoint prose trips
    bad_rb = runbook.replace("already-taken fallback unit-type (human-ELSE, deferred)",
                             "always spawned")
    c_prvill = caught(all_rows(extract, bad_rb, handler, gen),
                      "non-conflation:villager-disjoint")

    checks = [
        ("live body deleted", c_bodies), ("live hero rawcode mutated", c_slot),
        ("live two slots collapse", c_distinct), ("live villager=hero conflation", c_vill),
        ("live neutral-h012 -> picker", c_neutral), ("live hero/villager swap", c_order),
        ("gen HeroType drift", c_gen), ("gen villager=hero", c_gvill),
        ("handler spine drift", c_hsp), ("handler deferred-claim drop", c_hvill),
        ("prose HeroType-row drop", c_prose), ("prose villager-cite drop", c_prvill),
    ]
    for name, val in checks:
        print(f"  {name:<30}caught : {val}")
    ok = base_ok and all(v for _, v in checks)
    print(f"\nSELFTEST {'PASS' if ok else 'FAIL'}  ({sum(v for _, v in checks)}/{len(checks)} teeth)")
    return 0 if ok else 3


def main():
    if "--selftest" in sys.argv:
        return selftest()
    for label, p in (("live extract", EXTRACT), ("runbook", RUNBOOK),
                     ("handler", HANDLER), ("generated data", GEN_DATA)):
        if not p.exists():
            print(f"FATAL: {label} not found: {p}")
            return 2

    raw = EXTRACT.read_bytes()
    md5 = hashlib.md5(raw).hexdigest()
    print(f"live extract : {EXTRACT}")
    print(f"  md5={md5}  (runbook pins {RUNBOOK_CLAIMED_MD5})")
    if md5 != RUNBOOK_CLAIMED_MD5:
        print("RESULT: FAIL — live extract md5 DRIFTED from the runbook-pinned hash; "
              "the per-slot HeroType identity cites are now suspect. Re-ground vs the new bake.")
        return 1

    extract_text = raw.decode("latin-1")
    runbook_text = RUNBOOK.read_text()
    handler_text = HANDLER.read_text()
    gen_text = GEN_DATA.read_text()
    rows = all_rows(extract_text, runbook_text, handler_text, gen_text)
    report(rows)

    fail = [(lbl, d) for lbl, l, h, p, pr, d in rows if not _passed(l, h, p, pr)]
    live_ok = sum(1 for _, l, _, _, _, _ in rows if l)
    hand_ok = sum(1 for _, _, h, _, _, _ in rows if h)
    prose_req = [r for r in rows if r[4]]
    prose_ok = sum(1 for _, _, _, p, pr, _ in rows if pr and p)
    print(f"\nanchors={len(rows)}  live={live_ok}/{len(rows)}  "
          f"handler={hand_ok}/{len(rows)}  prose={prose_ok}/{len(prose_req)}(required)  md5=OK")
    if fail:
        print("RESULT: FAIL — hero-select P2 per-slot HeroType identity drifted:")
        for lbl, d in fail:
            print(f"  - {lbl}: {d}")
        return 1
    print("RESULT: GREEN — the STEP-0 CastleSlot_HeroType per-slot hero identity is bound vs "
          "the md5-pinned extract: every slot's live FIRST picker-owned hero spawn equals the "
          "generated udg_CastleSlot_HeroType[i] (all 10 present + DISTINCT), the handler spine "
          "consumes it as the CreateNUnitsAtLocFacingLocBJ 2nd arg, and the runbook STEP-0 row "
          "describes it — while the deferred TakenVillager fallback (the 2nd picker spawn) and "
          "Gawain's neutral 'h012' caster are both proven DISJOINT/excluded from the hero set, "
          "so the data-driven collapse cannot silently spawn the wrong unit at a pedestal.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
