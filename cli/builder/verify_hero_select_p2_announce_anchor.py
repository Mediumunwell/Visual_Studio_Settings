#!/usr/bin/env python3
r"""
verify_hero_select_p2_announce_anchor.py
================================================================================
KOTR Hero-Select REDESIGN (Track 4) · P2 **per-pick ANNOUNCE / ForForce broadcast op**
<-> handler authority <-> live extract binder.
Built 2026-06-19 by KOTR Builder (engine claude-p).

WHY THIS GATE EXISTS (a real, uncovered seam on the P2 apply path)
--------------------------------------------------------------------------------
Every one of the 10 hand-written `Trig_<Hero>_Actions` pick bodies broadcasts a
per-hero announce line at one fixed position (after SaveHero, before SelectHero):

    call ForForce(GetPlayersByMapControl(MAP_CONTROL_USER), function Trig_<Hero>_Func0NNA)

and each per-hero callback `Trig_<Hero>_Func0NNA` ends with the SAME force+duration
display, differing ONLY in the announce TRIGSTR:

    call DisplayTimedTextToForce(GetForceOfPlayer(GetOwningPlayer(udg_SaveTempUnit)), 5.00, "TRIGSTR_NNNN")

The handler collapses all 10 of those callbacks into ONE shared
`CastleSlot_AnnounceForForce`, and turns the lone per-hero datum (the announce
TRIGSTR) into per-slot data carried in `udg_CastleSlot_AnnounceStr[i]`. The spine
publishes the slot's TRIGSTR through the scratch global `udg_CastleSlot_AnnounceCur`
immediately before the ForForce, so the shared callback reads it:

    set udg_CastleSlot_AnnounceCur = udg_CastleSlot_AnnounceStr[i]
    call ForForce(GetPlayersByMapControl(MAP_CONTROL_USER), function CastleSlot_AnnounceForForce)
        ... // callback: DisplayTimedTextToForce(..., 5.00, udg_CastleSlot_AnnounceCur)

UNLIKE the sparse-scalar SpawnAbility op (only Yvain) and the windowed item/ally/
avail/rescue/invuln loops (variable per slot), the announce op is a DENSE, UNIFORM
per-slot scalar: EVERY one of the 10 slots carries exactly one broadcast, and the
only per-hero datum is the TRIGSTR. The handler header makes several checkable
claims the WE operator relies on before deleting the 10 old bodies:
  1. EVERY pick body carries exactly 1 in-body announce ForForce (10 total),
  2. the per-hero callbacks collapse to ONE shared `CastleSlot_AnnounceForForce`,
  3. the only per-hero datum is the announce TRIGSTR (the 10 are distinct),
  4. the broadcast is the arg-UNIFORM ForForce(GetPlayersByMapControl(
     MAP_CONTROL_USER), function <cb>) and the display the arg-UNIFORM
     DisplayTimedTextToForce(GetForceOfPlayer(GetOwningPlayer(udg_SaveTempUnit)),
     5.00, <trigstr>) — only the callback / TRIGSTR is per-slot data.
If any of those drift, the operator could drop a slot's announce line (silent — the
table compiles fine with an empty AnnounceStr), mis-route the broadcast force, or
mistake the shared callback for per-hero logic — and no other gate would catch it:
  * `verify_hero_select_p2_generated_j.py` / `verify_hero_select_p2_datatable.py`
    bind the MATERIALIZED AnnounceStr column vs the catalog JSON — they prove the
    BAKED column is internally consistent, NOT that it matches the live bodies'
    announce op nor the handler header's natural-language claims.
  * `verify_hero_select_p2_spawnability_anchor.py` / `_item_loadout_anchor.py` /
    `_avail_anchor.py` / `_allyrescueinvuln_anchor.py` bind the OTHER spine op
    families (a DIFFERENT op at a different position); none reads the announce
    broadcast.
  * `verify_hero_select_p2_loop.py` / `audit_hero_select_p2_equivalence.py` compile
    + op-equivalence-prove the handler; they never read the runbook .md, so a
    runbook/header announce claim that drifts from the spine they prove goes uncaught.

So this gate closes the seam the established Track-4 way: it binds the runbook
announce claim <-> handler header + spine authority <-> live extract announce op,
both ways, against the md5-pinned canonical extract — the dense-uniform-scalar
sibling of the item/avail/ally/rescue/invuln/spawn-ability binders. CRUCIAL TEETH:
the live extract has MANY more ForForce(MAP_CONTROL_USER, function ...) broadcasts
(43 total map-wide) and DisplayTimedTextToForce calls (33 total) OUTSIDE the 10
pick bodies (quest/portal/invasion systems). A flat grep would inflate the family;
this gate BODY-SCOPES to the 10 hand-written pick bodies and follows the body-NAMED
callback (never a flat TRIGSTR grep) so only the real pick-path announce counts.

WHAT IT CHECKS (read-only; touches no .w3x and no shippable .j)
--------------------------------------------------------------------------------
  0. md5 pin: the live extract still hashes to the runbook-pinned md5 (a re-bake trips it).
  1. all 10 hand-written hero pick bodies are present in the live extract.
  2. every-slot: ALL 10 pick bodies carry exactly 1 in-body announce ForForce (live,
     body-scoped) <-> handler "every body's ForForce(...function Trig_<Hero>_Func0NNA)"
     <-> runbook "per-pick broadcast TRIGSTR (ForForce dim)".
  3. total: in-body announce ForForce count == 10 (live) <-> handler "The 10 callbacks
     collapse to the one shared CastleSlot_AnnounceForForce" <-> runbook `CastleSlot_AnnounceStr`.
  4. ForForce uniform: every in-body announce ForForce == ForForce(GetPlayersByMapControl(
     MAP_CONTROL_USER), function <cb>) (live) <-> handler spine ForForce(...,
     function CastleSlot_AnnounceForForce) <-> runbook "ForForce dim".
  5. callback collapse + per-hero TRIGSTR: each body-named callback carries a
     DisplayTimedTextToForce TRIGSTR, and the 10 are DISTINCT (the lone per-hero datum)
     (live) <-> handler "the per-hero announce TRIGSTR is the only datum, carried per-slot
     in udg_CastleSlot_AnnounceStr[i]" <-> runbook `CastleSlot_AnnounceStr`.
  6. display uniform: every callback display == DisplayTimedTextToForce(GetForceOfPlayer(
     GetOwningPlayer(udg_SaveTempUnit)), 5.00, "<trigstr>") (force+duration uniform; only
     TRIGSTR per-hero) (live) <-> handler callback DisplayTimedTextToForce(...,
     udg_CastleSlot_AnnounceCur) <-> runbook "broadcasts ... the right announce line to all players".
  7. AnnounceCur indirection: every live callback hard-codes a LITERAL TRIGSTR (proving the
     redesign's per-slot AnnounceStr[i] -> AnnounceCur indirection faithfully generalizes the
     per-callback literal) (live) <-> handler "set udg_CastleSlot_AnnounceCur =
     udg_CastleSlot_AnnounceStr[i]" + "rides udg_CastleSlot_AnnounceCur, set by ApplyPick just
     before the ForForce" <-> runbook `CastleSlot_AnnounceCur` "scratch: announce of the slot picked NOW".

Run:        python3 verify_hero_select_p2_announce_anchor.py
Self-test:  python3 verify_hero_select_p2_announce_anchor.py --selftest
            (parser unit-tests + a per-direction RED-catch so the gate has teeth,
             incl. body-scoped exclusion of out-of-body ForForce/DisplayTimedTextToForce calls)
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

# DENSE-UNIFORM: every one of the 10 slots carries exactly one announce broadcast.
EXPECTED_OCCUPANTS = {h for _, h in HERO_FUNCS}             # all 10
EXPECTED_TOTAL = len(HERO_FUNCS)                            # 10

# the exact, arg-uniform display signature the live pick bodies' callbacks use
# (canonicalized: the announce TRIGSTR -> "<trigstr>").
DISPLAY_SIG = ('call DisplayTimedTextToForce(GetForceOfPlayer(GetOwningPlayer('
               'udg_SaveTempUnit)), 5.00, "<trigstr>")')

# the handler spine lines (post // strip + whitespace collapse). The shared callback +
# AnnounceCur generalize the 10 per-hero callbacks + literal TRIGSTRs.
ANNOUNCE_FORFORCE_SPINE = ("ForForce(GetPlayersByMapControl(MAP_CONTROL_USER), "
                           "function CastleSlot_AnnounceForForce)")
DISPLAY_SPINE = ("DisplayTimedTextToForce(GetForceOfPlayer(GetOwningPlayer(udg_SaveTempUnit)), "
                 "5.00, udg_CastleSlot_AnnounceCur)")

# the canonical user-force expression every live announce broadcast must use.
USER_FORCE = "GetPlayersByMapControl(MAP_CONTROL_USER)"

# any ForForce(<force-expr>, function <cb>) — force-expr captured so a non-uniform force is
# visible (NOT pre-filtered to MCU, else the uniform check would be tautological).
_ANY_FORFORCE_RE = re.compile(r"call ForForce\((.+?), function ([A-Za-z0-9_]+)\)")


def body_of(extract_text, func):
    """The body text of one function, or None if gone. Anchored on the exact
    `function <name> takes nothing returns nothing` ... `endfunction` span so the
    abundant out-of-body ForForce / DisplayTimedTextToForce calls can never leak in."""
    m = re.search(
        r"function " + re.escape(func) + r" takes nothing returns nothing(.*?)\nendfunction",
        extract_text, re.DOTALL)
    return m.group(1) if m else None


def _announce_forforce(body, extract_text):
    """Every in-body ForForce that ROUTES TO AN ANNOUNCE callback (one whose own body holds a
    DisplayTimedTextToForce), as (force_expr, cb_name). Following the body-NAMED callback —
    never a flat grep — so quest/portal ForForce broadcasts outside the pick path can't leak."""
    out = []
    for force, cb in _ANY_FORFORCE_RE.findall(body):
        cbb = body_of(extract_text, cb)
        if cbb is not None and "DisplayTimedTextToForce" in cbb:
            out.append((force, cb))
    return out


