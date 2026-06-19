#!/usr/bin/env python3
r"""
verify_hero_select_p2_setplayername_anchor.py
================================================================================
KOTR Hero-Select REDESIGN (Track 4) · P2 **per-slot SETPLAYERNAME / computer-slot
rename op** <-> handler authority <-> live extract binder.
Built 2026-06-19 by KOTR Builder (engine claude-p).

WHY THIS GATE EXISTS (a real, uncovered seam on the P2 apply path)
--------------------------------------------------------------------------------
Every one of the 10 hand-written `Trig_<Hero>_Actions` pick bodies ends on the SAME
name-guard branch — the LAST data-uniform covered op on the apply spine. Each body
renames the picker's player slot at one fixed position (after the camera pan, at the
body's tail), but ONLY for COMPUTER-controlled slots:

    if ( Trig_<Hero>_Func0NNC() ) then
        call SetPlayerName(GetOwningPlayer(GetTriggerUnit()), "TRIGSTR_NNN")
        [+ Arthur only: call EnableTrigger(gg_trg_Flurry_AI)]
    else
        <human-slot path: taken-villager spawn / nothing — DEFERRED, see handler>
    endif

where each per-hero predicate `Trig_<Hero>_Func0NNC` is byte-identical once normalized
— the lone controller==COMPUTER test:

    function Trig_<Hero>_Func0NNC takes nothing returns boolean
        if ( not ( GetPlayerController(GetOwningPlayer(GetTriggerUnit())) == MAP_CONTROL_COMPUTER ) ) then
            return false
        endif
        return true
    endfunction

The handler collapses all 10 of those tails into ONE name-guarded spine line, turning
the lone per-hero datum (the name TRIGSTR) into per-slot data carried in
`udg_CastleSlot_NameStr[i]`:

    if ( GetPlayerController(picker) == MAP_CONTROL_COMPUTER ) then
        call SetPlayerName(picker, udg_CastleSlot_NameStr[i])
        ... // EnableTrig tail, also computer-only
    else
        // human-controlled slot: taken-villager path, DEFERRED by design
    endif

UNLIKE the sparse-scalar SpawnAbility op (only Yvain) and the windowed item/ally/
avail/rescue/invuln loops (variable per slot), the rename op is a DENSE, UNIFORM
per-slot scalar GUARDED by control flow: EVERY one of the 10 slots renames exactly
once, the only per-hero datum is the TRIGSTR, and the rename is fenced behind the
controller==COMPUTER test (human slots are NOT renamed — they get the villager path).
The handler makes several checkable claims the WE operator relies on before deleting
the 10 old bodies:
  1. EVERY pick body carries exactly 1 in-body SetPlayerName (10 total),
  2. the only per-hero datum is the name TRIGSTR (the 10 are distinct),
  3. the rename arg form is the arg-UNIFORM SetPlayerName(GetOwningPlayer(
     GetTriggerUnit()), <trigstr>) — only the TRIGSTR is per-slot data,
  4. EVERY rename sits in the TRUE branch of a body-named controller==COMPUTER
     guard whose predicate is the uniform test — i.e. computer slots ONLY.
If any of those drift, the operator could rename a HUMAN slot the body never renames
(the v2 name-guard control-flow fix this whole posture exists to prevent), drop a
slot's rename (silent — an empty NameStr compiles fine), or mis-bind the per-hero
TRIGSTR — and no other gate would catch it:
  * `verify_hero_select_p2_generated_j.py` / `verify_hero_select_p2_datatable.py`
    bind the MATERIALIZED NameStr column vs the catalog JSON — they prove the BAKED
    column is internally consistent, NOT that it matches the live bodies' rename op
    nor the handler's name-guard control-flow claims.
  * `verify_hero_select_p2_announce_anchor.py` / `_spawnability_anchor.py` /
    `_item_loadout_anchor.py` / `_avail_anchor.py` / `_allyrescueinvuln_anchor.py`
    bind the OTHER spine op families (a DIFFERENT op at a different position); none
    reads the SetPlayerName rename nor the controller==COMPUTER guard around it.
  * `verify_hero_select_p2_loop.py` / `audit_hero_select_p2_equivalence.py` compile
    + op-equivalence-prove the handler; they never read the runbook .md, so a
    runbook/header rename claim that drifts from the spine they prove goes uncaught.

So this gate closes the seam the established Track-4 way: it binds the runbook rename
claim <-> handler header + spine authority <-> live extract rename op, both ways,
against the md5-pinned canonical extract — the GUARDED dense-uniform-scalar sibling of
the item/avail/ally/rescue/invuln/spawn-ability/announce binders. CRUCIAL TEETH: the
live extract has MORE SetPlayerName calls (yomp/fruitcup test renames + the User-handle
class method) OUTSIDE the 10 pick bodies. A flat grep would inflate the family; this
gate BODY-SCOPES to the 10 hand-written pick bodies and follows the body-NAMED guard
predicate (never a flat grep) so only the real pick-path rename counts.

WHAT IT CHECKS (read-only; touches no .w3x and no shippable .j)
--------------------------------------------------------------------------------
  0. md5 pin: the live extract still hashes to the runbook-pinned md5 (a re-bake trips it).
  1. all 10 hand-written hero pick bodies are present in the live extract.
  2. every-slot: ALL 10 pick bodies carry exactly 1 in-body SetPlayerName (live,
     body-scoped) <-> handler "per-slot player name — LAST data-uniform covered op"
     <-> runbook "per-slot player-name TRIGSTR (computer-slot rename)".
  3. total: in-body SetPlayerName count == 10 (live) <-> handler "call SetPlayerName(
     picker, udg_CastleSlot_NameStr[i])" <-> runbook `CastleSlot_NameStr`.
  4. uniform player-expr: every in-body rename == SetPlayerName(GetOwningPlayer(
     GetTriggerUnit()), "<trigstr>") (only the TRIGSTR per-hero) (live) <-> handler
     "the per-slot player name (TRIGSTR string)" <-> runbook "computer-slot rename".
  5. distinct TRIGSTR: each body renames with a DISTINCT name TRIGSTR (the lone per-hero
     datum) (live) <-> handler spine "udg_CastleSlot_NameStr[i]" <-> runbook `CastleSlot_NameStr`.
  6. computer-guard: every rename sits in the TRUE branch of a body-named guard whose
     predicate is the uniform controller==COMPUTER test (computer slots ONLY) (live)
     <-> handler "if ( GetPlayerController(picker) == MAP_CONTROL_COMPUTER ) then" +
     "the rename/AI-arm tail runs ONLY for computer slots" <-> runbook "renames **only**
     computer-controlled slots (human slots get the villager path, not a rename)".

Run:        python3 verify_hero_select_p2_setplayername_anchor.py
Self-test:  python3 verify_hero_select_p2_setplayername_anchor.py --selftest
            (parser unit-tests + a per-direction RED-catch so the gate has teeth,
             incl. body-scoped exclusion of out-of-body SetPlayerName calls and a
             non-COMPUTER-guard RED-catch)
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

# DENSE-UNIFORM: every one of the 10 slots renames exactly once.
EXPECTED_OCCUPANTS = {h for _, h in HERO_FUNCS}             # all 10
EXPECTED_TOTAL = len(HERO_FUNCS)                            # 10

# the exact, arg-uniform rename signature the live pick bodies use
# (canonicalized: the name TRIGSTR -> "<trigstr>").
NAME_SIG = 'call SetPlayerName(GetOwningPlayer(GetTriggerUnit()), "<trigstr>")'

# the canonical controller==COMPUTER predicate body, normalized (ws-collapsed). Every
# per-hero Trig_<Hero>_Func0NNC guard predicate must equal this (the rename is fenced to
# computer slots; the live extract proves the 10 are byte-identical, md5 ad0a387c...).
PRED_CANON = ("if ( not ( GetPlayerController(GetOwningPlayer(GetTriggerUnit())) == "
              "MAP_CONTROL_COMPUTER ) ) then return false endif return true")

# the handler spine line (post // strip + whitespace collapse). The name-guard collapses
# the 10 per-hero tails; the per-hero TRIGSTR generalizes to udg_CastleSlot_NameStr[i].
NAME_SPINE = "call SetPlayerName(picker, udg_CastleSlot_NameStr[i])"
GUARD_SPINE = "if ( GetPlayerController(picker) == MAP_CONTROL_COMPUTER ) then"

# any SetPlayerName(<player-expr>, "<trigstr>") — player-expr captured so a non-uniform
# player arg is visible (NOT pre-filtered, else the uniform check would be tautological).
_NAME_RE = re.compile(r'call SetPlayerName\((.*?),\s*("TRIGSTR_[0-9]+")\)')
# the name-guard: an `if ( <body-named pred>() ) then` ... `else` block (the inlined
# `if ( (true) )` block can never match — its condition is not a Trig_*_Func*C() call).
_GUARD_RE = re.compile(
    r"if \( (Trig_[A-Za-z0-9_]+_Func[0-9]+C)\(\) \) then\r?\n(.*?)\r?\n    else",
    re.DOTALL)


def body_of(extract_text, func):
    """The body text of one function, or None if gone. Anchored on the exact
    `function <name> takes nothing returns ...` ... `endfunction` span so the out-of-body
    SetPlayerName calls (yomp/fruitcup, User-handle class method) can never leak in."""
    m = re.search(
        r"function " + re.escape(func) + r" takes nothing returns \w+(.*?)\nendfunction",
        extract_text, re.DOTALL)
    return m.group(1) if m else None


def _name_call(body):
    """The canonicalized in-body SetPlayerName one-liner (TRIGSTR -> "<trigstr>") and the
    raw TRIGSTR, or (None, None). Anchored on the trailing "TRIGSTR_NNNN") so the nested
    GetOwningPlayer(GetTriggerUnit()) parens don't truncate the match."""
    m = _NAME_RE.search(body)
    if not m:
        return None, None
    canon = re.sub(r'"TRIGSTR_[0-9]+"', '"<trigstr>"', m.group(0).strip())
    return canon, m.group(2)


