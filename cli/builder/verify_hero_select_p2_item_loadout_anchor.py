#!/usr/bin/env python3
r"""
verify_hero_select_p2_item_loadout_anchor.py
================================================================================
KOTR Hero-Select REDESIGN (Track 4) · P2 **per-slot item-loadout transfer-op
family** <-> handler authority <-> live extract binder.
Built 2026-06-19 by KOTR Builder (engine claude-p).

WHY THIS GATE EXISTS (a real, uncovered seam on the P2 apply path)
--------------------------------------------------------------------------------
`hero_select_p2_APPLY_RUNBOOK.md`'s Smoke test promises each picked hero "gets its
FULL item loadout"; the STEP-0 var table reserves the `CastleSlot_Item*` flat
sub-table (`ItemStart`/`ItemCount`/`Item`) for it. The handler then collapses all 10
hand-written `Trig_<Hero>_Actions` bodies' item adds into ONE windowed loop:
    set k = udg_CastleSlot_ItemStart[i]
    set stop = k + udg_CastleSlot_ItemCount[i]
    loop ... call UnitAddItemByIdSwapped(udg_CastleSlot_Item[k], hero) ... endloop
i.e. only the ordered per-slot item-rawcode list is data; the call itself is uniform
(2nd arg = the just-spawned hero, which in a live body is `GetLastCreatedUnit()`).
The handler header makes several checkable distribution claims the WE operator relies
on before deleting the 10 old bodies:
  1. EVERY one of the 10 slots loads its full loadout (>=1 item — no empty slot),
  2. the per-slot counts are Arthur/Guinevere/Nimue/Percival 6, Merlin/Kay/Lancelot 7,
     Galahad/Yvain/Gawain 5 (60 items total),
  3. every item add is the arg-UNIFORM UnitAddItemByIdSwapped(<itemid>, hero) — only the
     ordered item-rawcode list is per-slot data.
If any of those drift, the operator could bake a short/long item window, drop a hero's
loadout entirely (the table compiles fine with ItemCount==0 — a SILENT empty hero), or
mistake the uniform call for per-slot logic — and no other gate would catch it:
  * `verify_hero_select_p2_generated_j.py` / `verify_hero_select_p2_datatable.py` bind the
    MATERIALIZED Item flat+span table vs the catalog JSON — they prove the BAKED table is
    internally consistent, NOT that it matches the live bodies' item-op family nor the
    handler header's natural-language loadout claims (a header/table that drifts from the
    bodies the table is baked from goes uncaught there).
  * `verify_hero_select_p2_allyrescueinvuln_anchor.py` binds the ally/rescue/invuln
    transfer ops — a sibling op family; it never reads the item adds.
  * `verify_hero_select_p2_spawnloc_faceloc_anchor.py` binds the hero-spawn spine — a
    different op family.
  * `verify_hero_select_p2_loop.py` / `audit_hero_select_p2_equivalence.py` compile +
    op-equivalence-prove the handler; they never read the runbook .md, so a runbook/header
    loadout claim that drifts from the spine they prove goes uncaught.

So this gate closes the seam the established Track-4 way: it binds the runbook full-loadout
claim <-> handler header + spine authority <-> live extract item-op family, both ways,
against the md5-pinned canonical extract — the twin of the ally/rescue/invuln binder.

WHAT IT CHECKS (read-only; touches no .w3x and no shippable .j)
--------------------------------------------------------------------------------
  0. md5 pin: the live extract still hashes to the runbook-pinned md5 (a re-bake trips it).
  1. all 10 hand-written hero pick bodies are present in the live extract.
  2. full-loadout: every body loads >=1 item via the UNIFORM UnitAddItemByIdSwapped(<id>,
     GetLastCreatedUnit()) (live) <-> handler "Every one of the 10 slots loads its FULL
     loadout" <-> runbook "gets its FULL item loadout".
  3. item-distribution: live item counts == {Arthur/Guinevere/Nimue/Percival:6, Merlin/Kay/
     Lancelot:7, Galahad/Yvain/Gawain:5} (live) <-> handler per-slot count claim <-> runbook
     `CastleSlot_ItemCount` row.
  4. item-total: total live item adds == 60 (live) <-> handler "60 items total" <-> runbook
     `CastleSlot_Item` flat-table row.
  5. item-uniform: every live item add equals UnitAddItemByIdSwapped(<id>, GetLastCreatedUnit())
     (live) <-> handler spine UnitAddItemByIdSwapped(udg_CastleSlot_Item[k], hero) + "only the
     ordered item-rawcode list is per-slot data" <-> runbook `CastleSlot_Item` table.

Run:        python3 verify_hero_select_p2_item_loadout_anchor.py
Self-test:  python3 verify_hero_select_p2_item_loadout_anchor.py --selftest
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

# the catalog/handler item-loadout distribution the runbook full-loadout claim is filled
# against (every slot >=1; 60 total).
EXPECTED_ITEMS = {
    "Arthur": 6, "Guinevere": 6, "Nimue": 6, "Percival": 6,
    "Merlin": 7, "Kay": 7, "Lancelot": 7,
    "Galahad": 5, "Yvain": 5, "Gawain": 5,
}
EXPECTED_ITEM_TOTAL = sum(EXPECTED_ITEMS.values())  # 60

# the exact, arg-uniform call signature the live bodies use (canonicalized: the item
# rawcode collapsed to '<id>'). The hero in a live body is literally GetLastCreatedUnit().
ITEM_SIG = "call UnitAddItemByIdSwapped('<id>', GetLastCreatedUnit())"

# the handler spine line (post // strip + whitespace collapse).
ITEM_SPINE = "UnitAddItemByIdSwapped(udg_CastleSlot_Item[k], hero)"


def body_of(extract_text, func):
    """The body text of one Trig_<Hero>_Actions function, or None if gone."""
    m = re.search(
        r"function " + re.escape(func) + r" takes nothing returns nothing(.*?)\nendfunction",
        extract_text, re.DOTALL)
    return m.group(1) if m else None


def _canon_item_calls(body):
    """All `call UnitAddItemByIdSwapped(...)` one-liners in a body, item rawcode -> '<id>'."""
    out = []
    for raw in re.findall(r"call UnitAddItemByIdSwapped\([^\n]*\)", body):
        out.append(re.sub(r"'[^']*'", "'<id>'", raw.strip()))
    return out


def live_facts(extract_text):
    """Per-body item-loadout facts. Every value independently checkable so a single
    mutation trips exactly one anchor."""
    items = {}     # hero -> [canonicalized UnitAddItemByIdSwapped calls]
    missing = []
    for func, hero in HERO_FUNCS:
        b = body_of(extract_text, func)
        if b is None:
            missing.append(hero)
            continue
        items[hero] = _canon_item_calls(b)
    return {
        "n_found": len(items),
        "missing": missing,
        "items": items,
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

    # 2) full-loadout: every body loads >=1 item via the uniform UnitAddItemByIdSwapped
    item_counts = _counts(f["items"])
    live_ok = (f["n_found"] == 10
               and all(len(f["items"].get(h, [])) >= 1 for _fn, h in HERO_FUNCS)
               and _all_match(f["items"], ITEM_SIG))
    row("loadout:every-slot>=1", live_ok,
        "Every one of the 10 slots loads its FULL loadout" in hd,
        "gets its full item loadout" in rbf, True,
        "" if live_ok else f"item counts={item_counts} (each>=1, all UnitAddItemByIdSwapped(<id>,GetLastCreatedUnit()))")

    # 3) item-distribution: {6,6,6,6,7,7,7,5,5,5} by hero
    live_ok = item_counts == EXPECTED_ITEMS
    row("item:distribution", live_ok,
        "Arthur/Guinevere/Nimue/Percival 6 each" in hd
        and "Lancelot 7 each, Galahad/Yvain/Gawain 5 each" in hd,
        "`CastleSlot_ItemCount`" in rbf, True,
        "" if live_ok else f"live item counts={item_counts} (expected {EXPECTED_ITEMS})")

    # 4) item-total: 60 item adds across the 10 bodies
    total = sum(len(v) for v in f["items"].values())
    live_ok = total == EXPECTED_ITEM_TOTAL
    row("item:total=60", live_ok,
        "60 items total" in hd,
        "`CastleSlot_Item`" in rbf, True,
        "" if live_ok else f"live item total={total} (expected {EXPECTED_ITEM_TOTAL})")

    # 5) item-uniform: every item add = UnitAddItemByIdSwapped(<id>, GetLastCreatedUnit())
    live_ok = _all_match(f["items"], ITEM_SIG)
    row("item:add-uniform-spine", live_ok,
        ITEM_SPINE in hd and "only the ordered item-rawcode list is per-slot data (audit Item dimension)" in hd,
        "`CastleSlot_Item`" in rbf, True,
        "" if live_ok else "a live item add is not the uniform UnitAddItemByIdSwapped(<id>,GetLastCreatedUnit())")
    return rows


def _passed(live_ok, handler_ok, prose_ok, prose_required):
    return bool(live_ok) and bool(handler_ok) and (bool(prose_ok) or not prose_required)


def report(rows):
    print(f"{'ANCHOR':<30}{'LIVE':<8}{'HANDLER':<10}{'PROSE':<8}")
    for label, live_ok, handler_ok, prose_ok, prose_required, detail in rows:
        prose_cell = ("OK" if prose_ok else "DRIFT") if prose_required else "n/a"
        print(f"{label:<30}{'OK' if live_ok else 'DRIFT':<8}"
              f"{'OK' if handler_ok else 'DRIFT':<10}"
              f"{prose_cell:<8}"
              + (f"  -> {detail}" if detail else ""))


def _synth_ok():
    """A synthetic (extract, runbook, handler) triple satisfying every anchor — the
    selftest baseline + the fixtures each RED-catch mutates. Encodes the real per-hero
    item distribution (6/6/6/6/7/7/7/5/5/5 = 60) so the count anchors have teeth."""
    bodies = []
    for func, hero in HERO_FUNCS:
        head = f"function {func} takes nothing returns nothing\n"
        lines = []
        for n in range(EXPECTED_ITEMS[hero]):
            lines.append(f"    call UnitAddItemByIdSwapped('it{n:02d}', GetLastCreatedUnit())\n")
        bodies.append(head + "".join(lines) + "endfunction\n")
    extract = "\n".join(bodies)
    handler = (
        "//  Replaces the SHARED mechanics of the 10 hand-written Trig_<Hero>_Actions pick bodies.\n"
        "    // --- per-slot item loadout (variable-length flat sub-table) ---\n"
        "    // Every one of the 10 slots loads its FULL loadout (>=1 item): Arthur/Guinevere/Nimue/Percival\n"
        "    // 6 each, Merlin/Kay/Lancelot 7 each, Galahad/Yvain/Gawain 5 each — 60 items total.\n"
        "    // only the ordered item-rawcode list is per-slot data (audit Item dimension)\n"
        "    call UnitAddItemByIdSwapped(udg_CastleSlot_Item[k], hero)\n"
    )
    runbook = (
        "## STEP 2 — Wire the pedestals ... disable the 10 old `Trig_<Hero>_Actions`\n"
        "| `CastleSlot_ItemCount` | integer array | item flat sub-table length |\n"
        "| `CastleSlot_Item` | integer array | flat item-type rawcode table |\n"
        "Pick each hero in turn -> each spawns the correct hero-type ... gets its full item loadout,\n"
    )
    return extract, runbook, handler


def selftest():
    print("=== SELFTEST: parser unit-tests + per-direction RED-catch (teeth) ===")
    extract, runbook, handler = _synth_ok()

    # parser sanity
    f = live_facts(extract)
    assert f["n_found"] == 10 and not f["missing"], f
    assert _counts(f["items"]) == EXPECTED_ITEMS, _counts(f["items"])
    assert _all_match(f["items"], ITEM_SIG), f["items"]
    assert sum(len(v) for v in f["items"].values()) == EXPECTED_ITEM_TOTAL

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

    # 2) LIVE: empty one hero's whole loadout -> full-loadout trips
    bad = re.sub(
        r"function Trig_Sir_Galahad_Actions takes nothing returns nothing\n(?:.*?\n)*?endfunction\n",
        "function Trig_Sir_Galahad_Actions takes nothing returns nothing\nendfunction\n",
        extract, count=1)
    c_full = caught(all_rows(bad, runbook, handler), "loadout:every-slot>=1")

    # 3) LIVE: drop one of Arthur's 6 items -> item-distribution + total trip
    bad = extract.replace(
        "    call UnitAddItemByIdSwapped('it05', GetLastCreatedUnit())\n", "", 1)
    c_dist = caught(all_rows(bad, runbook, handler), "item:distribution")
    c_total = caught(all_rows(bad, runbook, handler), "item:total=60")

    # 4) LIVE: an item add loses its uniform hero arg -> item-uniform trips
    bad = extract.replace(
        "    call UnitAddItemByIdSwapped('it00', GetLastCreatedUnit())\n",
        "    call UnitAddItemByIdSwapped('it00', GetTriggerUnit())\n", 1)
    c_uni = caught(all_rows(bad, runbook, handler), "item:add-uniform-spine")

    # 5) HANDLER drift: spine drops the Item array -> item-uniform trips
    bad_h = handler.replace("udg_CastleSlot_Item[k]", "udg_WRONG_Item[k]")
    c_huni = caught(all_rows(extract, runbook, bad_h), "item:add-uniform-spine")

    # 6) HANDLER drift: header drops the distribution claim -> item-distribution trips
    bad_h = handler.replace("Merlin/Kay/Lancelot 7 each", "Merlin/Kay/Lancelot 8 each")
    c_hdist = caught(all_rows(extract, runbook, bad_h), "item:distribution")

    # 7) HANDLER drift: header drops the 60-total claim -> item-total trips
    bad_h = handler.replace("60 items total", "59 items total")
    c_htot = caught(all_rows(extract, runbook, bad_h), "item:total=60")

    # 8) PROSE drift: runbook drops the full-loadout claim -> full-loadout trips
    bad_rb = runbook.replace("gets its full item loadout", "gets nothing")
    c_prose = caught(all_rows(extract, bad_rb, handler), "loadout:every-slot>=1")

    # 9) PROSE drift: runbook drops the CastleSlot_Item table row -> item-uniform (table cite) trips
    bad_rb = runbook.replace("`CastleSlot_Item`", "`CastleSlot_GONE`")
    c_prtab = caught(all_rows(extract, bad_rb, handler), "item:add-uniform-spine")

    for name, val in [
        ("live body deleted", c_bodies), ("live empty loadout", c_full),
        ("live item 6->5", c_dist), ("live total 60->59", c_total),
        ("live item hero-arg drift", c_uni), ("handler Item-array drift", c_huni),
        ("handler dist-count drift", c_hdist), ("handler 60-total drift", c_htot),
        ("prose full-loadout drop", c_prose), ("prose CastleSlot_Item drop", c_prtab),
    ]:
        print(f"  {name:<28}caught : {val}")
    ok = base_ok and all([c_bodies, c_full, c_dist, c_total, c_uni,
                          c_huni, c_hdist, c_htot, c_prose, c_prtab])
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
              "the item-loadout op cites are now suspect. Re-ground vs the new bake.")
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
        print("RESULT: FAIL — hero-select P2 item-loadout op family drifted:")
        for lbl, d in fail:
            print(f"  - {lbl}: {d}")
        return 1
    print("RESULT: GREEN — the per-slot item loadout is bound vs the md5-pinned extract: all 10 "
          "live pick bodies are present; every body loads its FULL loadout (>=1 item) via the "
          "uniform UnitAddItemByIdSwapped(<id>, GetLastCreatedUnit()); the per-slot counts are "
          "{Arthur/Guinevere/Nimue/Percival:6, Merlin/Kay/Lancelot:7, Galahad/Yvain/Gawain:5} = 60 "
          "total — matching the handler spine (UnitAddItemByIdSwapped(udg_CastleSlot_Item[k], hero) "
          "over [ItemStart..ItemStart+ItemCount)) + header distribution AND the runbook full-loadout "
          "claim. The operator's STEP-1 item table cannot silently drift from the bodies it replaces "
          "(no short window, no empty hero).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