def _display_trigstr(cb_body):
    """The TRIGSTR literal from a callback's DisplayTimedTextToForce, or None."""
    m = re.search(r'DisplayTimedTextToForce\([^\n]*?,\s*("TRIGSTR_[0-9]+")\s*\)', cb_body)
    return m.group(1) if m else None


def _display_call(cb_body):
    """The canonicalized DisplayTimedTextToForce one-liner (TRIGSTR -> "<trigstr>"), or None.
    Anchored on the trailing "TRIGSTR_NNNN") so the nested GetForceOfPlayer(GetOwningPlayer(...))
    parens don't truncate the match (a non-greedy `)` stops at the first inner close)."""
    m = re.search(r'call DisplayTimedTextToForce\([^\n]*"TRIGSTR_[0-9]+"\)', cb_body)
    if not m:
        return None
    return re.sub(r'"TRIGSTR_[0-9]+"', '"<trigstr>"', m.group(0).strip())


def live_facts(extract_text):
    """Per-body announce facts, BODY-SCOPED to the 10 pick bodies (and following each
    body-NAMED callback, never a flat grep). Every value independently checkable so a
    single mutation trips exactly one anchor."""
    forces = {}        # hero -> [force_expr of each in-body announce ForForce]
    callbacks = {}     # hero -> [cb_name of each in-body announce ForForce]
    trigstr = {}       # hero -> announce TRIGSTR literal (from the body-named callback)
    display = {}       # hero -> canonicalized DisplayTimedTextToForce one-liner
    literal_ok = {}    # hero -> the callback hard-codes a literal TRIGSTR (not a var)
    missing = []
    for func, hero in HERO_FUNCS:
        b = body_of(extract_text, func)
        if b is None:
            missing.append(hero)
            continue
        ann = _announce_forforce(b, extract_text)
        forces[hero] = [fc for fc, _ in ann]
        callbacks[hero] = [cb for _, cb in ann]
        # resolve the FIRST body-named announce callback for the per-hero TRIGSTR/display.
        ts, disp, lit = None, None, False
        if callbacks[hero]:
            cbb = body_of(extract_text, callbacks[hero][0])
            ts = _display_trigstr(cbb)
            disp = _display_call(cbb)
            lit = ts is not None
        trigstr[hero] = ts
        display[hero] = disp
        literal_ok[hero] = lit
    return {
        "n_found": len(callbacks),
        "missing": missing,
        "forces": forces,
        "callbacks": callbacks,
        "trigstr": trigstr,
        "display": display,
        "literal_ok": literal_ok,
    }


