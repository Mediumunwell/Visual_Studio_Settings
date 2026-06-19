#!/usr/bin/env python3
r"""
verify_hero_select_p2_talentstamp_anchor.py
================================================================================
KOTR Hero-Select REDESIGN (Track 4) · P2 **§1-skeleton EnableTalentStamp op**
(`EnableTrigger(gg_trg_HeroPickAssignTalentTree)`, armed in EVERY pick body)
<-> handler §1-skeleton authority <-> runbook armed-map-trigger claim <-> live extract binder.
Built 2026-06-19 by KOTR Builder (engine claude-p).

WHY THIS GATE EXISTS (a real, uncovered seam — the LAST un-bound covered spine op)
--------------------------------------------------------------------------------
The handler header enumerates the data-uniform spine op order (covered_order, uniform
across all 10 bodies per audit_hero_select_p2_equivalence.py):
    Disable -> EnableTalent -> KillWisp -> HeroSpawn -> SpawnAbility -> SaveHero ->
    ForForce -> SelectHero -> HeroItems -> AllyTransfer -> Avail -> Rescue -> Invuln ->
    PanCamera -> SetPlayerName -> EnableTrig(tail)
Every data-carrying op above is now bound 3 ways by a sibling Track-4 gate (HeroType,
NameStr, AnnounceStr, TakenVillager, Item, Ally/Rescue/Invuln, Avail, SpawnAbility,
EnableTrig-tail, SpawnLoc/FaceLoc, CamLoc, ExtrasHook). **EnableTalent** — the §1
skeleton's "arm the talent stamp" op (`call EnableTrigger(gg_trg_HeroPickAssignTalentTree)`)
— was NOT: it is a HARDCODED, DENSE-UNIFORM skeleton op (every body arms the SAME map
trigger; there is no per-slot `CastleSlot_*` datum for it), so the per-slot data binders
skip it by construction. The ONE gate that even mentions it
(`verify_hero_select_p2_enabletrig_anchor.py`) uses it only as the EXCLUDED control to
prove the sparse Flurry tail-arm is *not* the talent stamp — it never binds the talent
stamp AS a covered op (its presence-in-all-10, its bare handle, its skeleton position,
its handler-spine faithfulness). This gate closes that last covered-spine seam.

WHY IT MATTERS (a silent regression a compile/data-gen cannot catch):
`gg_trg_HeroPickAssignTalentTree` is the per-pick **talent-tree stamp** — arming it is how
each freshly-picked hero gets its talent UI/assignment trigger live. The handler reproduces
it as a fixed skeleton line; if that line were dropped, mis-handled (a `_Copy`/variant
trigger), or reordered after the hero spawn, every picked hero would silently lose (or
double-arm) its talent stamp — invisible to pjass (the handler still compiles) and invisible
to the data round-trip (there is no data column for it). Binding it to the live bodies + the
runbook's armed-map-trigger claim makes that drift loud.

THE TRAPS THAT MAKE THIS ITS OWN GATE (distinct teeth from every sibling):
  * DENSE-UNIFORM, not sparse: ALL 10 bodies arm exactly 1 talent stamp (the mirror of the
    EnableTrig tail op, which only Arthur carries). A tooth tuned for the sparse tail
    (occupant=={Arthur}) is WRONG here; this gate proves occupant == all 10 + count 1 each.
  * HARDCODED, not data-driven: the handler arms a LITERAL `gg_trg_HeroPickAssignTalentTree`,
    NOT a `udg_CastleSlot_*[i]` array element. This gate proves the handler spine carries the
    bare literal AND that it is distinct from the data-driven tail `EnableTrigger(
    udg_CastleSlot_EnableTrig[i])` — i.e. the talent stamp is the skeleton op, not the tail op.
  * BODY-SCOPE teeth: the live extract has **13** `EnableTrigger(gg_trg_HeroPickAssignTalentTree)`
    calls total but only **10** inside the pick bodies (the other 3 live in
    `Trig_Load_GUI_Actions` x2 + `SampleDialogSystem__OnButtonClick` — the save/load + sample
    paths). A flat grep would overcount; this gate body-scopes to the 10 hand-written
    `Trig_<Hero>_Actions` bodies (L49272-50811 per the runbook's corrected span).
  * SKELETON POSITION: in every body the talent stamp arms AFTER `DisableTrigger(
    GetTriggeringTrigger())` and BEFORE the wisp-consume (`KillUnit`/`h__RemoveUnit` of
    `GetTriggerUnit()` — Gawain uses RemoveUnit, the other 9 KillUnit), matching the handler's
    Disable->EnableTalent->KillWisp ordering. A reorder past the spawn trips it.
  * NON-CONFLATION (opposite direction to the enabletrig gate): the dense talent stamp (10)
    must NOT be conflated with the sparse Flurry tail (1, Arthur only). This gate proves the
    talent-stamp family is exactly the talent-stamp handle and excludes the Flurry tail-arm.

Why no existing gate closes THIS seam:
  * `verify_hero_select_p2_enabletrig_anchor.py` reads the talent stamp ONLY to exclude it
    (it proves "talent-stamp present in all 10 but the tail family excludes it"). It never
    binds the talent stamp's bare handle, skeleton position, handler-spine literal, or
    non-conflation as a covered op.
  * `verify_hero_select_p2_runbook_anchors.py` binds the runbook's `gg_trg_HeroPickAssignTalentTree`
    (21) **occurrence count** vs the live file — a whole-file grep count, NOT a per-body
    covered-op binding (it never reads the handler spine nor body-scopes the arm).
  * `verify_hero_select_p2_loop.py` / `audit_hero_select_p2_equivalence.py` compile +
    op-equivalence-prove the handler; they never read the runbook .md, so a runbook armed-trig
    claim that drifts from the spine goes uncaught.

So this gate closes the seam the established Track-4 way: runbook armed-map-trigger claim
<-> handler §1-skeleton spine + header authority <-> live per-body arm, both directions,
against the md5-pinned canonical extract — the DENSE-UNIFORM, HARDCODED-skeleton sibling of
the sparse data-driven EnableTrig tail binder, and the LAST un-bound covered spine op.

WHAT IT CHECKS (read-only; touches no .w3x and no shippable .j)
--------------------------------------------------------------------------------
  0. md5 pin: the live extract still hashes to the runbook-pinned md5 (a re-bake trips it).
  1. all 10 hand-written hero pick bodies are present in the live extract.
  2. dense-uniform: EVERY one of the 10 bodies arms EXACTLY 1 talent stamp (live, body-scoped)
     <-> handler "arm the talent stamp" §1-skeleton claim <-> runbook
     `gg_trg_HeroPickAssignTalentTree` (21, the talent stamp).
  3. total-in-bodies=10 (NOT 13 — body-scope past the 3 out-of-body arms) (live) <-> handler
     spine bare literal <-> runbook armed-map-trigger note.
  4. bare-handle: every body arms BARE `gg_trg_HeroPickAssignTalentTree` (no `_Copy`/variant)
     (live) <-> handler `EnableTrigger(gg_trg_HeroPickAssignTalentTree)` <-> runbook
     `gg_trg_HeroPickAssignTalentTree`.
  5. skeleton-position: in every body the talent stamp arms AFTER DisableTrigger and BEFORE
     the wisp-consume (live) <-> handler covered_order "Disable -> EnableTalent -> KillWisp"
     + the spine line order DisableTrigger -> EnableTrigger(talent) -> KillUnit(wisp) <->
     runbook (skeleton armed at pick).
  6. hardcoded-not-data: the handler arms the talent stamp as a LITERAL map trigger, distinct
     from the data-driven tail `EnableTrigger(udg_CastleSlot_EnableTrig[i])` (handler) — proves
     it is the uniform skeleton op, not a per-slot `CastleSlot_*` datum <-> handler
     "The talent-stamp arm is a separate, earlier covered op (EnableTalentStamp)".
  7. non-conflation: the dense talent-stamp family (10) is NOT the sparse Flurry tail (Arthur
     only) — the talent handle != the Flurry handle, and the talent stamp is body-uniform
     while the Flurry tail is body-sparse (live) <-> handler "a separate, earlier covered op".

Run:        python3 verify_hero_select_p2_talentstamp_anchor.py
Self-test:  python3 verify_hero_select_p2_talentstamp_anchor.py --selftest
            (parser unit-tests + a per-direction RED-catch so the gate has teeth, incl.
             body-scoped exclusion of the 3 out-of-body talent arms, dense-uniform-all-10,
             bare-handle vs _Copy, skeleton-position reorder, and Flurry non-conflation)
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

# the §1-skeleton talent stamp — armed in EVERY body (dense-uniform). Bare handle; a
# `_Copy`/variant would be a DIFFERENT trigger.
TALENT_STAMP = "gg_trg_HeroPickAssignTalentTree"

# the sparse data-driven tail trigger — the talent stamp must NOT be conflated with it
# (only Arthur arms this, at the tail, via the per-slot EnableTrig array).
FLURRY_TAIL = "gg_trg_Flurry_AI"

EXPECTED_TALENT_PER_BODY = 1               # every body arms exactly 1
EXPECTED_TALENT_TOTAL = 10                 # 10 bodies x 1 (body-scoped; NOT the 13 file-wide)
ALL_HEROES = {h for _, h in HERO_FUNCS}    # dense-uniform occupant set = all 10

# the exact, arg-uniform skeleton arm signature (the bare talent trigger).
TALENT_SIG = f"call EnableTrigger({TALENT_STAMP})"


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
    capture, so gg_trg_HeroPickAssignTalentTree_Copy is distinct from the bare handle)."""
    return re.findall(r"call EnableTrigger\((gg_trg_[A-Za-z0-9_]+)\)", body)


