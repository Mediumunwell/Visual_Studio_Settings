#!/usr/bin/env python3
r"""
verify_hero_select_p2_spawnloc_faceloc_anchor.py
================================================================================
KOTR Hero-Select REDESIGN (Track 4) · P2 APPLY-RUNBOOK **STEP-2 SpawnLoc/FaceLoc
hero-spawn spine** <-> handler authority <-> live extract binder.
Built 2026-06-19 by KOTR Builder (engine claude-p).

WHY THIS GATE EXISTS (a real, uncovered seam on the STEP-2 apply path)
--------------------------------------------------------------------------------
`hero_select_p2_APPLY_RUNBOOK.md` STEP 2 tells the WE operator how the data-uniform
`CastleSlot_ApplyPick(i)` spine spawns each hero:
    "- **Fill `SpawnLoc`/`FaceLoc` per slot** from the new pedestal rect handles, e.g.
       `set udg_CastleSlot_SpawnLoc[i] = GetRectCenter(gg_rct_<Pedestal_i>)` and the
       matching facing point P1 reserved (for Kay, the stored facing loc reproduces its
       old `bj_UNIT_FACING`)."
That single bullet carries the most load-bearing op in the whole redesign — the hero
spawn — and makes several checkable claims the operator relies on before deleting the
10 old `Trig_<Hero>_Actions` triggers:
  1. the spine spawns via the UNIFIED `CreateNUnitsAtLocFacingLocBJ` API, passing
     `udg_CastleSlot_SpawnLoc[i]` (spawn point) + `udg_CastleSlot_FaceLoc[i]` (facing point),
  2. that unification is faithful because 9 of the 10 live pick bodies already spawn the
     hero via `CreateNUnitsAtLocFacingLocBJ`,
  3. the ONE divergent body — Sir Kay — spawns via plain `CreateNUnitsAtLoc` + the
     `bj_UNIT_FACING` constant, and the runbook claims a stored FaceLoc reproduces it,
  4. Kay is the SOLE divergence (Gawain's body also contains a `CreateNUnitsAtLoc` +
     `bj_UNIT_FACING`, but it is the NEUTRAL `'h012'` polymorph caster — owned by
     `Player(PLAYER_NEUTRAL_AGGRESSIVE)`, NOT the picker — so it is not a hero spawn and
     must NOT be miscounted as a second divergence).
If any of those drift, the operator could fill SpawnLoc/FaceLoc against the wrong API
contract, or "subsume" Kay's bj_UNIT_FACING when the body never used it, silently
spawning heroes at a null location or the wrong facing.

Yet NO existing gate binds THIS runbook bullet to the handler spine + live bodies:
  * `verify_hero_select_divergence_catalog_anchors.py` binds the **catalog .md**'s §2
    spawn-API divergence (9x FacingLocBJ, 1x Kay plain @ L49951) <-> live — it never
    reads the RUNBOOK STEP-2 fill bullet, nor the handler spine that consumes SpawnLoc/
    FaceLoc, so it cannot catch a runbook/handler that drifts from the catalog.
  * `verify_hero_select_p2_runbook_anchors.py` binds the runbook's reuse-global counts +
    the 10-pick-body line range + tail rawcodes — NOT this SpawnLoc/FaceLoc spawn spine.
  * `verify_hero_select_p2_loop.py` / `audit_hero_select_p2_equivalence.py` (fix_specs)
    compile + op-equivalence-prove the handler; they never read the runbook .md, so a
    runbook bullet that drifts from the spine they prove goes uncaught.
  * `verify_hero_select_p2_generated_j.py` / `verify_castleslot_global_contract.py` cover
    the materialized data + the STEP-0 `CastleSlot_*` contract — a different surface.

So this gate closes the seam the established Track-4 way: it binds the STEP-2 SpawnLoc/
FaceLoc prose <-> handler header + spine authority <-> live extract, both ways, against
the md5-pinned canonical extract — the twin of the init-call / hero-ref / ExtrasHook
binders shipped 2026-06-18.

WHAT IT CHECKS (read-only; touches no .w3x and no shippable .j)
--------------------------------------------------------------------------------
  0. md5 pin: the live extract still hashes to the runbook-pinned md5 (a re-bake trips it).
  1. all 10 hand-written hero pick bodies are present in the live extract.
  2. spawn-api: exactly 9 of the 10 hero spawns use CreateNUnitsAtLocFacingLocBJ — the API
     the spine unifies on — and the handler spine line + header say so + the runbook bullet
     describes the SpawnLoc/FaceLoc fill.
  3. spine 4th arg is udg_CastleSlot_SpawnLoc[i] (handler) <-> "set ...SpawnLoc[i] =
     GetRectCenter" (runbook) <-> every live hero spawn carries a spawn-point loc.
  4. spine 5th arg is udg_CastleSlot_FaceLoc[i] (handler) <-> "matching facing point"
     (runbook) <-> the 9 FacingLocBJ hero spawns each carry a facing loc.
  5. kay-divergence: Trig_Sir_Kay_Actions spawns its hero via plain CreateNUnitsAtLoc +
     bj_UNIT_FACING (live) <-> handler header names it <-> runbook "for Kay ... bj_UNIT_FACING".
  6. kay-is-sole-divergence: plain==exactly {Kay} (Gawain's neutral 'h012' excluded) (live)
     <-> handler "lone API divergence" <-> runbook "subsumes Kay".
  7. spine-comment: the handler spine comment states the subsumption "via FaceLoc"
     (handler-precise; live = Kay divergence confirmed).

Run:        python3 verify_hero_select_p2_spawnloc_faceloc_anchor.py
Self-test:  python3 verify_hero_select_p2_spawnloc_faceloc_anchor.py --selftest
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

# the md5 the runbook pins the canonical extract to (Grounding header) — same pin
# the sibling Track-4 binders use, so a re-bake trips them all together.
RUNBOOK_CLAIMED_MD5 = "967131658fd8d4fb27ee0d7f74e4bd22"

# the 10 hand-written hero pick bodies, in catalog order. `is_kay` flags the ONE the
# catalog/runbook call out as the lone spawn-API divergence (plain CreateNUnitsAtLoc).
HERO_FUNCS = [
    ("Trig_King_Arthur_Actions", "Arthur", False),
    ("Trig_Lady_Guinevere_Actions", "Guinevere", False),
    ("Trig_Lady_of_the_Lake_Actions", "Nimue", False),
    ("Trig_Merlin_Actions", "Merlin", False),
    ("Trig_Sir_Kay_Actions", "Kay", True),
    ("Trig_Sir_Percival_Actions", "Percival", False),
    ("Trig_Sir_Galahad_Actions", "Galahad", False),
    ("Trig_Sir_Lancelot_Actions", "Lancelot", False),
    ("Trig_Sir_Yvain_Actions", "Yvain", False),
    ("Trig_Sir_Gawain_Actions", "Gawain", False),
]

# the exact spine call the handler must carry (collapsed-whitespace form).
SPINE_CALL = ("CreateNUnitsAtLocFacingLocBJ(1, udg_CastleSlot_HeroType[i], picker, "
              "udg_CastleSlot_SpawnLoc[i], udg_CastleSlot_FaceLoc[i])")


def body_of(extract_text, func):
    """The body text of one Trig_<Hero>_Actions function, or None if gone."""
    m = re.search(
        r"function " + re.escape(func) + r" takes nothing returns nothing(.*?)\nendfunction",
        extract_text, re.DOTALL)
    return m.group(1) if m else None


def hero_spawn_line(body):
    """The HERO spawn line in a pick body: the first CreateNUnits* call owned by the
    PICKER (`GetOwningPlayer(GetTriggerUnit())`). This deliberately skips Gawain's
    neutral 'h012' caster (owned by Player(PLAYER_NEUTRAL_AGGRESSIVE)) and returns the
    real hero spawn, so the 'h012' bj_UNIT_FACING is never miscounted as a divergence."""
    if body is None:
        return None
    for raw in body.splitlines():
        s = raw.strip()
        if s.startswith("call CreateNUnits") and "GetOwningPlayer(GetTriggerUnit())" in s:
            return s
    return None


def live_facts(extract_text):
    """Per-body hero-spawn API facts. Every value is independently checkable so a single
    mutation trips exactly one anchor."""
    spawns = {}          # hero -> (api, uses_bj_unit_facing, has_spawn_loc, has_face_loc)
    missing = []
    for func, hero, _is_kay in HERO_FUNCS:
        line = hero_spawn_line(body_of(extract_text, func))
        if line is None:
            missing.append(hero)
            continue
        api = "FacingLocBJ" if "CreateNUnitsAtLocFacingLocBJ" in line else "plain"
        uses_bj = line.rstrip().endswith("bj_UNIT_FACING)")
        has_spawn_loc = ("GetRectCenter(" in line) or ("GetRandomLocInRect(" in line)
        # the 9 FacingLocBJ spawns carry a facing loc as the 5th arg (GetUnitLoc/GetRectCenter)
        has_face_loc = (api == "FacingLocBJ" and not uses_bj)
        spawns[hero] = (api, uses_bj, has_spawn_loc, has_face_loc)
    facinglocbj = sorted(h for h, v in spawns.items() if v[0] == "FacingLocBJ")
    plain = sorted(h for h, v in spawns.items() if v[0] == "plain")
    return {
        "n_found": len(spawns),
        "missing": missing,
        "spawns": spawns,
        "facinglocbj": facinglocbj,
        "plain": plain,
    }


def runbook_spawn_clause(rb):
    """The STEP-2 SpawnLoc/FaceLoc fill bullet, collapsed to single-spaced text for
    contiguous token matching; '' if gone."""
    m = re.search(r"\*\*Fill `SpawnLoc`/`FaceLoc` per slot\*\*.*?its old `bj_UNIT_FACING`\)",
                  rb, re.DOTALL)
    return re.sub(r"\s+", " ", m.group(0)) if m else ""


def all_rows(extract_text, runbook_text, handler_text):
    """Per-anchor rows: (label, live_ok, handler_ok, prose_ok, prose_required, detail)."""
    f = live_facts(extract_text)
    rbf = re.sub(r"\s+", " ", runbook_text)         # full runbook, normalized
    clause = runbook_spawn_clause(runbook_text)     # the STEP-2 fill bullet, normalized
    # normalize the handler: strip `//` line-markers + collapse whitespace so wrapped
    # header claims AND the real spine call both match contiguously.
    hd = re.sub(r"\s+", " ", re.sub(r"//+", " ", handler_text))
    rows = []

    def row(label, live_ok, handler_ok, prose_ok, prose_required, detail=""):
        rows.append((label, live_ok, handler_ok, prose_ok, prose_required, detail))

    # 1) all 10 hero pick bodies present
    live_ok = f["n_found"] == 10 and not f["missing"]
    row("bodies:present=10", live_ok,
        "10 hand-written Trig_<Hero>_Actions" in hd,
        "10 old `Trig_<Hero>_Actions`" in rbf, True,
        "" if live_ok else f"missing/!=10: found={f['n_found']} missing={f['missing']}")

    # 2) spawn-api: 9 of 10 hero spawns use the unified CreateNUnitsAtLocFacingLocBJ
    live_ok = len(f["facinglocbj"]) == 9
    row("spawn-api:9-facinglocbj", live_ok,
        SPINE_CALL in hd and "hero spawn UNIFIED on CreateNUnitsAtLocFacingLocBJ" in hd,
        ("SpawnLoc" in clause and "FaceLoc" in clause and "facing" in clause), True,
        "" if live_ok else f"live FacingLocBJ hero spawns = {f['facinglocbj']} (expected 9)")

    # 3) spine 4th arg = udg_CastleSlot_SpawnLoc[i]
    live_ok = (f["n_found"] == 10
               and all(v[2] for v in f["spawns"].values()))   # every hero spawn has a spawn loc
    row("spine-arg:SpawnLoc", live_ok,
        "udg_CastleSlot_SpawnLoc[i]" in hd and SPINE_CALL in hd,
        "udg_CastleSlot_SpawnLoc[i] = GetRectCenter" in clause, True,
        "" if live_ok else "a live hero spawn carries no GetRectCenter/GetRandomLocInRect spawn loc")

    # 4) spine 5th arg = udg_CastleSlot_FaceLoc[i]
    live_ok = (len(f["facinglocbj"]) == 9
               and all(f["spawns"][h][3] for h in f["facinglocbj"]))  # all 9 carry a facing loc
    row("spine-arg:FaceLoc", live_ok,
        "udg_CastleSlot_FaceLoc[i]" in hd and SPINE_CALL in hd,
        "facing point" in clause, True,
        "" if live_ok else "a FacingLocBJ hero spawn carries no facing loc 5th arg")

    # 5) Kay's hero spawn is plain CreateNUnitsAtLoc + bj_UNIT_FACING (the lone divergence)
    kay = f["spawns"].get("Kay")
    live_ok = kay is not None and kay[0] == "plain" and kay[1] is True
    row("kay-divergence:plain+facing", live_ok,
        "Kay: CreateNUnitsAtLoc + bj_UNIT_FACING" in hd and "Kay's bj_UNIT_FACING" in hd,
        "for Kay, the stored facing loc reproduces its old" in clause, True,
        "" if live_ok else f"live Kay hero spawn = {kay} (expected plain + bj_UNIT_FACING)")

    # 6) Kay is the SOLE divergence — Gawain's neutral 'h012' must NOT count
    live_ok = f["plain"] == ["Kay"]
    row("kay-is-sole-divergence", live_ok,
        "lone API divergence" in hd,
        "subsumes Kay" in rbf, True,
        "" if live_ok else f"live plain-spawn bodies = {f['plain']} (expected exactly ['Kay'])")

    # 7) the handler spine comment states the subsumption is via FaceLoc (handler-precise)
    row("spine-comment:subsumes-via-faceloc",
        kay is not None and kay[0] == "plain",
        "subsumes Kay's CreateNUnitsAtLoc+bj_UNIT_FACING via FaceLoc" in hd,
        False, False,
        "" if (kay is not None and kay[0] == "plain")
        else "live Kay spawn not plain — subsumption claim unverifiable")
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
    selftest baseline + the fixtures each RED-catch mutates. Gawain's body carries the
    neutral 'h012' caster BEFORE its hero spawn, so the OK fixture passing proves the
    parser correctly EXCLUDES it from the divergence count."""
    bodies = []
    for func, _hero, is_kay in HERO_FUNCS:
        head = f"function {func} takes nothing returns nothing\n"
        pre = ""
        if "Gawain" in func:
            pre = ("    call CreateNUnitsAtLoc(1, 'h012', Player(PLAYER_NEUTRAL_AGGRESSIVE), "
                   "GetRectCenter(gg_rct_Gawain), bj_UNIT_FACING)\n")
        if is_kay:
            spawn = ("    call CreateNUnitsAtLoc(1, 'Hpb1', GetOwningPlayer(GetTriggerUnit()), "
                     "GetRandomLocInRect(gg_rct_x), bj_UNIT_FACING)\n")
        else:
            spawn = ("    call CreateNUnitsAtLocFacingLocBJ(1, 'Hxxx', GetOwningPlayer(GetTriggerUnit()), "
                     "GetRectCenter(gg_rct_x), GetRectCenter(gg_rct_y))\n")
        avail = ("    call CreateNUnitsAtLocFacingLocBJ(1, 'n00S', GetOwningPlayer(GetTriggerUnit()), "
                 "GetRectCenter(gg_rct_x), GetUnitLoc(gg_unit_h005_1098))\n")
        bodies.append(head + pre + spawn + avail + "endfunction\n")
    extract = "\n".join(bodies)
    handler = (
        "//  Replaces the SHARED mechanics of the 10 hand-written Trig_<Hero>_Actions pick\n"
        "//  bodies. hero spawn UNIFIED on CreateNUnitsAtLocFacingLocBJ. The catalog's lone "
        "API divergence (Kay: CreateNUnitsAtLoc + bj_UNIT_FACING) is subsumed: the facing loc "
        "is stored per-slot in udg_CastleSlot_FaceLoc[i], so Kay's bj_UNIT_FACING becomes a "
        "stored facing point.\n"
        "    // hero spawn: unified API (subsumes Kay's CreateNUnitsAtLoc+bj_UNIT_FACING via FaceLoc)\n"
        "    call CreateNUnitsAtLocFacingLocBJ(1, udg_CastleSlot_HeroType[i], picker, "
        "udg_CastleSlot_SpawnLoc[i], udg_CastleSlot_FaceLoc[i])\n"
    )
    runbook = (
        "## STEP 2 — Wire the pedestals ... disable the 10 old `Trig_<Hero>_Actions`\n"
        "- **Fill `SpawnLoc`/`FaceLoc` per slot** from the new pedestal rect handles, e.g.\n"
        "  `set udg_CastleSlot_SpawnLoc[i] = GetRectCenter(gg_rct_<Pedestal_i>)` and the matching facing\n"
        "  point P1 reserved (for Kay, the stored facing loc reproduces its old `bj_UNIT_FACING`).\n"
        "| `CastleSlot_FaceLoc` | location array | (none) | P2 | hero facing point (subsumes Kay's `bj_UNIT_FACING`) |\n"
    )
    return extract, runbook, handler