def _name_count(body):
    """How many in-body SetPlayerName(..., "TRIGSTR_...") calls the body carries."""
    return len(_NAME_RE.findall(body))


def _guarded_by_computer(body, extract_text):
    """True iff this body's SetPlayerName sits in the TRUE branch of a body-named guard
    `if ( Trig_<Hero>_Func0NNC() ) then ... <rename> ... else` whose predicate function
    normalizes EXACTLY to the controller==COMPUTER test PRED_CANON. Following the body-NAMED
    predicate (never a flat grep) so only the real computer-only fence counts."""
    for pred, true_branch in _GUARD_RE.findall(body):
        if "call SetPlayerName(" not in true_branch:
            continue
        pb = body_of(extract_text, pred)
        if pb is None:
            continue
        if re.sub(r"\s+", " ", pb).strip() == PRED_CANON:
            return True
    return False


def live_facts(extract_text):
    """Per-body rename facts, BODY-SCOPED to the 10 pick bodies (and following each
    body-NAMED guard predicate, never a flat grep). Every value independently checkable so
    a single mutation trips exactly one anchor."""
    count = {}         # hero -> # in-body SetPlayerName calls
    rename = {}        # hero -> canonicalized SetPlayerName one-liner
    trigstr = {}       # hero -> name TRIGSTR literal
    guarded = {}       # hero -> rename is fenced behind the controller==COMPUTER guard
    missing = []
    for func, hero in HERO_FUNCS:
        b = body_of(extract_text, func)
        if b is None:
            missing.append(hero)
            continue
        count[hero] = _name_count(b)
        canon, ts = _name_call(b)
        rename[hero] = canon
        trigstr[hero] = ts
        guarded[hero] = _guarded_by_computer(b, extract_text)
    return {
        "n_found": len(count),
        "missing": missing,
        "count": count,
        "rename": rename,
        "trigstr": trigstr,
        "guarded": guarded,
    }


