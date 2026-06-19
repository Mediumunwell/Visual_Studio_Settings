#!/usr/bin/env python3
r"""
verify_hero_select_p2_allyrescueinvuln_anchor.py
================================================================================
KOTR Hero-Select REDESIGN (Track 4) · P2 APPLY-RUNBOOK **STEP-2 "Bind the
`gg_unit_*` handles for `CastleSlot_Ally`/`Rescue`/`Invuln`" bullet** <-> handler
authority <-> live extract binder.
Built 2026-06-19 by KOTR Builder (engine claude-p).

WHY THIS GATE EXISTS (a real, uncovered seam on the STEP-2 apply path)
--------------------------------------------------------------------------------
`hero_select_p2_APPLY_RUNBOOK.md` STEP 2's second fill bullet tells the WE operator:
    "- **Bind the `gg_unit_*` handles** for `CastleSlot_Ally`/`Rescue`/`Invuln` to the
       units P1 placed (these handles do not exist until P1's units are on the map)."
That one bullet is the load-bearing reason these three sub-tables are DEFERRED to
STEP-2 (not filled by InitCastleSlotData in STEP-1): they hold live `gg_unit_*` map
handles, which simply do not exist until P1's units are placed on the map. The handler
spine then consumes them by slot window via three uniform APIs:
    set udg_CastleSlot_Ally[k]    -> SetUnitOwner(.., picker, true)
    set udg_CastleSlot_Rescue[k]  -> MakeUnitRescuableToForceBJ(.., true, GetForceOfPlayer(picker))
    set udg_CastleSlot_Invuln[k]  -> SetUnitInvulnerable(.., false)
The handler header makes several checkable distribution claims the operator relies on
before deleting the 10 old `Trig_<Hero>_Actions` triggers:
  1. all three arrays hold `gg_unit_*` handles ONLY (never rawcodes / locations) — the
     reason they are STEP-2-deferred,
  2. the three live ops are arg-UNIFORM across all 10 bodies (only the ordered gg_unit_*
     list is per-slot data): owner = `(unit, picker, true)`, rescue = `(unit, true,
     GetForceOfPlayer(picker))`, invuln = `(unit, false)`,
  3. RESCUE distribution: Arthur makes 8 units rescuable, Nimue/Percival/Lancelot 1 each,
     the other 6 none,
  4. INVULN distribution: only Percival uses it (4 `'nheb'` mobs), the other 9 none,
  5. every one of the 10 bodies transfers >=1 pre-placed ally (SetUnitOwner on a gg_unit_).
If any of those drift, the operator could bind the wrong handle list, fill a rescue/invuln
window against the wrong unit set, or mistake a STEP-1-fillable scalar for a STEP-2-deferred
handle — silently dropping an ally transfer, leaving Percival's invuln mobs locked, or
binding Arthur's 8 rescues to the wrong force.

Yet NO existing gate binds THIS runbook bullet to the handler spine + live bodies:
  * `verify_hero_select_p2_spawnloc_faceloc_anchor.py` binds STEP-2's FIRST fill bullet
    (the SpawnLoc/FaceLoc hero-spawn spine) — a different op family; it never reads the
    ally/rescue/invuln transfer ops nor this bind bullet.
  * `verify_hero_select_p2_generated_j.py` / `verify_castleslot_global_contract.py` bind the
    MATERIALIZED data table + the STEP-0 `CastleSlot_*` contract — they prove the baked
    Start/Count windows vs the extract, NOT the runbook BIND bullet nor the handler header's
    natural-language distribution claims (a runbook/header that drifts from the bodies the
    table is baked from goes uncaught there).
  * `verify_hero_select_divergence_catalog_anchors.py` binds the catalog's §2 spawn-API
    divergence — not the ally/rescue/invuln transfer ops.
  * `verify_hero_select_p2_loop.py` / `audit_hero_select_p2_equivalence.py` (fix_specs)
    compile + op-equivalence-prove the handler; they never read the runbook .md, so a
    runbook bullet that drifts from the spine they prove goes uncaught.

So this gate closes the seam the established Track-4 way: it binds the STEP-2 bind bullet
<-> handler header + spine authority <-> live extract, both ways, against the md5-pinned
canonical extract — the twin of the SpawnLoc/FaceLoc / init-call / hero-ref / ExtrasHook
binders shipped 2026-06-18/19.

WHAT IT CHECKS (read-only; touches no .w3x and no shippable .j)
--------------------------------------------------------------------------------
  0. md5 pin: the live extract still hashes to the runbook-pinned md5 (a re-bake trips it).
  1. all 10 hand-written hero pick bodies are present in the live extract.
  2. ally: every body transfers >=1 pre-placed ally via the UNIFORM SetUnitOwner(gg_unit_,
     picker, true) (live) <-> handler ally spine <-> runbook names `CastleSlot_Ally`.
  3. rescue-distribution: live rescue counts == {Arthur:8, Nimue:1, Percival:1, Lancelot:1}
     (others 0) <-> handler header "Arthur makes 8 ... the other 6 none" <-> runbook `Rescue`.
  4. rescue-uniform: every live rescue op is MakeUnitRescuableToForceBJ(gg_unit_, true,
     GetForceOfPlayer(picker)) <-> handler rescue spine + "ordered gg_unit_* list ... Rescue
     dimension" <-> runbook gg_unit_ handles.
  5. invuln-distribution: live invuln counts == {Percival:4} (others 0) <-> handler header
     "Only Percival uses it (4 units) ... the other 9 slots InvulnCount==0" <-> runbook `Invuln`.
  6. invuln-uniform: every live invuln op is SetUnitInvulnerable(gg_unit_, false) <-> handler
     invuln spine + "ordered gg_unit_* list ... Invuln dimension" <-> runbook gg_unit_ handles.
  7. defer-reason: across ALL three op families every target is a gg_unit_ handle (0 non-gg)
     (live) <-> handler consumes all three gg_unit_ arrays via its spine <-> runbook
     "these handles do not exist until P1's units are on the map" (the STEP-2 deferral reason).

Run:        python3 verify_hero_select_p2_allyrescueinvuln_anchor.py
Self-test:  python3 verify_hero_select_p2_allyrescueinvuln_anchor.py --selftest
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

# the catalog/handler distribution the runbook bind bullet is filled against.
EXPECTED_RESCUE = {"Arthur": 8, "Nimue": 1, "Percival": 1, "Lancelot": 1}  # others 0
EXPECTED_INVULN = {"Percival": 4}                                          # others 0

# the exact, arg-uniform call signatures the handler spine consumes (canonicalized:
# every gg_unit_<name> handle collapsed to gg_unit_*, whitespace single-spaced). The
# picker in a live body is literally GetOwningPlayer(GetTriggerUnit()).
OWNER_SIG = "call SetUnitOwner(gg_unit_*, GetOwningPlayer(GetTriggerUnit()), true)"
RESCUE_SIG = ("call MakeUnitRescuableToForceBJ(gg_unit_*, true, "
              "GetForceOfPlayer(GetOwningPlayer(GetTriggerUnit())))")
INVULN_SIG = "call SetUnitInvulnerable(gg_unit_*, false)"

# the handler spine lines (post // strip + whitespace collapse).
OWNER_SPINE = "SetUnitOwner(udg_CastleSlot_Ally[k], picker, true)"
RESCUE_SPINE = "MakeUnitRescuableToForceBJ(udg_CastleSlot_Rescue[k], true, GetForceOfPlayer(picker))"
INVULN_SPINE = "SetUnitInvulnerable(udg_CastleSlot_Invuln[k], false)"


def body_of(extract_text, func):
    """The body text of one Trig_<Hero>_Actions function, or None if gone."""
    m = re.search(
        r"function " + re.escape(func) + r" takes nothing returns nothing(.*?)\nendfunction",
        extract_text, re.DOTALL)
    return m.group(1) if m else None


def _canon_calls(body, verb):
    """All `call <verb>(...)` one-liners in a body, gg_unit_<name> -> gg_unit_*."""
    out = []
    for raw in re.findall(r"call " + re.escape(verb) + r"\([^\n]*\)", body):
        out.append(re.sub(r"gg_unit_\w+", "gg_unit_*", raw.strip()))
    return out


def live_facts(extract_text):
    """Per-body ally/rescue/invuln transfer-op facts. Every value independently checkable
    so a single mutation trips exactly one anchor."""
    owner = {}     # hero -> [canonicalized SetUnitOwner calls]
    rescue = {}    # hero -> [canonicalized MakeUnitRescuableToForceBJ calls]
    invuln = {}    # hero -> [canonicalized SetUnitInvulnerable calls]
    missing = []
    for func, hero in HERO_FUNCS:
        b = body_of(extract_text, func)
        if b is None:
            missing.append(hero)
            continue
        owner[hero] = _canon_calls(b, "SetUnitOwner")
        rescue[hero] = _canon_calls(b, "MakeUnitRescuableToForceBJ")
        invuln[hero] = _canon_calls(b, "SetUnitInvulnerable")
    return {
        "n_found": len(owner),
        "missing": missing,
        "owner": owner,
        "rescue": rescue,
        "invuln": invuln,
    }


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


def runbook_bind_clause(rb):
    """The STEP-2 'Bind the gg_unit_* handles' bullet, collapsed to single-spaced text
    for contiguous token matching; '' if gone."""
    m = re.search(r"\*\*Bind the `gg_unit_\*` handles\*\*.*?on the map\)", rb, re.DOTALL)
    return re.sub(r"\s+", " ", m.group(0)) if m else ""


def all_rows(extract_text, runbook_text, handler_text):
    """Per-anchor rows: (label, live_ok, handler_ok, prose_ok, prose_required, detail)."""
    f = live_facts(extract_text)
    rbf = re.sub(r"\s+", " ", runbook_text)         # full runbook, normalized
    clause = runbook_bind_clause(runbook_text)      # the STEP-2 bind bullet, normalized
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
        "10 old `Trig_<Hero>_Actions`" in rbf, True,
        "" if live_ok else f"missing/!=10: found={f['n_found']} missing={f['missing']}")

    # 2) ally: every body transfers >=1 pre-placed ally via the uniform SetUnitOwner
    owner_counts = _counts(f["owner"])
    live_ok = (f["n_found"] == 10
               and all(len(f["owner"].get(h, [])) >= 1 for _fn, h in HERO_FUNCS)
               and _all_match(f["owner"], OWNER_SIG))
    row("ally:owner-uniform-spine", live_ok,
        OWNER_SPINE in hd and "pre-placed ally ownership transfer" in hd,
        "`CastleSlot_Ally`" in clause, True,
        "" if live_ok else f"owner counts={owner_counts} (each>=1, all SetUnitOwner(gg_unit_,picker,true))")

    # 3) rescue distribution: {Arthur:8, Nimue:1, Percival:1, Lancelot:1}, others 0
    rescue_counts = _counts(f["rescue"])
    live_ok = rescue_counts == EXPECTED_RESCUE
    row("rescue:distribution", live_ok,
        "Arthur makes 8 units rescuable, Nimue/Percival/Lancelot 1 each, the other 6 none" in hd,
        "`Rescue`" in clause, True,
        "" if live_ok else f"live rescue counts={rescue_counts} (expected {EXPECTED_RESCUE})")

    # 4) rescue uniform: every rescue op = MakeUnitRescuableToForceBJ(gg_unit_, true, force(picker))
    live_ok = _all_match(f["rescue"], RESCUE_SIG)
    row("rescue:gg-uniform", live_ok,
        RESCUE_SPINE in hd and "only the ordered gg_unit_* list is per-slot data (audit Rescue dimension)" in hd,
        "`gg_unit_*`" in clause, True,
        "" if live_ok else "a live rescue op is not the uniform MakeUnitRescuableToForceBJ(gg_unit_,true,force(picker))")

    # 5) invuln distribution: {Percival:4}, others 0
    invuln_counts = _counts(f["invuln"])
    live_ok = invuln_counts == EXPECTED_INVULN
    row("invuln:distribution", live_ok,
        "Only Percival uses it (4 units)" in hd and "the other 9 slots have InvulnCount==0" in hd,
        "`Invuln`" in clause, True,
        "" if live_ok else f"live invuln counts={invuln_counts} (expected {EXPECTED_INVULN})")

    # 6) invuln uniform: every invuln op = SetUnitInvulnerable(gg_unit_, false)
    live_ok = _all_match(f["invuln"], INVULN_SIG)
    row("invuln:gg-uniform", live_ok,
        INVULN_SPINE in hd and "only the ordered gg_unit_* list is per-slot data (audit Invuln dimension)" in hd,
        "`gg_unit_*`" in clause, True,
        "" if live_ok else "a live invuln op is not the uniform SetUnitInvulnerable(gg_unit_,false)")

    # 7) defer-reason: ALL three op families target ONLY gg_unit_ handles (0 non-gg) — the
    #    reason the bullet is STEP-2-deferred (handles don't exist until P1 places units).
    non_gg = []
    for fam, d in (("owner", f["owner"]), ("rescue", f["rescue"]), ("invuln", f["invuln"])):
        for hero, calls in d.items():
            for c in calls:
                if "gg_unit_*" not in c:
                    non_gg.append(f"{fam}:{hero}:{c}")
    live_ok = f["n_found"] == 10 and not non_gg and (
        any(f["owner"].values()) and any(f["rescue"].values()) and any(f["invuln"].values()))
    row("defer-reason:handles-need-P1", live_ok,
        OWNER_SPINE in hd and RESCUE_SPINE in hd and INVULN_SPINE in hd,
        "do not exist until P1's units are on the map" in clause, True,
        "" if live_ok else f"a transfer op targets a non-gg_unit handle: {non_gg[:3]}")
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
    selftest baseline + the fixtures each RED-catch mutates. Encodes the real rescue
    (8/1/1/1) + invuln (Percival 4) distributions so the count anchors have teeth."""
    bodies = []
    for func, hero in HERO_FUNCS:
        head = f"function {func} takes nothing returns nothing\n"
        # every body transfers >=1 ally via the uniform owner sig
        lines = [f"    call SetUnitOwner(gg_unit_ally_{hero}, GetOwningPlayer(GetTriggerUnit()), true)\n"]
        for n in range(EXPECTED_RESCUE.get(hero, 0)):
            lines.append("    call MakeUnitRescuableToForceBJ(gg_unit_r_%s_%d, true, "
                         "GetForceOfPlayer(GetOwningPlayer(GetTriggerUnit())))\n" % (hero, n))
        for n in range(EXPECTED_INVULN.get(hero, 0)):
            lines.append(f"    call SetUnitInvulnerable(gg_unit_nheb_{n:04d}, false)\n")
        bodies.append(head + "".join(lines) + "endfunction\n")
    extract = "\n".join(bodies)
    handler = (
        "//  Replaces the SHARED mechanics of the 10 hand-written Trig_<Hero>_Actions pick bodies.\n"
        "    // --- per-slot pre-placed ally ownership transfer (variable-length flat sub-table) ---\n"
        "    call SetUnitOwner(udg_CastleSlot_Ally[k], picker, true)\n"
        "    // --- per-slot RESCUE transfer --- Arthur makes 8 units rescuable, Nimue/Percival/Lancelot\n"
        "    // 1 each, the other 6 none. only the ordered gg_unit_* list is per-slot data (audit Rescue dimension)\n"
        "    call MakeUnitRescuableToForceBJ(udg_CastleSlot_Rescue[k], true, GetForceOfPlayer(picker))\n"
        "    // --- per-slot INVULN clear --- Only Percival uses it (4 units); the other 9 slots have\n"
        "    // InvulnCount==0. only the ordered gg_unit_* list is per-slot data (audit Invuln dimension)\n"
        "    call SetUnitInvulnerable(udg_CastleSlot_Invuln[k], false)\n"
    )
    runbook = (
        "## STEP 2 — Wire the pedestals ... disable the 10 old `Trig_<Hero>_Actions`\n"
        "- **Bind the `gg_unit_*` handles** for `CastleSlot_Ally`/`Rescue`/`Invuln` to the units P1\n"
        "  placed (these handles do not exist until P1's units are on the map).\n"
    )
    return extract, runbook, handler