def _talent_handles(body):
    """Ordered talent-stamp arm handles in a body (whole-identifier == TALENT_STAMP, so a
    `_Copy`/variant is NOT counted). This is the dense skeleton op family."""
    return [h for h in _all_enabletrigger_handles(body) if h == TALENT_STAMP]


def _talent_like_handles(body):
    """Ordered EnableTrigger handles whose name STARTS with the talent-stamp name — i.e.
    the bare handle AND any `_Copy`/variant. Used by the bare-handle tooth: a body whose
    talent-like arm is a variant (HeroPickAssignTalentTree_Copy) has a talent-like arm that
    is NOT the bare handle, so bare != talent-like trips."""
    return [h for h in _all_enabletrigger_handles(body)
            if h.startswith(TALENT_STAMP)]


def _wisp_consume_index(body):
    """Index of the wisp consume = first `KillUnit`/`h__RemoveUnit` of `GetTriggerUnit()`
    (9 bodies KillUnit; Gawain h__RemoveUnit). -1 if absent."""
    cand = [body.find(x) for x in
            ("call KillUnit(GetTriggerUnit())", "call h__RemoveUnit(GetTriggerUnit())")]
    cand = [c for c in cand if c >= 0]
    return min(cand) if cand else -1


def _talent_skeleton_positioned(body):
    """True iff this body's talent stamp arms AFTER DisableTrigger(GetTriggeringTrigger())
    and BEFORE the wisp consume — the §1 skeleton op #2 position (deferred owner/claim sets
    may sit between Disable and the stamp; that does not affect the covered-op ordering vs
    the covered Disable/KillWisp neighbours)."""
    di = body.find("call DisableTrigger(GetTriggeringTrigger())")
    ti = body.find(TALENT_SIG)
    wc = _wisp_consume_index(body)
    return di != -1 and ti != -1 and wc != -1 and di < ti < wc


