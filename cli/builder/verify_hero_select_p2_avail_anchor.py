#!/usr/bin/env python3
r"""
verify_hero_select_p2_avail_anchor.py
================================================================================
KOTR Hero-Select REDESIGN (Track 4) · P2 **per-slot AVAILABILITY-toggle transfer-op
family** <-> handler authority <-> live extract binder.
Built 2026-06-19 by KOTR Builder (engine claude-p).

WHY THIS GATE EXISTS (a real, uncovered seam on the P2 apply path)
--------------------------------------------------------------------------------
`hero_select_p2_APPLY_RUNBOOK.md`'s Smoke test promises a picked hero "marks Merlin/
Galahad's avail unit-type unavailable"; the STEP-0 var table reserves the
`CastleSlot_Avail*` flat sub-table (`AvailStart`/`AvailCount`/`Avail`) for it. The
handler then collapses the two hand-written `Trig_<Hero>_Actions` bodies' availability
toggles into ONE windowed loop:
    set k = udg_CastleSlot_AvailStart[i]
    set stop = k + udg_CastleSlot_AvailCount[i]
    loop ... call SetPlayerUnitAvailableBJ(udg_CastleSlot_Avail[k], false, picker) ... endloop
i.e. only the ordered per-slot unit-type-rawcode list is data; the call itself is uniform
(2nd arg = false — mark unavailable; 3rd arg = the picker, which in a live body is
`GetOwningPlayer(GetTriggerUnit())`). Unlike the item loadout this op is SPARSE: only
Merlin ('Hgam') and Galahad ('H007') use it (1 type each); the other 8 slots have
AvailCount==0 (the loop is a no-op). The handler header makes several checkable claims
the WE operator relies on before deleting the 10 old bodies:
  1. EXACTLY Merlin + Galahad carry an avail toggle (the other 8 slots carry none),
  2. each occupant marks exactly 1 unit-type unavailable (Merlin 'Hgam', Galahad 'H007';
     2 avail toggles total),
  3. every avail toggle is the arg-UNIFORM SetPlayerUnitAvailableBJ(<id>, false, picker) —
     only the ordered unit-type rawcode list is per-slot data.
If any of those drift, the operator could bake an avail row onto the wrong slot, drop
Merlin's or Galahad's toggle (the table compiles fine with AvailCount==0 — a SILENT
still-available unit type), or mistake the uniform call for per-slot logic — and no other
gate would catch it:
  * `verify_hero_select_p2_generated_j.py` / `verify_hero_select_p2_datatable.py` bind the
    MATERIALIZED Avail flat+span table vs the catalog JSON — they prove the BAKED table is
    internally consistent, NOT that it matches the live bodies' avail-op family nor the
    handler header's natural-language availability claims (a header/table that drifts from
    the bodies the table is baked from goes uncaught there).
  * `verify_hero_select_p2_item_loadout_anchor.py` binds the per-slot item loadout — a
    sibling op family; it never reads the avail toggles.
  * `verify_hero_select_p2_allyrescueinvuln_anchor.py` binds the ally/rescue/invuln
    transfer ops — the three flat sub-tables that bracket Avail on the spine; it never
    reads the avail toggle in between.
  * `verify_hero_select_p2_spawnloc_faceloc_anchor.py` binds the hero-spawn spine — a
    different op family.
  * `verify_hero_select_p2_loop.py` / `audit_hero_select_p2_equivalence.py` compile +
    op-equivalence-prove the handler; they never read the runbook .md, so a runbook/header
    avail claim that drifts from the spine they prove goes uncaught.

So this gate closes the seam the established Track-4 way: it binds the runbook avail claim
<-> handler header + spine authority <-> live extract avail-op family, both ways, against
the md5-pinned canonical extract — the twin of the item-loadout + ally/rescue/invuln
binders. CRUCIAL TEETH: the live extract has FOUR more SetPlayerUnitAvailableBJ calls
OUTSIDE the 10 pick bodies (Trig_newMerlin_Actions, Trig_newGalahad_Actions,
Trig_Flying_Galahad_Actions, Trig_One_Flying_Galahad_Actions — the villager/flying
variants). Counting those would inflate the family; this gate BODY-SCOPES to the 10
hand-written Trig_<Hero>_Actions pick bodies so only the real pick-path toggles count.

WHAT IT CHECKS (read-only; touches no .w3x and no shippable .j)
--------------------------------------------------------------------------------
  0. md5 pin: the live extract still hashes to the runbook-pinned md5 (a re-bake trips it).
  1. all 10 hand-written hero pick bodies are present in the live extract.
  2. occupants: EXACTLY {Merlin, Galahad} carry an in-body avail toggle (the other 8 carry
     none) (live, body-scoped) <-> handler "Only Merlin/Galahad use it" <-> runbook
     "marks Merlin/Galahad's avail unit-type unavailable".
  3. avail-distribution: live in-body counts == {Merlin:1, Galahad:1, rest:0} (live) <->
     handler "1 type each ... the other 8 slots have AvailCount==0" <-> runbook
     `CastleSlot_AvailCount` row.
  4. avail-rawcodes: Merlin marks 'Hgam', Galahad marks 'H007' (live) <-> handler header
     SetPlayerUnitAvailableBJ('Hgam'/'H007', false, picker) <-> runbook `CastleSlot_Avail`.
  5. avail-uniform: every in-body avail toggle = SetPlayerUnitAvailableBJ(<id>, false,
     GetOwningPlayer(GetTriggerUnit())) (live) <-> handler spine
     SetPlayerUnitAvailableBJ(udg_CastleSlot_Avail[k], false, picker) + "only the ordered
     unit-type rawcode list is per-slot data" <-> runbook `CastleSlot_Avail`.

Run:        python3 verify_hero_select_p2_avail_anchor.py
Self-test:  python3 verify_hero_select_p2_avail_anchor.py --selftest
            (parser unit-tests + a per-direction RED-catch so the gate has teeth,
             incl. body-scoped exclusion of out-of-body avail calls)
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

# the catalog/handler avail distribution the runbook claim is filled against. SPARSE:
# only Merlin + Galahad mark a type unavailable (1 each); the other 8 slots carry none.
EXPECTED_AVAIL = {
    "Merlin": ["Hgam"],
    "Galahad": ["H007"],
}
EXPECTED_AVAIL_COUNTS = {h: 1 for h in EXPECTED_AVAIL}     # {Merlin:1, Galahad:1}
EXPECTED_AVAIL_TOTAL = sum(len(v) for v in EXPECTED_AVAIL.values())  # 2
EXPECTED_OCCUPANTS = set(EXPECTED_AVAIL)                   # {Merlin, Galahad}

# the exact, arg-uniform call signature the live pick bodies use (canonicalized: the
# unit-type rawcode collapsed to '<id>'). The picker in a live body is literally
# GetOwningPlayer(GetTriggerUnit()).
AVAIL_SIG = "call SetPlayerUnitAvailableBJ('<id>', false, GetOwningPlayer(GetTriggerUnit()))"

# the handler spine line (post // strip + whitespace collapse).
AVAIL_SPINE = "SetPlayerUnitAvailableBJ(udg_CastleSlot_Avail[k], false, picker)"


def body_of(extract_text, func):
    """The body text of one Trig_<Hero>_Actions function, or None if gone. Anchored on the
    exact `function <name> takes nothing returns nothing` ... `endfunction` span so the
    out-of-body villager/flying SetPlayerUnitAvailableBJ calls can never leak in."""
    m = re.search(
        r"function " + re.escape(func) + r" takes nothing returns nothing(.*?)\nendfunction",
        extract_text, re.DOTALL)
    return m.group(1) if m else None


def _avail_rawcodes(body):
    """Ordered unit-type rawcodes from `call SetPlayerUnitAvailableBJ('<id>', ...)` in a body."""
    out = []
    for raw in re.findall(r"call SetPlayerUnitAvailableBJ\('([^']*)'", body):
        out.append(raw)
    return out


def _avail_calls(body):
    """All `call SetPlayerUnitAvailableBJ(...)` one-liners in a body, rawcode -> '<id>'."""
    out = []
    for raw in re.findall(r"call SetPlayerUnitAvailableBJ\([^\n]*\)", body):
        out.append(re.sub(r"'[^']*'", "'<id>'", raw.strip()))
    return out


def live_facts(extract_text):
    """Per-body avail facts, BODY-SCOPED to the 10 pick bodies. Every value independently
    checkable so a single mutation trips exactly one anchor."""
    rawcodes = {}  # hero -> [unit-type rawcodes]
    calls = {}     # hero -> [canonicalized SetPlayerUnitAvailableBJ calls]
    missing = []
    for func, hero in HERO_FUNCS:
        b = body_of(extract_text, func)
        if b is None:
            missing.append(hero)
            continue
        rawcodes[hero] = _avail_rawcodes(b)
        calls[hero] = _avail_calls(b)
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
        "10 old `Trig_<Hero>_Actions`" in rbf, True,
        "" if live_ok else f"missing/!=10: found={f['n_found']} missing={f['missing']}")

    # 2) occupants: EXACTLY {Merlin, Galahad} carry an in-body avail toggle
    occ = _occupants(f["rawcodes"])
    live_ok = occ == EXPECTED_OCCUPANTS
    row("avail:occupants={Merlin,Galahad}", live_ok,
        "Only Merlin/Galahad use it (1 type each); the other 8 slots have AvailCount==0" in hd,
        # the runbook claim wraps "Merlin/\nGalahad's" -> a space after the slash once
        # normalized; bind to the contiguous tail so the wrap can't false-DRIFT it.
        "galahad's avail unit-type unavailable" in rbf.lower(), True,
        "" if live_ok else f"in-body avail occupants={sorted(occ)} (expected {sorted(EXPECTED_OCCUPANTS)})")

    # 3) avail-distribution: {Merlin:1, Galahad:1}, total 2
    counts = _counts(f["rawcodes"])
    total = sum(len(v) for v in f["rawcodes"].values())
    live_ok = counts == EXPECTED_AVAIL_COUNTS and total == EXPECTED_AVAIL_TOTAL
    row("avail:distribution+total=2", live_ok,
        "1 type each); the other 8 slots have AvailCount==0" in hd,
        "`CastleSlot_AvailCount`" in rbf, True,
        "" if live_ok else f"live avail counts={counts} total={total} (expected {EXPECTED_AVAIL_COUNTS}, total {EXPECTED_AVAIL_TOTAL})")

    # 4) avail-rawcodes: Merlin 'Hgam', Galahad 'H007'
    live_ok = {h: v for h, v in f["rawcodes"].items() if v} == EXPECTED_AVAIL
    row("avail:rawcodes", live_ok,
        "SetPlayerUnitAvailableBJ('Hgam', false, picker)" in hd
        and "SetPlayerUnitAvailableBJ('H007', false, picker)" in hd,
        "`CastleSlot_Avail`" in rbf, True,
        "" if live_ok else f"live avail rawcodes={ {h: v for h, v in f['rawcodes'].items() if v} } (expected {EXPECTED_AVAIL})")

    # 5) avail-uniform: every toggle = SetPlayerUnitAvailableBJ(<id>, false, GetOwningPlayer(GetTriggerUnit()))
    live_ok = _all_match(f["calls"], AVAIL_SIG)
    row("avail:uniform-spine", live_ok,
        AVAIL_SPINE in hd
        and "only the ordered unit-type rawcode list is per-slot data (audit Avail dimension)" in hd,
        "`CastleSlot_Avail`" in rbf, True,
        "" if live_ok else "a live avail toggle is not the uniform SetPlayerUnitAvailableBJ(<id>,false,GetOwningPlayer(GetTriggerUnit()))")
    return rows


def _passed(live_ok, handler_ok, prose_ok, prose_required):
    return bool(live_ok) and bool(handler_ok) and (bool(prose_ok) or not prose_required)


def report(rows):
    print(f"{'ANCHOR':<36}{'LIVE':<8}{'HANDLER':<10}{'PROSE':<8}")
    for label, live_ok, handler_ok, prose_ok, prose_required, detail in rows:
        prose_cell = ("OK" if prose_ok else "DRIFT") if prose_required else "n/a"
        print(f"{label:<36}{'OK' if live_ok else 'DRIFT':<8}"
              f"{'OK' if handler_ok else 'DRIFT':<10}"
              f"{prose_cell:<8}"
              + (f"  -> {detail}" if detail else ""))


def _synth_ok():
    """A synthetic (extract, runbook, handler) triple satisfying every anchor — the
    selftest baseline + the fixtures each RED-catch mutates. Encodes the real sparse avail
    distribution (only Merlin 'Hgam' + Galahad 'H007') so the count/occupant anchors have
    teeth, AND plants an OUT-OF-BODY avail call so the body-scope exclusion is exercised."""
    bodies = []
    for func, hero in HERO_FUNCS:
        head = f"function {func} takes nothing returns nothing\n"
        lines = []
        for rc in EXPECTED_AVAIL.get(hero, []):
            lines.append(f"    call SetPlayerUnitAvailableBJ('{rc}', false, GetOwningPlayer(GetTriggerUnit()))\n")
        bodies.append(head + "".join(lines) + "endfunction\n")
    # out-of-body avail calls (the villager/flying variants) — MUST NOT be counted.
    bodies.append(
        "function Trig_newGalahad_Actions takes nothing returns nothing\n"
        "    call SetPlayerUnitAvailableBJ('H007', false, udg_SaveLoadEvent_Player)\n"
        "endfunction\n")
    bodies.append(
        "function Trig_Flying_Galahad_Actions takes nothing returns nothing\n"
        "    call SetPlayerUnitAvailableBJ('H007', true, GetOwningPlayer(GetTriggerUnit()))\n"
        "endfunction\n")
    extract = "\n".join(bodies)
    handler = (
        "//  Replaces the SHARED mechanics of the 10 hand-written Trig_<Hero>_Actions pick bodies.\n"
        "    // --- per-slot AVAILABILITY toggle (variable-length flat sub-table) ---\n"
        "    // faithful to Merlin's SetPlayerUnitAvailableBJ('Hgam', false, picker) and Galahad's\n"
        "    // SetPlayerUnitAvailableBJ('H007', false, picker) at this exact position. Only Merlin/Galahad\n"
        "    // use it (1 type each); the other 8 slots have AvailCount==0 -> the loop is a no-op.\n"
        "    // only the ordered unit-type rawcode list is per-slot data (audit Avail dimension)\n"
        "    call SetPlayerUnitAvailableBJ(udg_CastleSlot_Avail[k], false, picker)\n"
    )
    runbook = (
        "## STEP 2 — Wire the pedestals ... disable the 10 old `Trig_<Hero>_Actions`\n"
        "| `CastleSlot_AvailCount` | integer array | avail flat sub-table length |\n"
        "| `CastleSlot_Avail` | integer array | flat unit-type rawcode made UNAVAILABLE to the picker |\n"
        "Pick each hero in turn -> ... marks Merlin/Galahad's avail unit-type unavailable,\n"
    )
    return extract, runbook, handler


def selftest():
    print("=== SELFTEST: parser unit-tests + per-direction RED-catch (teeth) ===")
    extract, runbook, handler = _synth_ok()

    # parser sanity (body-scoped: the 2 out-of-body funcs are NOT in HERO_FUNCS)
    f = live_facts(extract)
    assert f["n_found"] == 10 and not f["missing"], f
    assert _occupants(f["rawcodes"]) == EXPECTED_OCCUPANTS, _occupants(f["rawcodes"])
    assert {h: v for h, v in f["rawcodes"].items() if v} == EXPECTED_AVAIL, f["rawcodes"]
    assert sum(len(v) for v in f["rawcodes"].values()) == EXPECTED_AVAIL_TOTAL
    assert _all_match(f["calls"], AVAIL_SIG), f["calls"]

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

    # 2) LIVE: give a non-occupant (Arthur) an avail toggle -> occupants + distribution trip
    bad = extract.replace(
        "function Trig_King_Arthur_Actions takes nothing returns nothing\n",
        "function Trig_King_Arthur_Actions takes nothing returns nothing\n"
        "    call SetPlayerUnitAvailableBJ('hfoo', false, GetOwningPlayer(GetTriggerUnit()))\n")
    c_occ = caught(all_rows(bad, runbook, handler), "avail:occupants={Merlin,Galahad}")
    c_dist_add = caught(all_rows(bad, runbook, handler), "avail:distribution+total=2")

    # 3) LIVE: drop Galahad's only avail toggle -> occupants + distribution + rawcodes trip
    bad = extract.replace(
        "    call SetPlayerUnitAvailableBJ('H007', false, GetOwningPlayer(GetTriggerUnit()))\n", "", 1)
    c_dist_drop = caught(all_rows(bad, runbook, handler), "avail:distribution+total=2")
    c_raw_drop = caught(all_rows(bad, runbook, handler), "avail:rawcodes")

    # 4) LIVE: wrong rawcode (Merlin 'Hgam'->'Hxxx') -> rawcodes trips
    bad = extract.replace("SetPlayerUnitAvailableBJ('Hgam', false, GetOwningPlayer(GetTriggerUnit()))",
                          "SetPlayerUnitAvailableBJ('Hxxx', false, GetOwningPlayer(GetTriggerUnit()))", 1)
    c_raw = caught(all_rows(bad, runbook, handler), "avail:rawcodes")

    # 5) LIVE: a toggle loses its uniform args (true instead of false) -> uniform trips
    bad = extract.replace(
        "    call SetPlayerUnitAvailableBJ('Hgam', false, GetOwningPlayer(GetTriggerUnit()))\n",
        "    call SetPlayerUnitAvailableBJ('Hgam', true, GetOwningPlayer(GetTriggerUnit()))\n", 1)
    c_uni = caught(all_rows(bad, runbook, handler), "avail:uniform-spine")

    # 6) BODY-SCOPE TEETH: plant ANOTHER out-of-body avail call (a func NOT in HERO_FUNCS).
    #    A correctly body-scoped gate must IGNORE it — distribution/occupants stay GREEN. (If
    #    scoping regressed to a flat grep, this extra 'H007' would inflate the family and trip.)
    bad = extract + (
        "\nfunction Trig_One_Flying_Galahad_Actions takes nothing returns nothing\n"
        "    call SetPlayerUnitAvailableBJ('H007', false, GetOwningPlayer(GetTriggerUnit()))\n"
        "endfunction\n")
    c_scope = (not caught(all_rows(bad, runbook, handler), "avail:occupants={Merlin,Galahad}")
               and not caught(all_rows(bad, runbook, handler), "avail:distribution+total=2"))

    # 7) HANDLER drift: spine drops the Avail array -> uniform trips
    bad_h = handler.replace("udg_CastleSlot_Avail[k]", "udg_WRONG_Avail[k]")
    c_huni = caught(all_rows(extract, runbook, bad_h), "avail:uniform-spine")

    # 8) HANDLER drift: header drops the occupant claim -> occupants trips
    bad_h = handler.replace("Only Merlin/Galahad", "Only Merlin/Lancelot")
    c_hocc = caught(all_rows(extract, runbook, bad_h), "avail:occupants={Merlin,Galahad}")

    # 9) HANDLER drift: header drops a rawcode -> rawcodes trips
    bad_h = handler.replace("SetPlayerUnitAvailableBJ('H007', false, picker)",
                            "SetPlayerUnitAvailableBJ('Hzzz', false, picker)")
    c_hraw = caught(all_rows(extract, runbook, bad_h), "avail:rawcodes")

    # 10) PROSE drift: runbook drops the avail claim -> occupants trips
    bad_rb = runbook.replace("marks Merlin/Galahad's avail unit-type unavailable", "marks nothing")
    c_prose = caught(all_rows(extract, bad_rb, handler), "avail:occupants={Merlin,Galahad}")

    # 11) PROSE drift: runbook drops the CastleSlot_Avail table row -> uniform (table cite) trips
    bad_rb = runbook.replace("`CastleSlot_Avail`", "`CastleSlot_GONE`")
    c_prtab = caught(all_rows(extract, bad_rb, handler), "avail:uniform-spine")

    for name, val in [
        ("live body deleted", c_bodies), ("live extra occupant", c_occ),
        ("live extra occ dist", c_dist_add), ("live drop occupant dist", c_dist_drop),
        ("live drop occupant raw", c_raw_drop), ("live wrong rawcode", c_raw),
        ("live non-uniform args", c_uni), ("body-scope holds (out-of-body ignored)", c_scope),
        ("handler Avail-array drift", c_huni), ("handler occupant drift", c_hocc),
        ("handler rawcode drift", c_hraw), ("prose avail-claim drop", c_prose),
        ("prose CastleSlot_Avail drop", c_prtab),
    ]:
        print(f"  {name:<28}caught : {val}")
    ok = base_ok and all([c_bodies, c_occ, c_dist_add, c_dist_drop, c_raw_drop, c_raw,
                          c_uni, c_scope, c_huni, c_hocc, c_hraw, c_prose, c_prtab])
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
              "the avail-toggle op cites are now suspect. Re-ground vs the new bake.")
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
        print("RESULT: FAIL — hero-select P2 avail-toggle op family drifted:")
        for lbl, d in fail:
            print(f"  - {lbl}: {d}")
        return 1
    print("RESULT: GREEN — the per-slot availability toggle is bound vs the md5-pinned extract: all "
          "10 live pick bodies are present; EXACTLY Merlin + Galahad carry an in-body avail toggle "
          "(the other 8 carry none — body-scoped past the 4 villager/flying SetPlayerUnitAvailableBJ "
          "calls); each marks 1 unit-type unavailable (Merlin 'Hgam', Galahad 'H007' = 2 total) via "
          "the uniform SetPlayerUnitAvailableBJ(<id>, false, GetOwningPlayer(GetTriggerUnit())) — "
          "matching the handler spine (SetPlayerUnitAvailableBJ(udg_CastleSlot_Avail[k], false, picker) "
          "over [AvailStart..AvailStart+AvailCount)) + header occupant/rawcode claims AND the runbook "
          "avail claim. The operator's STEP-1 avail table cannot silently drift from the bodies it "
          "replaces (no mis-slotted row, no still-available unit type).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