def selftest():
    print("=== SELFTEST: parser unit-tests + per-direction RED-catch (teeth) ===")
    extract, runbook, handler = _synth_ok()

    # parser sanity
    f = live_facts(extract)
    assert f["n_found"] == 10 and not f["missing"], f
    assert len(f["facinglocbj"]) == 9, f["facinglocbj"]
    assert f["plain"] == ["Kay"], f["plain"]            # neutral 'h012' correctly excluded
    assert f["spawns"]["Kay"][1] is True, f["spawns"]["Kay"]

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
    bad = extract.replace("function Trig_Merlin_Actions takes nothing returns nothing", "function Trig_GONE_Actions takes nothing returns nothing")
    c_bodies = caught(all_rows(bad, runbook, handler), "bodies:present=10")

    # 2) LIVE: a FacingLocBJ hero spawn downgraded to plain -> 9-count + sole-divergence trip
    bad = extract.replace(
        "    call CreateNUnitsAtLocFacingLocBJ(1, 'Hxxx', GetOwningPlayer(GetTriggerUnit()), GetRectCenter(gg_rct_x), GetRectCenter(gg_rct_y))\n",
        "    call CreateNUnitsAtLoc(1, 'Hxxx', GetOwningPlayer(GetTriggerUnit()), GetRectCenter(gg_rct_x), bj_UNIT_FACING)\n",
        1)
    c_api = caught(all_rows(bad, runbook, handler), "spawn-api:9-facinglocbj")

    # 3) LIVE: Gawain's neutral 'h012' rewired to the picker -> would FALSELY become a 2nd
    #    divergence; sole-divergence anchor must catch it (proves the neutral exclusion is load-bearing)
    bad = extract.replace(
        "call CreateNUnitsAtLoc(1, 'h012', Player(PLAYER_NEUTRAL_AGGRESSIVE), GetRectCenter(gg_rct_Gawain), bj_UNIT_FACING)\n"
        "    call CreateNUnitsAtLocFacingLocBJ(1, 'Hxxx', GetOwningPlayer(GetTriggerUnit()), GetRectCenter(gg_rct_x), GetRectCenter(gg_rct_y))\n",
        "call CreateNUnitsAtLoc(1, 'h012', GetOwningPlayer(GetTriggerUnit()), GetRectCenter(gg_rct_Gawain), bj_UNIT_FACING)\n")
    c_sole = caught(all_rows(bad, runbook, handler), "kay-is-sole-divergence")

    # 4) LIVE: Kay's plain spawn upgraded to FacingLocBJ -> kay-divergence trips
    bad = extract.replace(
        "    call CreateNUnitsAtLoc(1, 'Hpb1', GetOwningPlayer(GetTriggerUnit()), GetRandomLocInRect(gg_rct_x), bj_UNIT_FACING)\n",
        "    call CreateNUnitsAtLocFacingLocBJ(1, 'Hpb1', GetOwningPlayer(GetTriggerUnit()), GetRectCenter(gg_rct_x), GetRectCenter(gg_rct_y))\n")
    c_kay = caught(all_rows(bad, runbook, handler), "kay-divergence:plain+facing")

    # 5) HANDLER drift: spine drops the SpawnLoc arg -> SpawnLoc anchor trips
    bad_h = handler.replace("udg_CastleSlot_SpawnLoc[i]", "udg_WRONG_SpawnLoc[i]")
    c_hsp = caught(all_rows(extract, runbook, bad_h), "spine-arg:SpawnLoc")

    # 6) HANDLER drift: header drops the "lone API divergence" claim -> sole-divergence trips
    bad_h = handler.replace("lone API divergence", "some API divergence")
    c_hlone = caught(all_rows(extract, runbook, bad_h), "kay-is-sole-divergence")

    # 7) PROSE drift: runbook drops the Kay subsumption clause -> kay-divergence trips
    bad_rb = runbook.replace("for Kay, the stored facing loc reproduces its old `bj_UNIT_FACING`", "for everyone")
    c_prose = caught(all_rows(extract, bad_rb, handler), "kay-divergence:plain+facing")

    # 8) PROSE drift: runbook drops the SpawnLoc fill cite -> SpawnLoc anchor trips
    bad_rb = runbook.replace("udg_CastleSlot_SpawnLoc[i] = GetRectCenter", "something else")
    c_prsp = caught(all_rows(extract, bad_rb, handler), "spine-arg:SpawnLoc")

    for name, val in [
        ("live body deleted", c_bodies), ("live FacingLocBJ->plain", c_api),
        ("live neutral-h012 -> picker", c_sole), ("live Kay->FacingLocBJ", c_kay),
        ("handler SpawnLoc drift", c_hsp), ("handler lone-divergence drift", c_hlone),
        ("prose Kay-clause drop", c_prose), ("prose SpawnLoc-cite drop", c_prsp),
    ]:
        print(f"  {name:<28}caught : {val}")
    ok = base_ok and all([c_bodies, c_api, c_sole, c_kay, c_hsp, c_hlone, c_prose, c_prsp])
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
              "the SpawnLoc/FaceLoc spawn-spine cites are now suspect. Re-ground vs the new bake.")
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
        print("RESULT: FAIL — hero-select P2 SpawnLoc/FaceLoc spawn spine drifted:")
        for lbl, d in fail:
            print(f"  - {lbl}: {d}")
        return 1
    print("RESULT: GREEN — the STEP-2 SpawnLoc/FaceLoc hero-spawn spine is bound vs the "
          "md5-pinned extract: all 10 live pick bodies are present, exactly 9 spawn the hero "
          "via CreateNUnitsAtLocFacingLocBJ and 1 (Sir Kay) via plain CreateNUnitsAtLoc + "
          "bj_UNIT_FACING — Kay the SOLE divergence (Gawain's neutral 'h012' correctly "
          "excluded) — and that structure matches the handler spine (SpawnLoc[i]/FaceLoc[i] "
          "args + 'subsumes Kay via FaceLoc' header) AND the runbook STEP-2 fill bullet. The "
          "operator's SpawnLoc/FaceLoc fill cannot silently drift from the bodies it replaces.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