def live_facts(extract_text):
    """Per-body talent-stamp facts, BODY-SCOPED to the 10 pick bodies (the 3 out-of-body
    talent arms are never read). Every value independently checkable so a single mutation
    trips exactly one anchor."""
    talent = {}        # hero -> [bare talent-stamp handles]   (== TALENT_STAMP only)
    talent_like = {}   # hero -> [talent-like handles]         (bare + any _Copy variant)
    positioned = {}    # hero -> talent arm is in §1 skeleton position
    flurry = {}        # hero -> [Flurry tail handles]         (non-conflation control)
    missing = []
    for func, hero in HERO_FUNCS:
        b = body_of(extract_text, func)
        if b is None:
            missing.append(hero)
            continue
        talent[hero] = _talent_handles(b)
        talent_like[hero] = _talent_like_handles(b)
        positioned[hero] = _talent_skeleton_positioned(b)
        flurry[hero] = [h for h in _all_enabletrigger_handles(b) if h == FLURRY_TAIL]
    return {
        "n_found": len(talent),
        "missing": missing,
        "talent": talent,
        "talent_like": talent_like,
        "positioned": positioned,
        "flurry": flurry,
    }


def all_rows(extract_text, runbook_text, handler_text):
    """Per-anchor rows: (label, live_ok, handler_ok, prose_ok, prose_required, detail)."""
    f = live_facts(extract_text)
    rbf = re.sub(r"\s+", " ", runbook_text)         # full runbook, normalized
    # normalize the handler: strip `//` line-markers + collapse whitespace so wrapped
    # header claims AND the real spine calls both match contiguously.
    hd = re.sub(r"\s+", " ", re.sub(r"//+", " ", handler_text))
    # raw handler (// kept) for ordering of the real spine lines.
    raw_h = handler_text
    rows = []

    def row(label, live_ok, handler_ok, prose_ok, prose_required, detail=""):
        rows.append((label, live_ok, handler_ok, prose_ok, prose_required, detail))

    # 1) all 10 hero pick bodies present
    live_ok = f["n_found"] == 10 and not f["missing"]
    row("bodies:present=10", live_ok,
        "10 hand-written Trig_<Hero>_Actions" in hd,
        "10 hand-written pick bodies" in rbf, True,
        "" if live_ok else f"missing/!=10: found={f['n_found']} missing={f['missing']}")

    # 2) dense-uniform: EVERY body arms exactly 1 talent stamp (occupant == all 10)
    occ = {h for h, v in f["talent"].items() if v}
    one_each = (occ == ALL_HEROES
                and all(len(v) == EXPECTED_TALENT_PER_BODY for v in f["talent"].values()))
    row("talentstamp:dense-uniform-all-10", one_each,
        "arm the talent stamp" in hd,
        "`gg_trg_HeroPickAssignTalentTree` (21" in rbf, True,
        "" if one_each else f"per-body talent-arm counts (expected 1 each, all 10)="
        f"{ {h: len(v) for h, v in f['talent'].items()} }")

    # 3) total-in-bodies == 10 (body-scope past the 3 out-of-body arms)
    total = sum(len(v) for v in f["talent"].values())
    live_ok = total == EXPECTED_TALENT_TOTAL
    row("talentstamp:total-in-bodies=10", live_ok,
        TALENT_SIG in raw_h,
        "the talent stamp" in rbf, True,
        "" if live_ok else f"in-body talent-arm total={total} (expected {EXPECTED_TALENT_TOTAL})")

    # 4) bare-handle: every talent-like arm IS the bare handle (no _Copy/variant)
    bare_ok = (sum(len(v) for v in f["talent_like"].values()) == EXPECTED_TALENT_TOTAL
               and all(all(h == TALENT_STAMP for h in v) for v in f["talent_like"].values()))
    row("talentstamp:bare-handle", bare_ok,
        TALENT_SIG in raw_h,
        "`gg_trg_HeroPickAssignTalentTree`" in rbf, True,
        "" if bare_ok else "a body's talent-like arm is not the bare gg_trg_HeroPickAssignTalentTree "
        f"(talent_like={ {h: v for h, v in f['talent_like'].items()} })")

    # 5) skeleton-position: talent arms AFTER Disable, BEFORE wisp consume, in every body
    pos_ok = all(f["positioned"].get(h) for h in ALL_HEROES)
    # handler spine ordering: DisableTrigger before EnableTrigger(talent) before KillUnit(wisp)
    h_di = raw_h.find("call DisableTrigger(GetTriggeringTrigger())")
    h_ti = raw_h.find(TALENT_SIG)
    h_ki = raw_h.find("call KillUnit(wisp)")
    handler_order = h_di != -1 and h_ti != -1 and h_ki != -1 and h_di < h_ti < h_ki
    row("talentstamp:skeleton-position", pos_ok,
        handler_order and "Disable -> EnableTalent -> KillWisp" in hd, None, False,
        "" if pos_ok else f"a body's talent arm is out of §1-skeleton position "
        f"(positioned={f['positioned']})")

    # 6) hardcoded-not-data: handler arms a LITERAL trigger, distinct from the data-driven
    #    tail EnableTrigger(udg_CastleSlot_EnableTrig[i]).
    handler_literal = (TALENT_SIG in raw_h
                       and "call EnableTrigger(udg_CastleSlot_EnableTrig[i])" in raw_h
                       and "separate, earlier covered op (EnableTalentStamp)" in hd)
    row("talentstamp:hardcoded-not-data", True, handler_literal, None, False,
        "" if handler_literal else "handler does not arm the talent stamp as a literal "
        "distinct from the data-driven EnableTrig tail")

    # 7) non-conflation: dense talent stamp (10) is NOT the sparse Flurry tail (Arthur only)
    flurry_occ = {h for h, v in f["flurry"].items() if v}
    nonconflate = (TALENT_STAMP != FLURRY_TAIL
                   and occ == ALL_HEROES               # talent dense
                   and flurry_occ == {"Arthur"}        # Flurry sparse
                   and occ != flurry_occ)
    row("talentstamp:flurry-non-conflation", nonconflate,
        "separate, earlier covered op" in hd, None, False,
        "" if nonconflate else f"talent occupants={sorted(occ)} flurry occupants={sorted(flurry_occ)} "
        "(talent must be dense-all-10, Flurry sparse-Arthur)")
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
    selftest baseline + the fixtures each RED-catch mutates. Encodes the DENSE-UNIFORM talent
    stamp in EVERY body at the §1-skeleton position (after Disable, before the wisp consume),
    the sparse Flurry tail-arm (Arthur only), AND plants OUT-OF-BODY talent arms so the
    body-scope exclusion is exercised. Gawain uses h__RemoveUnit (not KillUnit) for the wisp."""
    bodies = []
    for n, (func, hero) in enumerate(HERO_FUNCS):
        consume = ("    call h__RemoveUnit(GetTriggerUnit())\n" if hero == "Gawain"
                   else "    call KillUnit(GetTriggerUnit())\n")
        flurry = ("    call EnableTrigger(gg_trg_Flurry_AI)\n" if hero == "Arthur" else "")
        bodies.append(
            f"function {func} takes nothing returns nothing\n"
            "    call DisableTrigger(GetTriggeringTrigger())\n"
            f"    set udg_{hero}_owner=GetOwningPlayer(GetTriggerUnit())\n"   # deferred owner set
            "    call EnableTrigger(gg_trg_HeroPickAssignTalentTree)\n"        # talent stamp (every body)
            f"{consume}"
            "    call CreateNUnitsAtLocFacingLocBJ(1, 'Hxxx', GetOwningPlayer(GetTriggerUnit()), L, F)\n"
            f"{flurry}"
            "endfunction\n")
    # out-of-body talent arms (save/load + sample paths) — MUST NOT count toward the 10.
    bodies.append(
        "function Trig_Load_GUI_Actions takes nothing returns nothing\n"
        "    call EnableTrigger(gg_trg_HeroPickAssignTalentTree)\n"
        "    call EnableTrigger(gg_trg_HeroPickAssignTalentTree)\n"
        "endfunction\n")
    bodies.append(
        "function SampleDialogSystem__OnButtonClick takes nothing returns nothing\n"
        "    call EnableTrigger(gg_trg_HeroPickAssignTalentTree)\n"
        "endfunction\n")
    extract = "\n".join(bodies)
    handler = (
        "//  Replaces the SHARED mechanics of the 10 hand-written Trig_<Hero>_Actions pick bodies.\n"
        "//  This handler covers the data-uniform spine ...\n"
        "//    * the §1 5-line skeleton (disable re-entry, arm the talent stamp, consume the\n"
        "//      wisp, record the SavePlayerHero slot, select for the picker)  — parameterized\n"
        "    // OP ORDER ... Disable -> EnableTalent -> KillWisp -> HeroSpawn -> SpawnAbility -> ...\n"
        "    call DisableTrigger(GetTriggeringTrigger())\n"
        "    call EnableTrigger(gg_trg_HeroPickAssignTalentTree)\n"
        "    call KillUnit(wisp)\n"
        "    call CreateNUnitsAtLocFacingLocBJ(1, udg_CastleSlot_HeroType[i], picker, L, F)\n"
        "    // ... tail ...\n"
        "        if udg_CastleSlot_EnableTrig[i] != null then\n"
        "            call EnableTrigger(udg_CastleSlot_EnableTrig[i])\n"
        "        endif\n"
        "        // The talent-stamp arm is a separate, earlier covered op (EnableTalentStamp).\n"
    )
    runbook = (
        "## STEP 0 ... collapses the 10 hand-written pick bodies\n"
        "> The handler also arms two **pre-existing map triggers** — `gg_trg_HeroPickAssignTalentTree` "
        "(21 refs, the talent stamp) and, for Arthur only, `gg_trg_Flurry_AI` (9 refs, via the per-slot "
        "EnableTrig array).\n"
    )
    return extract, runbook, handler


def selftest():
    print("=== SELFTEST: parser unit-tests + per-direction RED-catch (teeth) ===")
    extract, runbook, handler = _synth_ok()

    # parser sanity (body-scoped: the 2 out-of-body funcs are NOT in HERO_FUNCS)
    f = live_facts(extract)
    assert f["n_found"] == 10 and not f["missing"], f
    assert {h for h, v in f["talent"].items() if v} == ALL_HEROES, f["talent"]
    assert sum(len(v) for v in f["talent"].values()) == EXPECTED_TALENT_TOTAL, f["talent"]
    assert all(f["positioned"].values()), f["positioned"]
    assert {h for h, v in f["flurry"].items() if v} == {"Arthur"}, f["flurry"]

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

    # 2) LIVE: drop a body's talent stamp -> dense-uniform + total trip
    bad = extract.replace(
        "function Trig_Lady_Guinevere_Actions takes nothing returns nothing\n"
        "    call DisableTrigger(GetTriggeringTrigger())\n"
        "    set udg_Guinevere_owner=GetOwningPlayer(GetTriggerUnit())\n"
        "    call EnableTrigger(gg_trg_HeroPickAssignTalentTree)\n",
        "function Trig_Lady_Guinevere_Actions takes nothing returns nothing\n"
        "    call DisableTrigger(GetTriggeringTrigger())\n"
        "    set udg_Guinevere_owner=GetOwningPlayer(GetTriggerUnit())\n", 1)
    c_dense = caught(all_rows(bad, runbook, handler), "talentstamp:dense-uniform-all-10")
    c_total_drop = caught(all_rows(bad, runbook, handler), "talentstamp:total-in-bodies=10")

    # 3) LIVE: a body arms it TWICE -> dense-uniform (count 2) + total (11) trip
    bad = extract.replace(
        "function Trig_Sir_Kay_Actions takes nothing returns nothing\n"
        "    call DisableTrigger(GetTriggeringTrigger())\n"
        "    set udg_Kay_owner=GetOwningPlayer(GetTriggerUnit())\n"
        "    call EnableTrigger(gg_trg_HeroPickAssignTalentTree)\n",
        "function Trig_Sir_Kay_Actions takes nothing returns nothing\n"
        "    call DisableTrigger(GetTriggeringTrigger())\n"
        "    set udg_Kay_owner=GetOwningPlayer(GetTriggerUnit())\n"
        "    call EnableTrigger(gg_trg_HeroPickAssignTalentTree)\n"
        "    call EnableTrigger(gg_trg_HeroPickAssignTalentTree)\n", 1)
    c_dense2 = caught(all_rows(bad, runbook, handler), "talentstamp:dense-uniform-all-10")
    c_total_add = caught(all_rows(bad, runbook, handler), "talentstamp:total-in-bodies=10")

    # 4) LIVE: a body's talent arm becomes the _Copy variant -> bare-handle + dense trip
    bad = extract.replace(
        "function Trig_Sir_Yvain_Actions takes nothing returns nothing\n"
        "    call DisableTrigger(GetTriggeringTrigger())\n"
        "    set udg_Yvain_owner=GetOwningPlayer(GetTriggerUnit())\n"
        "    call EnableTrigger(gg_trg_HeroPickAssignTalentTree)\n",
        "function Trig_Sir_Yvain_Actions takes nothing returns nothing\n"
        "    call DisableTrigger(GetTriggeringTrigger())\n"
        "    set udg_Yvain_owner=GetOwningPlayer(GetTriggerUnit())\n"
        "    call EnableTrigger(gg_trg_HeroPickAssignTalentTree_Copy)\n", 1)
    c_bare = caught(all_rows(bad, runbook, handler), "talentstamp:bare-handle")

    # 5) LIVE: move a body's talent arm AFTER the wisp consume -> skeleton-position trips
    bad = extract.replace(
        "    call EnableTrigger(gg_trg_HeroPickAssignTalentTree)\n"
        "    call KillUnit(GetTriggerUnit())\n"
        "    call CreateNUnitsAtLocFacingLocBJ(1, 'Hxxx', GetOwningPlayer(GetTriggerUnit()), L, F)\n"
        "    call EnableTrigger(gg_trg_Flurry_AI)\n",
        "    call KillUnit(GetTriggerUnit())\n"
        "    call CreateNUnitsAtLocFacingLocBJ(1, 'Hxxx', GetOwningPlayer(GetTriggerUnit()), L, F)\n"
        "    call EnableTrigger(gg_trg_HeroPickAssignTalentTree)\n"
        "    call EnableTrigger(gg_trg_Flurry_AI)\n", 1)  # Arthur's arm moved past the spawn
    c_pos = caught(all_rows(bad, runbook, handler), "talentstamp:skeleton-position")

    # 6) BODY-SCOPE teeth: plant ANOTHER out-of-body talent arm (func NOT in HERO_FUNCS).
    #    A correctly body-scoped gate must IGNORE it — total stays 10, dense stays green.
    bad = extract + (
        "\nfunction Trig_Some_Other_Repick takes nothing returns nothing\n"
        "    call EnableTrigger(gg_trg_HeroPickAssignTalentTree)\n"
        "endfunction\n")
    c_scope = (not caught(all_rows(bad, runbook, handler), "talentstamp:total-in-bodies=10")
               and not caught(all_rows(bad, runbook, handler), "talentstamp:dense-uniform-all-10"))

    # 7) FLURRY NON-CONFLATION teeth: the baseline already has Flurry sparse(Arthur)+talent
    #    dense(10). The non-conflation anchor must be GREEN at baseline (proves we did not
    #    merge the two families), AND must TRIP if the live talent set collapses to Arthur-only.
    c_nonconf_holds = not caught(all_rows(extract, runbook, handler),
                                 "talentstamp:flurry-non-conflation")
    # collapse talent to Arthur-only (drop 9 talent arms) -> non-conflation + dense + total trip
    bad = extract
    for hero in [h for _, h in HERO_FUNCS if h != "Arthur"]:
        bad = bad.replace(
            f"    set udg_{hero}_owner=GetOwningPlayer(GetTriggerUnit())\n"
            "    call EnableTrigger(gg_trg_HeroPickAssignTalentTree)\n",
            f"    set udg_{hero}_owner=GetOwningPlayer(GetTriggerUnit())\n", 1)
    c_nonconf_trip = caught(all_rows(bad, runbook, handler), "talentstamp:flurry-non-conflation")

    # 8) HANDLER drift: spine drops the talent arm literal -> total/bare/position trip
    bad_h = handler.replace("    call EnableTrigger(gg_trg_HeroPickAssignTalentTree)\n", "", 1)
    c_htotal = caught(all_rows(extract, runbook, bad_h), "talentstamp:total-in-bodies=10")
    c_hpos = caught(all_rows(extract, runbook, bad_h), "talentstamp:skeleton-position")

    # 9) HANDLER drift: spine reorders talent arm AFTER KillUnit(wisp) -> skeleton-position trips
    bad_h = handler.replace(
        "    call EnableTrigger(gg_trg_HeroPickAssignTalentTree)\n"
        "    call KillUnit(wisp)\n",
        "    call KillUnit(wisp)\n"
        "    call EnableTrigger(gg_trg_HeroPickAssignTalentTree)\n")
    c_hpos2 = caught(all_rows(extract, runbook, bad_h), "talentstamp:skeleton-position")

    # 10) HANDLER drift: drop the EnableTalentStamp separateness note -> hardcoded-not-data trips
    bad_h = handler.replace("separate, earlier covered op (EnableTalentStamp)", "unrelated thing")
    c_hsep = caught(all_rows(extract, runbook, bad_h), "talentstamp:hardcoded-not-data")

    # 11) HANDLER drift: drop the data-driven tail line -> hardcoded-not-data trips
    bad_h = handler.replace("            call EnableTrigger(udg_CastleSlot_EnableTrig[i])\n", "")
    c_hdata = caught(all_rows(extract, runbook, bad_h), "talentstamp:hardcoded-not-data")

    # 12) PROSE drift: runbook drops the talent-stamp armed-trigger claim -> dense-uniform trips
    bad_rb = runbook.replace("`gg_trg_HeroPickAssignTalentTree` (21", "`gg_trg_GONE` (0")
    c_prose = caught(all_rows(extract, bad_rb, handler), "talentstamp:dense-uniform-all-10")

    for name, val in [
        ("live body deleted", c_bodies), ("live drop a talent stamp (dense)", c_dense),
        ("live drop a talent stamp (total)", c_total_drop),
        ("live double talent stamp (dense)", c_dense2), ("live double talent stamp (total)", c_total_add),
        ("live _Copy variant (bare-handle)", c_bare), ("live talent moved past spawn (pos)", c_pos),
        ("body-scope holds (out-of-body ignored)", c_scope),
        ("flurry non-conflation holds at baseline", c_nonconf_holds),
        ("flurry non-conflation trips on collapse", c_nonconf_trip),
        ("handler drop talent literal (total)", c_htotal),
        ("handler drop talent literal (pos)", c_hpos),
        ("handler reorder talent past wisp (pos)", c_hpos2),
        ("handler drop EnableTalentStamp note", c_hsep),
        ("handler drop data-tail line", c_hdata),
        ("prose talent-claim drop", c_prose),
    ]:
        print(f"  {name:<46}caught : {val}")
    ok = base_ok and all([c_bodies, c_dense, c_total_drop, c_dense2, c_total_add, c_bare,
                          c_pos, c_scope, c_nonconf_holds, c_nonconf_trip, c_htotal, c_hpos,
                          c_hpos2, c_hsep, c_hdata, c_prose])
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
              "the talent-stamp op cites are now suspect. Re-ground vs the new bake.")
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
        print("RESULT: FAIL — hero-select P2 talent-stamp (EnableTalentStamp) skeleton op drifted:")
        for lbl, d in fail:
            print(f"  - {lbl}: {d}")
        return 1
    print("RESULT: GREEN — the §1-skeleton talent-stamp op is bound vs the md5-pinned extract: "
          "all 10 live pick bodies are present and EACH arms EXACTLY 1 bare "
          "EnableTrigger(gg_trg_HeroPickAssignTalentTree) (dense-uniform; 10 in-body total — "
          "body-scoped past the 3 out-of-body arms in Trig_Load_GUI_Actions + "
          "SampleDialogSystem__OnButtonClick, NOT the 13 file-wide), positioned in §1-skeleton "
          "order (AFTER DisableTrigger, BEFORE the wisp consume — KillUnit, or Gawain's "
          "h__RemoveUnit), matching the handler spine "
          "(DisableTrigger -> EnableTrigger(gg_trg_HeroPickAssignTalentTree) -> KillUnit(wisp), "
          "a HARDCODED literal distinct from the data-driven EnableTrigger(udg_CastleSlot_EnableTrig[i]) "
          "tail) + header 'Disable -> EnableTalent -> KillWisp' / 'separate, earlier covered op "
          "(EnableTalentStamp)' claims AND the runbook 'gg_trg_HeroPickAssignTalentTree (21 refs, the "
          "talent stamp)' armed-map-trigger claim; the dense talent stamp (all 10) is NOT conflated "
          "with the sparse Flurry tail-arm (Arthur only). The operator's collapse cannot silently drop, "
          "double-arm, _Copy-substitute, or reorder the per-pick talent stamp.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