def _occupants(d):
    """heroes whose announce-ForForce list is non-empty."""
    return {h for h, v in d.items() if v}


def _all_equal(lists_by_hero, want):
    """True iff every element across every body equals `want` (and >=1 exists)."""
    seen = False
    for vals in lists_by_hero.values():
        for v in vals:
            seen = True
            if v != want:
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

    # 2) every-slot: ALL 10 carry exactly 1 in-body announce ForForce (dense-uniform)
    occ = _occupants(f["callbacks"])
    one_each = all(len(v) == 1 for v in f["callbacks"].values()) and len(f["callbacks"]) == 10
    live_ok = occ == EXPECTED_OCCUPANTS and one_each
    row("announce:every-slot=1", live_ok,
        "ForForce(GetPlayersByMapControl(MAP_CONTROL_USER), function Trig_<Hero>_Func0NNA)" in hd,
        "per-pick broadcast TRIGSTR (ForForce dim)" in rbf, True,
        "" if live_ok else f"in-body announce-ForForce occupants={sorted(occ)} "
        f"counts={ {h: len(v) for h, v in f['callbacks'].items()} }")

    # 3) total: in-body announce ForForce count == 10
    total = sum(len(v) for v in f["callbacks"].values())
    live_ok = total == EXPECTED_TOTAL
    row("announce:total=10", live_ok,
        "The 10 callbacks collapse to the one shared CastleSlot_AnnounceForForce" in hd,
        "`CastleSlot_AnnounceStr`" in rbf, True,
        "" if live_ok else f"live in-body announce-ForForce total={total} (expected {EXPECTED_TOTAL})")

    # 4) ForForce uniform: every in-body announce ForForce broadcasts over the SAME user force
    #    GetPlayersByMapControl(MAP_CONTROL_USER) — only the per-hero callback varies (real
    #    teeth: a body that announced over a different force is captured here and trips).
    live_ok = _all_equal(f["forces"], USER_FORCE)
    row("announce:uniform-forforce-spine", live_ok,
        ANNOUNCE_FORFORCE_SPINE in hd,
        "per-pick broadcast TRIGSTR (ForForce dim)" in rbf, True,
        "" if live_ok else f"a live announce ForForce is not over the uniform user force "
        f"{USER_FORCE}: { {h: v for h, v in f['forces'].items() if any(x != USER_FORCE for x in v)} }")

    # 5) callback collapse + per-hero TRIGSTR distinct (the lone per-hero datum)
    tss = [f["trigstr"][h] for _, h in HERO_FUNCS if f["trigstr"].get(h)]
    all_present = len(tss) == 10
    distinct = len(set(tss)) == 10
    live_ok = all_present and distinct
    row("announce:callback-collapse+distinct-trigstr", live_ok,
        "the per-hero announce TRIGSTR is the only datum, carried per-slot in "
        "udg_CastleSlot_AnnounceStr[i]" in hd
        and "function CastleSlot_AnnounceForForce takes nothing returns nothing" in hd,
        "`CastleSlot_AnnounceStr`" in rbf, True,
        "" if live_ok else f"live per-hero TRIGSTRs present={all_present} distinct={distinct} "
        f"({tss})")

    # 6) display uniform: force+duration uniform, only the TRIGSTR per-hero
    live_ok = (all(d == DISPLAY_SIG for d in f["display"].values() if d is not None)
               and sum(1 for d in f["display"].values() if d is not None) == 10)
    row("announce:uniform-display-spine", live_ok,
        DISPLAY_SPINE in hd,
        "broadcasts" in rbf and "the right announce line to all players" in rbf, True,
        "" if live_ok else f"a live announce display is not the uniform "
        f"DisplayTimedTextToForce(...,5.00,\"<trigstr>\"): { {h: d for h, d in f['display'].items() if d != DISPLAY_SIG} }")

    # 7) AnnounceCur indirection: every live callback hard-codes a LITERAL TRIGSTR
    live_ok = all(f["literal_ok"].values()) and len(f["literal_ok"]) == 10
    row("announce:literal->announcecur-indirection", live_ok,
        "set udg_CastleSlot_AnnounceCur = udg_CastleSlot_AnnounceStr[i]" in hd
        and "rides udg_CastleSlot_AnnounceCur, set by ApplyPick just before the ForForce" in hd,
        "scratch: announce of the slot picked NOW" in rbf, True,
        "" if live_ok else f"a live callback does not hard-code a literal TRIGSTR: "
        f"{ {h: v for h, v in f['literal_ok'].items() if not v} }")
    return rows