def selftest():
    print("=== SELFTEST: parser unit-tests + per-direction RED-catch (teeth) ===")
    extract, runbook, handler = _synth_ok()

    # parser sanity
    f = live_facts(extract)
    assert f["n_found"] == 10 and not f["missing"], f
    assert _counts(f["rescue"]) == EXPECTED_RESCUE, _counts(f["rescue"])
    assert _counts(f["invuln"]) == EXPECTED_INVULN, _counts(f["invuln"])
    assert _all_match(f["owner"], OWNER_SIG), f["owner"]

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
    bad = extract.replace("function Trig_Merlin_Actions takes nothing returns nothing",
                          "function Trig_GONE_Actions takes nothing returns nothing")
    c_bodies = caught(all_rows(bad, runbook, handler), "bodies:present=10")

    # 2) LIVE: drop one of Arthur's 8 rescues -> rescue-distribution trips
    bad = extract.replace(
        "    call MakeUnitRescuableToForceBJ(gg_unit_r_Arthur_7, true, GetForceOfPlayer(GetOwningPlayer(GetTriggerUnit())))\n",
        "", 1)
    c_rdist = caught(all_rows(bad, runbook, handler), "rescue:distribution")

    # 3) LIVE: give a 2nd hero an invuln clear -> invuln-distribution trips
    bad = extract.replace(
        "function Trig_King_Arthur_Actions takes nothing returns nothing\n",
        "function Trig_King_Arthur_Actions takes nothing returns nothing\n"
        "    call SetUnitInvulnerable(gg_unit_nheb_9999, false)\n", 1)
    c_idist = caught(all_rows(bad, runbook, handler), "invuln:distribution")

    # 4) LIVE: a rescue op loses its uniform force arg -> rescue-uniform trips
    bad = extract.replace(
        "    call MakeUnitRescuableToForceBJ(gg_unit_r_Arthur_0, true, GetForceOfPlayer(GetOwningPlayer(GetTriggerUnit())))\n",
        "    call MakeUnitRescuableToForceBJ(gg_unit_r_Arthur_0, true, GetPlayersAll())\n", 1)
    c_runi = caught(all_rows(bad, runbook, handler), "rescue:gg-uniform")

    # 5) LIVE: an ally transfer targets a non-gg handle -> defer-reason trips (handle universality)
    bad = extract.replace(
        "    call SetUnitOwner(gg_unit_ally_Yvain, GetOwningPlayer(GetTriggerUnit()), true)\n",
        "    call SetUnitOwner(GetLastCreatedUnit(), GetOwningPlayer(GetTriggerUnit()), true)\n", 1)
    c_defer = caught(all_rows(bad, runbook, handler), "defer-reason:handles-need-P1")

    # 6) HANDLER drift: spine drops the Rescue array -> rescue-uniform trips
    bad_h = handler.replace("udg_CastleSlot_Rescue[k]", "udg_WRONG_Rescue[k]")
    c_hres = caught(all_rows(extract, runbook, bad_h), "rescue:gg-uniform")

    # 7) HANDLER drift: header drops the invuln distribution claim -> invuln-distribution trips
    bad_h = handler.replace("Only Percival uses it (4 units)", "Only Percival uses it (5 units)")
    c_hinv = caught(all_rows(extract, runbook, bad_h), "invuln:distribution")

    # 8) PROSE drift: runbook drops the deferral reason -> defer-reason trips
    bad_rb = runbook.replace("do not exist until P1's units are on the map", "always exist")
    c_prose = caught(all_rows(extract, bad_rb, handler), "defer-reason:handles-need-P1")

    # 9) PROSE drift: runbook drops the gg_unit_* token -> rescue-uniform (gg cite) trips
    bad_rb = runbook.replace("**Bind the `gg_unit_*` handles**", "**Bind the unit handles**")
    c_prgg = caught(all_rows(extract, bad_rb, handler), "rescue:gg-uniform")

    for name, val in [
        ("live body deleted", c_bodies), ("live rescue 8->7", c_rdist),
        ("live 2nd-hero invuln", c_idist), ("live rescue force drift", c_runi),
        ("live ally non-gg handle", c_defer), ("handler Rescue-array drift", c_hres),
        ("handler invuln-count drift", c_hinv), ("prose defer-reason drop", c_prose),
        ("prose gg_unit_* drop", c_prgg),
    ]:
        print(f"  {name:<28}caught : {val}")
    ok = base_ok and all([c_bodies, c_rdist, c_idist, c_runi, c_defer,
                          c_hres, c_hinv, c_prose, c_prgg])
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
              "the ally/rescue/invuln transfer-op cites are now suspect. Re-ground vs the new bake.")
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
        print("RESULT: FAIL — hero-select P2 ally/rescue/invuln gg_unit bind drifted:")
        for lbl, d in fail:
            print(f"  - {lbl}: {d}")
        return 1
    print("RESULT: GREEN — the STEP-2 'Bind the gg_unit_* handles for CastleSlot_Ally/Rescue/"
          "Invuln' bullet is bound vs the md5-pinned extract: all 10 live pick bodies are present; "
          "every ally transfer is the uniform SetUnitOwner(gg_unit_,picker,true); rescue is "
          "{Arthur:8, Nimue/Percival/Lancelot:1} (others 0) via the uniform "
          "MakeUnitRescuableToForceBJ(gg_unit_,true,force(picker)); invuln is {Percival:4} (others 0) "
          "via the uniform SetUnitInvulnerable(gg_unit_,false); and ALL three op families target "
          "gg_unit_ handles only — matching the handler spine + header distribution AND the runbook "
          "bind bullet ('handles do not exist until P1's units are on the map'). The operator's "
          "STEP-2 handle bind cannot silently drift from the bodies it replaces.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