def _occupants(d):
    """heroes whose in-body rename count is >= 1."""
    return {h for h, v in d.items() if v}


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

    # 2) every-slot: ALL 10 carry exactly 1 in-body SetPlayerName (dense-uniform)
    occ = _occupants(f["count"])
    one_each = all(v == 1 for v in f["count"].values()) and len(f["count"]) == 10
    live_ok = occ == EXPECTED_OCCUPANTS and one_each
    row("name:every-slot=1", live_ok,
        "LAST data-uniform covered op" in hd,
        "per-slot player-name TRIGSTR (computer-slot rename)" in rbf, True,
        "" if live_ok else f"in-body SetPlayerName occupants={sorted(occ)} counts={f['count']}")

    # 3) total: in-body SetPlayerName count == 10
    total = sum(f["count"].values())
    live_ok = total == EXPECTED_TOTAL
    row("name:total=10", live_ok,
        NAME_SPINE in hd,
        "`CastleSlot_NameStr`" in rbf, True,
        "" if live_ok else f"live in-body SetPlayerName total={total} (expected {EXPECTED_TOTAL})")

    # 4) uniform player-expr: every in-body rename uses the SAME player arg
    #    GetOwningPlayer(GetTriggerUnit()) — only the per-hero TRIGSTR varies (real teeth:
    #    a body that renamed a different player expr is captured here and trips).
    renames = [r for r in f["rename"].values() if r is not None]
    live_ok = len(renames) == 10 and all(r == NAME_SIG for r in renames)
    row("name:uniform-player-expr", live_ok,
        "the per-slot player name (TRIGSTR string)" in hd,
        "per-slot player-name TRIGSTR (computer-slot rename)" in rbf, True,
        "" if live_ok else f"a live rename is not the uniform {NAME_SIG!r}: "
        f"{ {h: r for h, r in f['rename'].items() if r != NAME_SIG} }")

    # 5) distinct TRIGSTR: each body renames with a DISTINCT name TRIGSTR (per-hero datum)
    tss = [f["trigstr"][h] for _, h in HERO_FUNCS if f["trigstr"].get(h)]
    all_present = len(tss) == 10
    distinct = len(set(tss)) == 10
    live_ok = all_present and distinct
    row("name:distinct-trigstr", live_ok,
        "udg_CastleSlot_NameStr[i]" in hd,
        "`CastleSlot_NameStr`" in rbf, True,
        "" if live_ok else f"live per-hero name TRIGSTRs present={all_present} "
        f"distinct={distinct} ({tss})")

    # 6) computer-guard: every rename is fenced behind the controller==COMPUTER guard
    #    (the v2 name-guard control-flow faithfulness — human slots are NOT renamed).
    live_ok = all(f["guarded"].values()) and len(f["guarded"]) == 10
    row("name:computer-guard", live_ok,
        GUARD_SPINE in hd and "the rename/AI-arm tail runs ONLY for computer slots" in hd,
        "renames **only** computer-controlled slots (human slots get the villager path, "
        "not a rename)" in rbf, True,
        "" if live_ok else f"a live rename is NOT fenced behind the controller==COMPUTER guard: "
        f"{ {h: v for h, v in f['guarded'].items() if not v} }")
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
    selftest baseline + the fixtures each RED-catch mutates. Encodes the real dense-uniform
    rename distribution (every slot 1 rename, distinct per-hero TRIGSTR, fenced behind the
    controller==COMPUTER guard) AND plants OUT-OF-BODY SetPlayerName calls so the body-scope
    exclusion is exercised."""
    bodies = []
    for n, (func, hero) in enumerate(HERO_FUNCS):
        pred = f"Trig_{hero}_Func0{n}C"
        bodies.append(
            f"function {pred} takes nothing returns boolean\n"
            "    if ( not ( GetPlayerController(GetOwningPlayer(GetTriggerUnit())) == MAP_CONTROL_COMPUTER ) ) then\n"
            "        return false\n"
            "    endif\n"
            "    return true\n"
            "endfunction\n")
        bodies.append(
            f"function {func} takes nothing returns nothing\n"
            "    call PanCameraToTimedLocForPlayer(GetOwningPlayer(GetTriggerUnit()), GetRectCenter(gg_rct_X), 0.00)\n"
            f"    if ( {pred}() ) then\n"
            f'        call SetPlayerName(GetOwningPlayer(GetTriggerUnit()), "TRIGSTR_{839 + n}")\n'
            "    else\n"
            "    endif\n"
            "endfunction\n")
    # out-of-body renames (test-harness yomp/fruitcup + a class method) — MUST NOT count.
    bodies.append(
        "function Trig_Init_Test_Actions takes nothing returns nothing\n"
        '    call SetPlayerName(Player(0), "yomp")\n'
        '    call SetPlayerName(Player(1), "fruitcup")\n'
        "endfunction\n")
    extract = "\n".join(bodies)
    handler = (
        "//  Replaces the SHARED mechanics of the 10 hand-written Trig_<Hero>_Actions pick bodies.\n"
        "//     * the per-slot player name (TRIGSTR string)\n"
        "//  The guard is reproduced here so the rename/AI-arm tail runs ONLY for computer slots.\n"
        "//  per-slot player name — LAST data-uniform covered op (set inside the name-guard TRUE branch)\n"
        "    if ( GetPlayerController(picker) == MAP_CONTROL_COMPUTER ) then\n"
        "        call SetPlayerName(picker, udg_CastleSlot_NameStr[i])\n"
        "    else\n"
        "    endif\n"
    )
    runbook = (
        "## STEP 2 — Wire the pedestals ... the 10 hand-written pick bodies\n"
        "| `CastleSlot_NameStr` | string **array** | (empty) | P2 | per-slot player-name TRIGSTR (computer-slot rename) |\n"
        "Smoke: ... pans the picker's camera to the appear rect, broadcasts the right announce line "
        "to all players, renames **only** computer-controlled slots (human slots get the villager path, "
        "not a rename), arms Arthur's Flurry AI ...\n"
    )
    return extract, runbook, handler


def selftest():
    print("=== SELFTEST: parser unit-tests + per-direction RED-catch (teeth) ===")
    extract, runbook, handler = _synth_ok()

    # parser sanity (body-scoped: the out-of-body yomp/fruitcup func is NOT in HERO_FUNCS)
    f = live_facts(extract)
    assert f["n_found"] == 10 and not f["missing"], f
    assert _occupants(f["count"]) == EXPECTED_OCCUPANTS, _occupants(f["count"])
    assert sum(f["count"].values()) == EXPECTED_TOTAL, f["count"]
    assert all(r == NAME_SIG for r in f["rename"].values()), f["rename"]
    assert len({f["trigstr"][h] for _, h in HERO_FUNCS}) == 10, f["trigstr"]
    assert all(f["guarded"].values()), f["guarded"]

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

    # 2) LIVE: drop a slot's rename -> every-slot + total + guard trip
    bad = re.sub(
        r'        call SetPlayerName\(GetOwningPlayer\(GetTriggerUnit\(\)\), "TRIGSTR_839"\)\n',
        "", extract)
    c_every = caught(all_rows(bad, runbook, handler), "name:every-slot=1")
    c_total = caught(all_rows(bad, runbook, handler), "name:total=10")

    # 3) LIVE: a slot gets a SECOND in-body rename -> every-slot trips (not exactly 1)
    bad = extract.replace(
        '        call SetPlayerName(GetOwningPlayer(GetTriggerUnit()), "TRIGSTR_842")\n',
        '        call SetPlayerName(GetOwningPlayer(GetTriggerUnit()), "TRIGSTR_842")\n'
        '        call SetPlayerName(GetOwningPlayer(GetTriggerUnit()), "TRIGSTR_9000")\n')
    c_every2 = caught(all_rows(bad, runbook, handler), "name:every-slot=1")

    # 4) LIVE: two heroes share a TRIGSTR -> distinct trips
    bad = extract.replace('"TRIGSTR_840"', '"TRIGSTR_839"')   # Guinevere == Arthur
    c_distinct = caught(all_rows(bad, runbook, handler), "name:distinct-trigstr")

    # 5) LIVE: a rename uses a different player expr -> uniform-player-expr trips
    bad = extract.replace(
        'call SetPlayerName(GetOwningPlayer(GetTriggerUnit()), "TRIGSTR_841")',
        'call SetPlayerName(Player(5), "TRIGSTR_841")', 1)
    c_uni = caught(all_rows(bad, runbook, handler), "name:uniform-player-expr")

    # 6) LIVE: a rename's guard predicate is NOT the controller==COMPUTER test -> guard trips
    bad = extract.replace(
        "function Trig_Galahad_Func06C takes nothing returns boolean\n"
        "    if ( not ( GetPlayerController(GetOwningPlayer(GetTriggerUnit())) == MAP_CONTROL_COMPUTER ) ) then\n"
        "        return false\n"
        "    endif\n"
        "    return true\n"
        "endfunction\n",
        "function Trig_Galahad_Func06C takes nothing returns boolean\n"
        "    return true\n"
        "endfunction\n")
    c_guard = caught(all_rows(bad, runbook, handler), "name:computer-guard")

    # 7) LIVE: a rename is moved OUT of the guard (renames unconditionally) -> guard trips
    bad = extract.replace(
        "    if ( Trig_Kay_Func04C() ) then\n"
        '        call SetPlayerName(GetOwningPlayer(GetTriggerUnit()), "TRIGSTR_843")\n'
        "    else\n"
        "    endif\n",
        '    call SetPlayerName(GetOwningPlayer(GetTriggerUnit()), "TRIGSTR_843")\n')
    c_guard2 = caught(all_rows(bad, runbook, handler), "name:computer-guard")

    # 8) BODY-SCOPE TEETH: plant ANOTHER out-of-body rename (a func NOT in HERO_FUNCS). A
    #    correctly body-scoped gate must IGNORE it — total/every-slot stay GREEN. (If scoping
    #    regressed to a flat grep, this extra rename would inflate the family and trip.)
    bad = extract + (
        "\nfunction Trig_Extra_Quest_Actions takes nothing returns nothing\n"
        '    call SetPlayerName(Player(3), "TRIGSTR_9999")\n'
        "endfunction\n")
    c_scope = (not caught(all_rows(bad, runbook, handler), "name:total=10")
               and not caught(all_rows(bad, runbook, handler), "name:every-slot=1"))

    # 9) HANDLER drift: spine drops the NameStr rename line -> total trips
    bad_h = handler.replace(NAME_SPINE, "call SetPlayerName(picker, udg_WRONG_NameStr[i])")
    c_htot = caught(all_rows(extract, runbook, bad_h), "name:total=10")

    # 10) HANDLER drift: spine drops the controller==COMPUTER guard -> guard trips
    bad_h = handler.replace(GUARD_SPINE, "if ( true ) then")
    c_hguard = caught(all_rows(extract, runbook, bad_h), "name:computer-guard")

    # 11) HANDLER drift: header drops the NameStr datum claim -> distinct trips
    bad_h = handler.replace("udg_CastleSlot_NameStr[i]", "udg_CastleSlot_WrongStr[i]")
    c_hdist = caught(all_rows(extract, runbook, bad_h), "name:distinct-trigstr")

    # 12) PROSE drift: runbook drops the computer-slot-rename row -> every-slot trips
    bad_rb = runbook.replace("per-slot player-name TRIGSTR (computer-slot rename)",
                             "per-slot player-name (some other dim)")
    c_prose = caught(all_rows(extract, bad_rb, handler), "name:every-slot=1")

    # 13) PROSE drift: runbook drops the "renames only computer-controlled" claim -> guard trips
    bad_rb = runbook.replace(
        "renames **only** computer-controlled slots (human slots get the villager path, not a rename)",
        "renames all slots")
    c_prguard = caught(all_rows(extract, bad_rb, handler), "name:computer-guard")

    for name, val in [
        ("live body deleted", c_bodies), ("live drop rename every-slot", c_every),
        ("live drop rename total", c_total), ("live double rename", c_every2),
        ("live shared TRIGSTR (distinct)", c_distinct), ("live non-uniform player-expr", c_uni),
        ("live non-COMPUTER predicate (guard)", c_guard),
        ("live rename out of guard (guard)", c_guard2),
        ("body-scope holds (out-of-body ignored)", c_scope),
        ("handler NameStr-spine drift", c_htot), ("handler guard drift", c_hguard),
        ("handler NameStr-datum drift", c_hdist),
        ("prose NameStr-row drop", c_prose), ("prose computer-only-claim drop", c_prguard),
    ]:
        print(f"  {name:<42}caught : {val}")
    ok = base_ok and all([c_bodies, c_every, c_total, c_every2, c_distinct, c_uni, c_guard,
                          c_guard2, c_scope, c_htot, c_hguard, c_hdist, c_prose, c_prguard])
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
              "the rename op cites are now suspect. Re-ground vs the new bake.")
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
        print("RESULT: FAIL — hero-select P2 SetPlayerName/computer-rename op drifted:")
        for lbl, d in fail:
            print(f"  - {lbl}: {d}")
        return 1
    print("RESULT: GREEN — the per-slot computer-slot rename is bound vs the md5-pinned extract: all "
          "10 live pick bodies are present; EVERY slot carries exactly 1 in-body SetPlayerName (10 "
          "total — body-scoped past the out-of-body yomp/fruitcup + User-handle SetPlayerName calls, "
          "following each body-NAMED guard predicate never a flat grep); each renames with a DISTINCT "
          "name TRIGSTR through the arg-uniform SetPlayerName(GetOwningPlayer(GetTriggerUnit()), "
          "<trigstr>), and EVERY rename is fenced in the TRUE branch of a body-named "
          "controller==COMPUTER guard whose predicate is the uniform test (computer slots ONLY) — "
          "matching the handler's collapse to ONE name-guarded SetPlayerName(picker, "
          "udg_CastleSlot_NameStr[i]) under if (GetPlayerController(picker)==MAP_CONTROL_COMPUTER) AND "
          "the runbook NameStr 'computer-slot rename' / 'renames only computer-controlled slots' "
          "claims. The operator's STEP-1 NameStr column cannot silently drift from the bodies it "
          "replaces, and the v2 name-guard (no rename leaking onto human slots) is locked.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