def _passed(live_ok, handler_ok, prose_ok, prose_required):
    return bool(live_ok) and bool(handler_ok) and (bool(prose_ok) or not prose_required)


def report(rows):
    print(f"{'ANCHOR':<46}{'LIVE':<8}{'HANDLER':<10}{'PROSE':<8}")
    for label, live_ok, handler_ok, prose_ok, prose_required, detail in rows:
        prose_cell = ("OK" if prose_ok else "DRIFT") if prose_required else "n/a"
        print(f"{label:<46}{'OK' if live_ok else 'DRIFT':<8}"
              f"{'OK' if handler_ok else 'DRIFT':<10}"
              f"{prose_cell:<8}"
              + (f"  -> {detail}" if detail else ""))


def _synth_ok():
    """A synthetic (extract, runbook, handler) triple satisfying every anchor — the
    selftest baseline + the fixtures each RED-catch mutates. Encodes the real dense-uniform
    announce distribution (every slot 1 broadcast, distinct per-hero TRIGSTR) AND plants
    OUT-OF-BODY ForForce / DisplayTimedTextToForce calls so the body-scope exclusion is
    exercised."""
    bodies = []
    for n, (func, hero) in enumerate(HERO_FUNCS):
        cb = f"Trig_{hero}_Func0{n}A"
        bodies.append(
            f"function {cb} takes nothing returns nothing\n"
            "    if ( GetOwningPlayer(GetTriggerUnit()) == Player(0) ) then\n"
            "        set udg_Player1 = GetLastCreatedUnit()\n"
            "    endif\n"
            f'    call DisplayTimedTextToForce(GetForceOfPlayer(GetOwningPlayer(udg_SaveTempUnit)), 5.00, "TRIGSTR_{2987 + n}")\n'
            "endfunction\n")
        bodies.append(
            f"function {func} takes nothing returns nothing\n"
            f"    call ForForce(GetPlayersByMapControl(MAP_CONTROL_USER), function {cb})\n"
            "endfunction\n")
    # out-of-body announce broadcasts (quest/portal systems) — MUST NOT be counted.
    bodies.append(
        "function Trig_Invasion_Func007002 takes nothing returns nothing\n"
        '    call DisplayTimedTextToForce(GetForceOfPlayer(GetOwningPlayer(udg_SaveTempUnit)), 5.00, "TRIGSTR_9001")\n'
        "endfunction\n")
    bodies.append(
        "function Trig_Find_Portal_Camelot_Actions takes nothing returns nothing\n"
        "    call ForForce(GetPlayersByMapControl(MAP_CONTROL_USER), function Trig_Invasion_Func007002)\n"
        "endfunction\n")
    extract = "\n".join(bodies)
    handler = (
        "//  Replaces the SHARED mechanics of the 10 hand-written Trig_<Hero>_Actions pick bodies.\n"
        "//  The lone per-hero datum — the announce TRIGSTR — rides udg_CastleSlot_AnnounceCur,\n"
        "//  set by ApplyPick just before the ForForce.\n"
        "function CastleSlot_AnnounceForForce takes nothing returns nothing\n"
        "    call DisplayTimedTextToForce(GetForceOfPlayer(GetOwningPlayer(udg_SaveTempUnit)), 5.00, udg_CastleSlot_AnnounceCur)\n"
        "endfunction\n"
        "    // per-pick broadcast — faithful to every body's ForForce(GetPlayersByMapControl(MAP_CONTROL_USER),\n"
        "    // function Trig_<Hero>_Func0NNA) at this exact position. The 10 callbacks collapse to the one\n"
        "    // shared CastleSlot_AnnounceForForce; the per-hero announce TRIGSTR is the only datum, carried\n"
        "    // per-slot in udg_CastleSlot_AnnounceStr[i].\n"
        "    set udg_CastleSlot_AnnounceCur = udg_CastleSlot_AnnounceStr[i]\n"
        "    call ForForce(GetPlayersByMapControl(MAP_CONTROL_USER), function CastleSlot_AnnounceForForce)\n"
    )
    runbook = (
        "## STEP 2 — Wire the pedestals ... disable the 10 hand-written pick bodies\n"
        "| `CastleSlot_AnnounceStr` | string **array** | (empty) | P2 | per-pick broadcast TRIGSTR (ForForce dim) |\n"
        "| `CastleSlot_AnnounceCur` | string | (empty) | P2 | scratch: announce of the slot picked NOW |\n"
        "Smoke: ... pans the picker's camera to the appear rect, broadcasts the right announce line to all players, renames ...\n"
    )
    return extract, runbook, handler


