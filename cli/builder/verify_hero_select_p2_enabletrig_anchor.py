#!/usr/bin/env python3
r"""
verify_hero_select_p2_enabletrig_anchor.py
================================================================================
KOTR Hero-Select REDESIGN (Track 4) · P2 **per-slot ENABLE-TRIGGER / Flurry-AI-arm
scalar tail op** <-> handler authority <-> live extract binder.
Built 2026-06-19 by KOTR Builder (engine claude-p).

WHY THIS GATE EXISTS (a real, uncovered seam on the P2 apply path)
--------------------------------------------------------------------------------
`hero_select_p2_APPLY_RUNBOOK.md`'s STEP-0 var table reserves the *scalar*
`CastleSlot_EnableTrig` array for the per-slot trigger armed at the body's tail
("per-slot trigger armed at the tail (Arthur `gg_trg_Flurry_AI`); null = none"). The
handler collapses the bodies' tail trigger-arms into ONE guarded scalar op, positioned
INSIDE the controller==COMPUTER guard's TRUE branch, immediately AFTER SetPlayerName:
    if ( GetPlayerController(picker) == MAP_CONTROL_COMPUTER ) then
        call SetPlayerName(picker, udg_CastleSlot_NameStr[i])
        if udg_CastleSlot_EnableTrig[i] != null then
            call EnableTrigger(udg_CastleSlot_EnableTrig[i])
        endif
    else
        ...
    endif
i.e. only the trigger handle is per-slot data, guarded on `!= null`. Like SpawnAbility
this op is a SPARSE SCALAR — only Arthur ('gg_trg_Flurry_AI', arming its Flurry AI) sets
one; the other 9 slots have EnableTrig==null (the guard skips, zero cost). UNLIKE
SpawnAbility it is ALSO control-flow-fenced behind the computer-controller guard (the
v2 name-guard branch), so it arms ONLY for computer slots — exactly the posture of the
sibling SetPlayerName op it follows.

THE CRUCIAL DISTINCTION THIS GATE PROTECTS: every one of the 10 pick bodies ALSO arms
the talent-stamp `EnableTrigger(gg_trg_HeroPickAssignTalentTree)` at the TOP (a SEPARATE,
earlier covered op — the §1 skeleton's EnableTalentStamp). The EnableTrig tail op is the
NON-talent-stamp arm, and only Arthur has one. A gate that counted all EnableTrigger calls
would conflate the dense talent-stamp arm (10) with the sparse Flurry arm (1) and the whole
op would be meaningless. This gate scopes the op family to EnableTrigger arms EXCLUDING the
talent stamp, and separately proves the talent stamp is present-in-all-10-but-excluded.

The handler header makes several checkable claims the WE operator relies on before
deleting the 10 old bodies:
  1. EXACTLY Arthur carries a tail trigger-arm (the other 9 carry none),
  2. Arthur arms exactly 1 trigger ('gg_trg_Flurry_AI'; 1 tail-arm total),
  3. the arm is the uniform EnableTrigger(<trigger>) — only the trigger handle is per-slot,
  4. the arm sits in the TRUE branch of the controller==COMPUTER guard, AFTER SetPlayerName
     (computer slots ONLY), NOT conflated with the always-armed talent stamp.
If any of those drift, the operator could bake an EnableTrig row onto the wrong slot, drop
Arthur's Flurry arm (the table compiles fine with EnableTrig==null — a SILENT no-AI Arthur),
leak the arm onto human slots, or mistake the talent stamp for the tail op — and no other
gate would catch it:
  * `verify_hero_select_p2_generated_j.py` / `verify_hero_select_p2_datatable.py` bind the
    MATERIALIZED EnableTrig scalar column vs the catalog JSON — they prove the BAKED column
    is internally consistent, NOT that it matches the live bodies' tail trigger-arm nor the
    handler header's natural-language claims (talent-stamp conflation goes uncaught there).
  * `verify_hero_select_p2_setplayername_anchor.py` binds the SetPlayerName op + the SAME
    computer guard, but never reads the EnableTrigger arm that follows it.
  * `verify_hero_select_p2_spawnability_anchor.py` binds the OTHER scalar-guard op (the
    spawn-ability add, a DIFFERENT op right after the spawn); it never reads the tail arm.
  * `verify_hero_select_p2_loop.py` / `audit_hero_select_p2_equivalence.py` compile +
    op-equivalence-prove the handler; they never read the runbook .md, so a runbook/header
    enable-trig claim that drifts from the spine they prove goes uncaught.

So this gate closes the seam the established Track-4 way: it binds the runbook enable-trig
claim <-> handler header + spine authority <-> live extract tail trigger-arm op, both ways,
against the md5-pinned canonical extract — the GUARDED scalar twin of the spawn-ability /
setplayername binders. CRUCIAL TEETH: the live extract has MANY more EnableTrigger calls
OUTSIDE the 10 pick bodies AND the dense talent-stamp arm INSIDE every body; this gate
BODY-SCOPES to the 10 hand-written Trig_<Hero>_Actions pick bodies (L49272-50811 per the
runbook's corrected span) AND excludes the talent-stamp arm so only the real per-slot tail
trigger-arm counts.

WHAT IT CHECKS (read-only; touches no .w3x and no shippable .j)
--------------------------------------------------------------------------------
  0. md5 pin: the live extract still hashes to the runbook-pinned md5 (a re-bake trips it).
  1. all 10 hand-written hero pick bodies are present in the live extract.
  2. talent-stamp present+excluded: ALL 10 bodies carry exactly 1 talent-stamp
     EnableTrigger(gg_trg_HeroPickAssignTalentTree) (a SEPARATE op the tail family excludes)
     (live) <-> handler "The talent-stamp arm is a separate, earlier covered op" <-> runbook
     `gg_trg_HeroPickAssignTalentTree` (21 refs, the talent stamp).
  3. occupant: EXACTLY {Arthur} carries an in-body tail trigger-arm (non-talent EnableTrigger)
     (live, body-scoped) <-> handler "Only Arthur sets one" <-> runbook "per-slot trigger
     armed at the tail (Arthur `gg_trg_Flurry_AI`); null = none".
  4. distribution: live in-body tail-arm counts == {Arthur:1}, total 1 (live) <-> handler
     "the other 9 slots have EnableTrig==null" <-> runbook `CastleSlot_EnableTrig`.
  5. trigger handle: Arthur arms 'gg_trg_Flurry_AI' (bare, NOT the _Copy sibling) (live) <->
     handler "Arthur's EnableTrigger(gg_trg_Flurry_AI)" <-> runbook "Arthur `gg_trg_Flurry_AI`".
  6. uniform-spine: every in-body tail-arm = EnableTrigger(<trigger>) (live) <-> handler spine
     EnableTrigger(udg_CastleSlot_EnableTrig[i]) + "the whole op is the trigger handle ...
     scalar udg_CastleSlot_EnableTrig[i]" <-> runbook `CastleSlot_EnableTrig`.
  7. computer-guard: Arthur's tail-arm sits in the TRUE branch of the body-named
     controller==COMPUTER guard, AFTER SetPlayerName (computer slots ONLY) (live) <-> handler
     "immediately AFTER SetPlayerName inside this TRUE branch" + spine under
     "if ( GetPlayerController(picker) == MAP_CONTROL_COMPUTER )" <-> runbook "arms Arthur's
     Flurry AI" / "for Arthur only, `gg_trg_Flurry_AI` ... via the per-slot EnableTrig array".

Run:        python3 verify_hero_select_p2_enabletrig_anchor.py
Self-test:  python3 verify_hero_select_p2_enabletrig_anchor.py --selftest
            (parser unit-tests + a per-direction RED-catch so the gate has teeth, incl.
             body-scoped exclusion of out-of-body EnableTrigger calls, talent-stamp
             non-conflation, and a non-COMPUTER-guard RED-catch)
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

# the always-armed §1 skeleton talent-stamp trigger — a SEPARATE op (every body arms it at
# the top). The tail enable-trig family EXCLUDES this so the sparse Flurry arm is not
# conflated with the dense talent stamp.
TALENT_STAMP = "gg_trg_HeroPickAssignTalentTree"

# the catalog/handler tail-arm distribution the runbook claim is filled against.
# SPARSE-SCALAR: only Arthur arms a tail trigger ('gg_trg_Flurry_AI'); the other 9 carry none.
EXPECTED_ENABLETRIG = {
    "Arthur": ["gg_trg_Flurry_AI"],
}
EXPECTED_ENABLETRIG_COUNTS = {h: len(v) for h, v in EXPECTED_ENABLETRIG.items()}   # {Arthur:1}
EXPECTED_ENABLETRIG_TOTAL = sum(len(v) for v in EXPECTED_ENABLETRIG.values())      # 1
EXPECTED_OCCUPANTS = set(EXPECTED_ENABLETRIG)                                       # {Arthur}

# the exact, arg-uniform tail-arm signature the live pick bodies use (canonicalized: the
# trigger handle collapsed to <trig>).
ENABLETRIG_SIG = "call EnableTrigger(<trig>)"

# the handler spine line (post // strip + whitespace collapse). The spine's arg is the
# per-slot scalar udg_CastleSlot_EnableTrig[i], guarded on != null.
ENABLETRIG_SPINE = "call EnableTrigger(udg_CastleSlot_EnableTrig[i])"

# the canonical controller==COMPUTER predicate body, normalized (ws-collapsed) — the same
# guard the SetPlayerName op uses (the rename + the Flurry arm share the one TRUE branch).
PRED_CANON = ("if ( not ( GetPlayerController(GetOwningPlayer(GetTriggerUnit())) == "
              "MAP_CONTROL_COMPUTER ) ) then return false endif return true")

# the name-guard: an `if ( <body-named pred>() ) then` ... `else` block (the inlined
# `if ( (true) )` block can never match — its condition is not a Trig_*_Func*C() call).
_GUARD_RE = re.compile(
    r"if \( (Trig_[A-Za-z0-9_]+_Func[0-9]+C)\(\) \) then\r?\n(.*?)\r?\n    else",
    re.DOTALL)


def body_of(extract_text, func):
    """The body text of one function, or None if gone. Anchored on the exact
    `function <name> takes nothing returns ...` ... `endfunction` span so the abundant
    out-of-body EnableTrigger calls can never leak in."""
    m = re.search(
        r"function " + re.escape(func) + r" takes nothing returns \w+(.*?)\nendfunction",
        extract_text, re.DOTALL)
    return m.group(1) if m else None


def _all_enabletrigger_handles(body):
    """Ordered `call EnableTrigger(<gg_trg_*>)` trigger handles in a body (whole-identifier
    capture, so gg_trg_Flurry_AI_Copy is distinct from gg_trg_Flurry_AI)."""
    return re.findall(r"call EnableTrigger\((gg_trg_[A-Za-z0-9_]+)\)", body)


def _talent_stamp_count(body):
    """How many talent-stamp EnableTrigger(gg_trg_HeroPickAssignTalentTree) arms a body carries
    (the separate §1 skeleton op the tail family excludes)."""
    return sum(1 for h in _all_enabletrigger_handles(body) if h == TALENT_STAMP)


def _tail_arm_handles(body):
    """Ordered tail trigger-arm handles = in-body EnableTrigger arms EXCLUDING the talent
    stamp. This is the per-slot EnableTrig op family."""
    return [h for h in _all_enabletrigger_handles(body) if h != TALENT_STAMP]


def _tail_arm_calls(body):
    """All non-talent `call EnableTrigger(gg_trg_*)` one-liners in a body, canonicalized
    (trigger handle -> <trig>)."""
    out = []
    for m in re.findall(r"call EnableTrigger\((gg_trg_[A-Za-z0-9_]+)\)", body):
        if m == TALENT_STAMP:
            continue
        out.append("call EnableTrigger(<trig>)")
    return out


def _tail_arm_guarded(body, extract_text):
    """True iff this body's tail trigger-arm (non-talent EnableTrigger) sits in the TRUE
    branch of a body-named guard `if ( Trig_<Hero>_Func0NNC() ) then ... else` whose
    predicate normalizes EXACTLY to the controller==COMPUTER test PRED_CANON, AND appears
    AFTER the SetPlayerName rename in that branch (the handler's "immediately AFTER
    SetPlayerName inside this TRUE branch"). Following the body-NAMED predicate, never a
    flat grep."""
    for pred, true_branch in _GUARD_RE.findall(body):
        # the tail arm we care about: a non-talent EnableTrigger inside this branch
        arms = [h for h in _all_enabletrigger_handles(true_branch) if h != TALENT_STAMP]
        if not arms:
            continue
        pb = body_of(extract_text, pred)
        if pb is None:
            continue
        if re.sub(r"\s+", " ", pb).strip() != PRED_CANON:
            continue
        # ordering: the arm must follow SetPlayerName in the same TRUE branch
        name_i = true_branch.find("call SetPlayerName(")
        arm_i = true_branch.find("call EnableTrigger(")
        if name_i == -1 or arm_i == -1 or arm_i < name_i:
            continue
        return True
    return False


def live_facts(extract_text):
    """Per-body tail trigger-arm facts, BODY-SCOPED to the 10 pick bodies (talent stamp
    excluded; guard predicate followed by NAME, never a flat grep). Every value
    independently checkable so a single mutation trips exactly one anchor."""
    handles = {}    # hero -> [tail trigger handles]   (talent stamp excluded)
    calls = {}      # hero -> [canonicalized tail EnableTrigger calls]
    talent = {}     # hero -> # talent-stamp arms (must be 1 each)
    guarded = {}    # hero -> tail-arm is fenced behind controller==COMPUTER guard, after rename
    missing = []
    for func, hero in HERO_FUNCS:
        b = body_of(extract_text, func)
        if b is None:
            missing.append(hero)
            continue
        handles[hero] = _tail_arm_handles(b)
        calls[hero] = _tail_arm_calls(b)
        talent[hero] = _talent_stamp_count(b)
        guarded[hero] = _tail_arm_guarded(b, extract_text)
    return {
        "n_found": len(handles),
        "missing": missing,
        "handles": handles,
        "calls": calls,
        "talent": talent,
        "guarded": guarded,
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

    # 2) talent-stamp present in ALL 10 (a SEPARATE op the tail family excludes)
    one_each = all(v == 1 for v in f["talent"].values()) and len(f["talent"]) == 10
    row("enabletrig:talent-stamp-excluded", one_each,
        "The talent-stamp arm is a separate, earlier covered op" in hd,
        "`gg_trg_HeroPickAssignTalentTree` (21" in rbf, True,
        "" if one_each else f"talent-stamp arm counts (expected 1 each)={f['talent']}")

    # 3) occupant: EXACTLY {Arthur} carries an in-body tail trigger-arm
    occ = _occupants(f["handles"])
    live_ok = occ == EXPECTED_OCCUPANTS
    row("enabletrig:occupant={Arthur}", live_ok,
        "Only Arthur sets one" in hd,
        "per-slot trigger armed at the tail (Arthur `gg_trg_Flurry_AI`); null = none" in rbf, True,
        "" if live_ok else f"in-body tail-arm occupants={sorted(occ)} (expected {sorted(EXPECTED_OCCUPANTS)})")

    # 4) distribution: {Arthur:1}, total 1
    counts = _counts(f["handles"])
    total = sum(len(v) for v in f["handles"].values())
    live_ok = counts == EXPECTED_ENABLETRIG_COUNTS and total == EXPECTED_ENABLETRIG_TOTAL
    row("enabletrig:distribution+total=1", live_ok,
        "the other 9 slots have EnableTrig==null" in hd,
        "`CastleSlot_EnableTrig`" in rbf, True,
        "" if live_ok else f"live tail-arm counts={counts} total={total} "
        f"(expected {EXPECTED_ENABLETRIG_COUNTS}, total {EXPECTED_ENABLETRIG_TOTAL})")

    # 5) trigger handle: Arthur arms 'gg_trg_Flurry_AI' (bare, not _Copy)
    live_ok = {h: v for h, v in f["handles"].items() if v} == EXPECTED_ENABLETRIG
    row("enabletrig:trigger-handle", live_ok,
        "Arthur's EnableTrigger(gg_trg_Flurry_AI)" in hd,
        "Arthur `gg_trg_Flurry_AI`" in rbf, True,
        "" if live_ok else f"live tail-arm handles={ {h: v for h, v in f['handles'].items() if v} } "
        f"(expected {EXPECTED_ENABLETRIG})")

    # 6) uniform-spine: every tail-arm = EnableTrigger(<trig>)
    live_ok = _all_match(f["calls"], ENABLETRIG_SIG)
    row("enabletrig:uniform-spine", live_ok,
        ENABLETRIG_SPINE in hd
        and "whole op is the trigger handle, carried as the" in hd
        and "scalar udg_CastleSlot_EnableTrig[i]" in hd,
        "`CastleSlot_EnableTrig`" in rbf, True,
        "" if live_ok else "a live tail-arm is not the uniform EnableTrigger(<trig>)")

    # 7) computer-guard: Arthur's tail-arm fenced behind controller==COMPUTER guard, after rename
    live_ok = _occupants(f["guarded"]) == EXPECTED_OCCUPANTS and all(
        f["guarded"][h] for h in EXPECTED_OCCUPANTS)
    row("enabletrig:computer-guard", live_ok,
        "immediately AFTER SetPlayerName inside" in hd
        and "if ( GetPlayerController(picker) == MAP_CONTROL_COMPUTER ) then" in hd,
        "arms Arthur's Flurry AI" in rbf
        and "for Arthur only, `gg_trg_Flurry_AI`" in rbf, True,
        "" if live_ok else f"Arthur tail-arm guarded={f['guarded'].get('Arthur')} "
        f"(occupants guarded={sorted(_occupants(f['guarded']))})")
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
    selftest baseline + the fixtures each RED-catch mutates. Encodes the real sparse tail-arm
    distribution (only Arthur 'gg_trg_Flurry_AI', fenced behind the controller==COMPUTER guard
    AFTER SetPlayerName), the always-armed talent stamp in EVERY body, AND plants OUT-OF-BODY
    EnableTrigger calls so the body-scope exclusion is exercised."""
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
        # the tail arm (only Arthur) goes INSIDE the guard TRUE branch, AFTER SetPlayerName
        tail = ""
        for trg in EXPECTED_ENABLETRIG.get(hero, []):
            tail = f"        call EnableTrigger({trg})\n"
        bodies.append(
            f"function {func} takes nothing returns nothing\n"
            "    call EnableTrigger(gg_trg_HeroPickAssignTalentTree)\n"   # talent stamp (every body)
            "    call PanCameraToTimedLocForPlayer(GetOwningPlayer(GetTriggerUnit()), GetRectCenter(gg_rct_X), 0.00)\n"
            f"    if ( {pred}() ) then\n"
            f'        call SetPlayerName(GetOwningPlayer(GetTriggerUnit()), "TRIGSTR_{839 + n}")\n'
            f"{tail}"
            "    else\n"
            "    endif\n"
            "endfunction\n")
    # out-of-body EnableTrigger calls (other systems / re-pick triggers) — MUST NOT count.
    bodies.append(
        "function Trig_newArthur_Actions takes nothing returns nothing\n"
        "    call EnableTrigger(gg_trg_Flurry_AI)\n"
        "endfunction\n")
    bodies.append(
        "function InitSomeSystem takes nothing returns nothing\n"
        "    call EnableTrigger(gg_trg_Some_Other_System)\n"
        "endfunction\n")
    extract = "\n".join(bodies)
    handler = (
        "//  Replaces the SHARED mechanics of the 10 hand-written Trig_<Hero>_Actions pick bodies.\n"
        "    // --- per-slot ENABLE-TRIGGER (v2 2026-06-18) ---\n"
        "    // faithful to Arthur's EnableTrigger(gg_trg_Flurry_AI) immediately AFTER SetPlayerName inside\n"
        "    // this TRUE branch (arming its Flurry AI). The whole op is the trigger handle, carried as the\n"
        "    // scalar udg_CastleSlot_EnableTrig[i]. Only Arthur sets one; the other 9 slots have\n"
        "    // EnableTrig==null -> the guard skips, zero cost (audit EnableTrig dimension). The talent-stamp\n"
        "    // arm is a separate, earlier covered op (EnableTalentStamp).\n"
        "    if ( GetPlayerController(picker) == MAP_CONTROL_COMPUTER ) then\n"
        "        call SetPlayerName(picker, udg_CastleSlot_NameStr[i])\n"
        "        if udg_CastleSlot_EnableTrig[i] != null then\n"
        "            call EnableTrigger(udg_CastleSlot_EnableTrig[i])\n"
        "        endif\n"
        "    else\n"
        "    endif\n"
    )
    runbook = (
        "## STEP 0 ... collapses the 10 hand-written pick bodies\n"
        "| `CastleSlot_EnableTrig` | trigger **array** | (none) | P2 | per-slot trigger armed at the "
        "tail (Arthur `gg_trg_Flurry_AI`); null = none |\n"
        "> The handler also arms two **pre-existing map triggers** — `gg_trg_HeroPickAssignTalentTree` "
        "(21 refs, the talent stamp) and, for Arthur only, `gg_trg_Flurry_AI` (9 refs, via the per-slot "
        "EnableTrig array).\n"
        "Smoke: ... renames only computer-controlled slots, arms Arthur's Flurry AI, fires Gawain's "
        "polymorph cluster ...\n"
    )
    return extract, runbook, handler


def selftest():
    print("=== SELFTEST: parser unit-tests + per-direction RED-catch (teeth) ===")
    extract, runbook, handler = _synth_ok()

    # parser sanity (body-scoped: the 2 out-of-body funcs are NOT in HERO_FUNCS)
    f = live_facts(extract)
    assert f["n_found"] == 10 and not f["missing"], f
    assert _occupants(f["handles"]) == EXPECTED_OCCUPANTS, _occupants(f["handles"])
    assert {h: v for h, v in f["handles"].items() if v} == EXPECTED_ENABLETRIG, f["handles"]
    assert sum(len(v) for v in f["handles"].values()) == EXPECTED_ENABLETRIG_TOTAL
    assert all(v == 1 for v in f["talent"].values()), f["talent"]
    assert _all_match(f["calls"], ENABLETRIG_SIG), f["calls"]
    assert f["guarded"]["Arthur"], f["guarded"]

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
    bad = extract.replace("function Trig_King_Arthur_Actions takes nothing returns nothing",
                          "function Trig_GONE_Actions takes nothing returns nothing")
    c_bodies = caught(all_rows(bad, runbook, handler), "bodies:present=10")

    # 2) LIVE: drop a body's talent-stamp arm -> talent-stamp anchor trips
    bad = extract.replace(
        "function Trig_Lady_Guinevere_Actions takes nothing returns nothing\n"
        "    call EnableTrigger(gg_trg_HeroPickAssignTalentTree)\n",
        "function Trig_Lady_Guinevere_Actions takes nothing returns nothing\n", 1)
    c_talent = caught(all_rows(bad, runbook, handler), "enabletrig:talent-stamp-excluded")

    # 3) LIVE: give a non-occupant (Galahad) a tail trigger-arm -> occupant + distribution trip
    bad = extract.replace(
        '        call SetPlayerName(GetOwningPlayer(GetTriggerUnit()), "TRIGSTR_845")\n',
        '        call SetPlayerName(GetOwningPlayer(GetTriggerUnit()), "TRIGSTR_845")\n'
        "        call EnableTrigger(gg_trg_Some_AI)\n", 1)
    c_occ = caught(all_rows(bad, runbook, handler), "enabletrig:occupant={Arthur}")
    c_dist_add = caught(all_rows(bad, runbook, handler), "enabletrig:distribution+total=1")

    # 4) LIVE: drop Arthur's only tail-arm -> occupant + distribution + handle + guard trip
    bad = extract.replace("        call EnableTrigger(gg_trg_Flurry_AI)\n", "", 1)
    c_dist_drop = caught(all_rows(bad, runbook, handler), "enabletrig:distribution+total=1")
    c_handle_drop = caught(all_rows(bad, runbook, handler), "enabletrig:trigger-handle")
    c_occ_drop = caught(all_rows(bad, runbook, handler), "enabletrig:occupant={Arthur}")

    # 5) LIVE: wrong handle (Flurry_AI -> the _Copy sibling) -> handle trips
    bad = extract.replace("call EnableTrigger(gg_trg_Flurry_AI)\n",
                          "call EnableTrigger(gg_trg_Flurry_AI_Copy)\n", 1)
    c_handle = caught(all_rows(bad, runbook, handler), "enabletrig:trigger-handle")

    # 6) LIVE: Arthur's tail-arm moved OUT of the computer guard (arms unconditionally) -> guard trips
    bad = extract.replace(
        '        call SetPlayerName(GetOwningPlayer(GetTriggerUnit()), "TRIGSTR_839")\n'
        "        call EnableTrigger(gg_trg_Flurry_AI)\n"
        "    else\n"
        "    endif\n",
        '        call SetPlayerName(GetOwningPlayer(GetTriggerUnit()), "TRIGSTR_839")\n'
        "    else\n"
        "    endif\n"
        "    call EnableTrigger(gg_trg_Flurry_AI)\n")
    c_guard = caught(all_rows(bad, runbook, handler), "enabletrig:computer-guard")

    # 7) LIVE: Arthur's guard predicate is NOT the controller==COMPUTER test -> guard trips
    bad = extract.replace(
        "function Trig_Arthur_Func00C takes nothing returns boolean\n"
        "    if ( not ( GetPlayerController(GetOwningPlayer(GetTriggerUnit())) == MAP_CONTROL_COMPUTER ) ) then\n"
        "        return false\n"
        "    endif\n"
        "    return true\n"
        "endfunction\n",
        "function Trig_Arthur_Func00C takes nothing returns boolean\n"
        "    return true\n"
        "endfunction\n")
    c_guard2 = caught(all_rows(bad, runbook, handler), "enabletrig:computer-guard")

    # 8) BODY-SCOPE + TALENT TEETH: plant ANOTHER out-of-body Flurry arm (func NOT in HERO_FUNCS).
    #    A correctly body-scoped gate must IGNORE it — occupant/distribution stay GREEN.
    bad = extract + (
        "\nfunction Trig_One_More_Repick_Actions takes nothing returns nothing\n"
        "    call EnableTrigger(gg_trg_Flurry_AI)\n"
        "endfunction\n")
    c_scope = (not caught(all_rows(bad, runbook, handler), "enabletrig:occupant={Arthur}")
               and not caught(all_rows(bad, runbook, handler), "enabletrig:distribution+total=1"))

    # 9) TALENT NON-CONFLATION TEETH: the dense talent-stamp arm in all 10 bodies must NOT
    #    inflate the tail family (occupant stays {Arthur}, total stays 1). (If the family
    #    regressed to all EnableTrigger calls, total would be 11 and occupant all-10.)
    c_nonconflate = (not caught(all_rows(extract, runbook, handler), "enabletrig:occupant={Arthur}")
                     and not caught(all_rows(extract, runbook, handler), "enabletrig:distribution+total=1"))

    # 10) HANDLER drift: spine drops the EnableTrig scalar -> uniform trips
    bad_h = handler.replace("udg_CastleSlot_EnableTrig[i])", "udg_WRONG_EnableTrig[i])")
    c_huni = caught(all_rows(extract, runbook, bad_h), "enabletrig:uniform-spine")

    # 11) HANDLER drift: header drops the occupant claim -> occupant trips
    bad_h = handler.replace("Only Arthur sets one", "Only Galahad sets one")
    c_hocc = caught(all_rows(extract, runbook, bad_h), "enabletrig:occupant={Arthur}")

    # 12) HANDLER drift: header drops the Flurry handle -> handle trips
    bad_h = handler.replace("Arthur's EnableTrigger(gg_trg_Flurry_AI)",
                            "Arthur's EnableTrigger(gg_trg_Zzzz_AI)")
    c_hhandle = caught(all_rows(extract, runbook, bad_h), "enabletrig:trigger-handle")

    # 13) HANDLER drift: header drops the computer-guard order claim -> guard trips
    bad_h = handler.replace("immediately AFTER SetPlayerName inside",
                            "somewhere unrelated to")
    c_hguard = caught(all_rows(extract, runbook, bad_h), "enabletrig:computer-guard")

    # 14) PROSE drift: runbook drops the EnableTrig tail row -> occupant trips
    bad_rb = runbook.replace(
        "per-slot trigger armed at the tail (Arthur `gg_trg_Flurry_AI`); null = none",
        "per-slot trigger armed at the tail for nobody")
    c_prose = caught(all_rows(extract, bad_rb, handler), "enabletrig:occupant={Arthur}")

    # 15) PROSE drift: runbook drops the CastleSlot_EnableTrig table row -> uniform (table cite) trips
    bad_rb = runbook.replace("`CastleSlot_EnableTrig`", "`CastleSlot_GONE`")
    c_prtab = caught(all_rows(extract, bad_rb, handler), "enabletrig:uniform-spine")

    for name, val in [
        ("live body deleted", c_bodies), ("live drop talent stamp", c_talent),
        ("live extra occupant", c_occ), ("live extra occ dist", c_dist_add),
        ("live drop arm dist", c_dist_drop), ("live drop arm handle", c_handle_drop),
        ("live drop arm occ", c_occ_drop), ("live wrong handle (_Copy)", c_handle),
        ("live arm out of guard", c_guard), ("live non-COMPUTER predicate", c_guard2),
        ("body-scope holds (out-of-body ignored)", c_scope),
        ("talent non-conflation holds", c_nonconflate),
        ("handler EnableTrig-scalar drift", c_huni), ("handler occupant drift", c_hocc),
        ("handler handle drift", c_hhandle), ("handler guard-order drift", c_hguard),
        ("prose enable-trig-claim drop", c_prose), ("prose CastleSlot_EnableTrig drop", c_prtab),
    ]:
        print(f"  {name:<42}caught : {val}")
    ok = base_ok and all([c_bodies, c_talent, c_occ, c_dist_add, c_dist_drop, c_handle_drop,
                          c_occ_drop, c_handle, c_guard, c_guard2, c_scope, c_nonconflate,
                          c_huni, c_hocc, c_hhandle, c_hguard, c_prose, c_prtab])
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
              "the enable-trig op cites are now suspect. Re-ground vs the new bake.")
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
        print("RESULT: FAIL — hero-select P2 enable-trig/Flurry-arm op drifted:")
        for lbl, d in fail:
            print(f"  - {lbl}: {d}")
        return 1
    print("RESULT: GREEN — the per-slot tail trigger-arm (Arthur's Flurry AI) is bound vs the "
          "md5-pinned extract: all 10 live pick bodies are present, each carries the always-armed "
          "talent-stamp EnableTrigger(gg_trg_HeroPickAssignTalentTree) as a SEPARATE op the tail "
          "family excludes; EXACTLY Arthur carries an in-body tail trigger-arm (the other 9 carry "
          "none — body-scoped past the out-of-body EnableTrigger calls AND the dense talent stamp); "
          "Arthur arms 1 trigger ('gg_trg_Flurry_AI' bare, not the _Copy sibling = 1 total) via the "
          "uniform EnableTrigger(<trig>), fenced in the TRUE branch of the body-named "
          "controller==COMPUTER guard AFTER SetPlayerName (computer slots ONLY) — matching the "
          "handler spine (EnableTrigger(udg_CastleSlot_EnableTrig[i]) guarded on != null, under the "
          "same name-guard) + header occupant/handle/order claims AND the runbook EnableTrig "
          "'Arthur gg_trg_Flurry_AI' / 'arms Arthur's Flurry AI' claims. The operator's STEP-1 "
          "EnableTrig column cannot silently drift from the bodies it replaces (no mis-slotted row, "
          "no no-AI Arthur, no talent-stamp conflation, no arm leaking onto human slots).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