def selftest():
    print("=== SELFTEST: parser unit-tests + per-direction RED-catch (teeth) ===")
    extract, runbook, handler = _synth_ok()

    # parser sanity (body-scoped: the 2 out-of-body funcs are NOT in HERO_FUNCS)
    f = live_facts(extract)
    assert f["n_found"] == 10 and not f["missing"], f
    assert _occupants(f["callbacks"]) == EXPECTED_OCCUPANTS, _occupants(f["callbacks"])
    assert sum(len(v) for v in f["callbacks"].values()) == EXPECTED_TOTAL, f["callbacks"]
    assert _all_equal(f["forces"], USER_FORCE), f["forces"]
    assert len({f["trigstr"][h] for _, h in HERO_FUNCS}) == 10, f["trigstr"]
    assert all(d == DISPLAY_SIG for d in f["display"].values()), f["display"]
    assert all(f["literal_ok"].values()), f["literal_ok"]

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

    # 2) LIVE: drop a slot's announce ForForce -> every-slot + total trip
    bad = re.sub(
        r"(function Trig_King_Arthur_Actions takes nothing returns nothing\n)"
        r"    call ForForce\(GetPlayersByMapControl\(MAP_CONTROL_USER\), function [A-Za-z0-9_]+\)\n",
        r"\1", extract)
    c_every = caught(all_rows(bad, runbook, handler), "announce:every-slot=1")
    c_total = caught(all_rows(bad, runbook, handler), "announce:total=10")

    # 3) LIVE: a slot gets a SECOND announce broadcast (routed to a real announce callback,
    #    so the cb-body filter counts it) -> every-slot trips (not exactly 1)
    bad = extract.replace(
        "function Trig_Merlin_Actions takes nothing returns nothing\n",
        "function Trig_Merlin_Actions takes nothing returns nothing\n"
        "    call ForForce(GetPlayersByMapControl(MAP_CONTROL_USER), function Trig_Arthur_Func00A)\n")
    c_every2 = caught(all_rows(bad, runbook, handler), "announce:every-slot=1")

    # 4) LIVE: two heroes share a TRIGSTR -> distinct trips
    bad = extract.replace('"TRIGSTR_2988"', '"TRIGSTR_2987"')   # Guinevere == Arthur
    c_distinct = caught(all_rows(bad, runbook, handler), "announce:callback-collapse+distinct-trigstr")

    # 5) LIVE: a callback's display loses its uniform force/duration -> display uniform trips
    bad = extract.replace(
        'call DisplayTimedTextToForce(GetForceOfPlayer(GetOwningPlayer(udg_SaveTempUnit)), 5.00, "TRIGSTR_2987")',
        'call DisplayTimedTextToForce(bj_FORCE_ALL_PLAYERS, 9.00, "TRIGSTR_2987")', 1)
    c_disp = caught(all_rows(bad, runbook, handler), "announce:uniform-display-spine")

    # 6) LIVE: a callback uses a VARIABLE instead of a literal TRIGSTR -> literal-indirection trips
    bad = extract.replace('5.00, "TRIGSTR_2989")', '5.00, udg_SomeOtherStr)', 1)
    c_lit = caught(all_rows(bad, runbook, handler), "announce:literal->announcecur-indirection")

    # 7) LIVE: an announce ForForce loses its uniform user-force arg -> uniform-forforce trips
    bad = extract.replace(
        "call ForForce(GetPlayersByMapControl(MAP_CONTROL_USER), function Trig_Arthur_Func00A)",
        "call ForForce(bj_FORCE_ALL_PLAYERS, function Trig_Arthur_Func00A)", 1)
    c_uni = caught(all_rows(bad, runbook, handler), "announce:uniform-forforce-spine")

    # 8) BODY-SCOPE TEETH: plant ANOTHER out-of-body announce broadcast (a func NOT in
    #    HERO_FUNCS, with its own DisplayTimedTextToForce). A correctly body-scoped gate must
    #    IGNORE it — total/every-slot stay GREEN. (If scoping regressed to a flat grep, this
    #    extra broadcast would inflate the family and trip.)
    bad = extract + (
        "\nfunction Trig_Extra_Quest_Func001A takes nothing returns nothing\n"
        '    call DisplayTimedTextToForce(GetForceOfPlayer(GetOwningPlayer(udg_SaveTempUnit)), 5.00, "TRIGSTR_9999")\n'
        "endfunction\n"
        "function Trig_Extra_Quest_Actions takes nothing returns nothing\n"
        "    call ForForce(GetPlayersByMapControl(MAP_CONTROL_USER), function Trig_Extra_Quest_Func001A)\n"
        "endfunction\n")
    c_scope = (not caught(all_rows(bad, runbook, handler), "announce:total=10")
               and not caught(all_rows(bad, runbook, handler), "announce:every-slot=1"))

    # 9) HANDLER drift: spine drops the shared-callback ForForce -> uniform-forforce trips
    bad_h = handler.replace("function CastleSlot_AnnounceForForce)", "function WRONG_AnnounceForForce)")
    c_huni = caught(all_rows(extract, runbook, bad_h), "announce:uniform-forforce-spine")

    # 10) HANDLER drift: spine drops the AnnounceCur publish -> literal-indirection trips
    bad_h = handler.replace("set udg_CastleSlot_AnnounceCur = udg_CastleSlot_AnnounceStr[i]",
                            "set udg_WRONG_AnnounceCur = udg_CastleSlot_AnnounceStr[i]")
    c_hlit = caught(all_rows(extract, runbook, bad_h), "announce:literal->announcecur-indirection")

    # 11) HANDLER drift: callback drops the uniform display -> display-uniform trips
    bad_h = handler.replace(DISPLAY_SPINE, "DisplayTimedTextToForce(bj_FORCE_ALL_PLAYERS, 9.00, udg_CastleSlot_AnnounceCur)")
    c_hdisp = caught(all_rows(extract, runbook, bad_h), "announce:uniform-display-spine")

    # 12) HANDLER drift: header drops the collapse claim -> distinct/collapse trips
    bad_h = handler.replace("the per-hero announce TRIGSTR is the only datum",
                            "the per-hero announce TRIGSTR is irrelevant")
    c_hcol = caught(all_rows(extract, runbook, bad_h), "announce:callback-collapse+distinct-trigstr")

    # 13) PROSE drift: runbook drops the AnnounceStr ForForce-dim row -> every-slot trips
    bad_rb = runbook.replace("per-pick broadcast TRIGSTR (ForForce dim)",
                             "per-pick broadcast (some other dim)")
    c_prose = caught(all_rows(extract, bad_rb, handler), "announce:every-slot=1")

    # 14) PROSE drift: runbook drops the AnnounceCur scratch line -> literal-indirection trips
    bad_rb = runbook.replace("scratch: announce of the slot picked NOW", "unused scratch")
    c_prcur = caught(all_rows(extract, bad_rb, handler), "announce:literal->announcecur-indirection")

    for name, val in [
        ("live body deleted", c_bodies), ("live drop announce every-slot", c_every),
        ("live drop announce total", c_total), ("live double announce", c_every2),
        ("live shared TRIGSTR (distinct)", c_distinct), ("live non-uniform display", c_disp),
        ("live variable TRIGSTR (literal)", c_lit), ("live non-uniform forforce", c_uni),
        ("body-scope holds (out-of-body ignored)", c_scope),
        ("handler forforce drift", c_huni), ("handler AnnounceCur publish drift", c_hlit),
        ("handler display drift", c_hdisp), ("handler collapse-claim drift", c_hcol),
        ("prose AnnounceStr-row drop", c_prose), ("prose AnnounceCur-scratch drop", c_prcur),
    ]:
        print(f"  {name:<42}caught : {val}")
    ok = base_ok and all([c_bodies, c_every, c_total, c_every2, c_distinct, c_disp, c_lit,
                          c_uni, c_scope, c_huni, c_hlit, c_hdisp, c_hcol, c_prose, c_prcur])
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
              "the announce op cites are now suspect. Re-ground vs the new bake.")
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
        print("RESULT: FAIL — hero-select P2 announce/ForForce op drifted:")
        for lbl, d in fail:
            print(f"  - {lbl}: {d}")
        return 1
    print("RESULT: GREEN — the per-pick announce broadcast is bound vs the md5-pinned extract: all "
          "10 live pick bodies are present; EVERY slot carries exactly 1 in-body announce ForForce "
          "(10 total — body-scoped past the 33 out-of-body ForForce/DisplayTimedTextToForce calls, "
          "following each body-NAMED callback never a flat grep); the 10 per-hero callbacks each "
          "hard-code a DISTINCT literal announce TRIGSTR through the arg-uniform ForForce("
          "GetPlayersByMapControl(MAP_CONTROL_USER), function <cb>) + DisplayTimedTextToForce("
          "GetForceOfPlayer(GetOwningPlayer(udg_SaveTempUnit)), 5.00, <trigstr>) — matching the "
          "handler's collapse to ONE CastleSlot_AnnounceForForce parameterized by "
          "udg_CastleSlot_AnnounceCur (published from udg_CastleSlot_AnnounceStr[i] just before the "
          "ForForce) AND the runbook AnnounceStr/AnnounceCur claims. The operator's STEP-1 AnnounceStr "
          "column cannot silently drift from the bodies it replaces (no dropped/mis-routed announce).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
