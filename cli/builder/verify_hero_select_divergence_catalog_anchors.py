#!/usr/bin/env python3
"""
verify_hero_select_divergence_catalog_anchors.py
================================================================================
KOTR Hero-Select REDESIGN (Track 4) · P1-PREP DIVERGENCE-CATALOG PROSE <-> LIVE-EXTRACT binder.

WHY THIS GATE EXISTS (a real, uncovered seam — the LAST unbound Track-4 source-of-truth)
--------------------------------------------------------------------------------
`hero_select_pick_triggers_DIVERGENCE_CATALOG_2026-06-17_claude-p.md` is the
byte-exact grounding the P2 data-driven pick collapse is filled from "with zero
re-derivation." Its §2 ships an explicit, self-described **"byte-exact, re-greppable"**
anchor table pinning, for each of the 10 hand-written pick slots:

  * the `Trig_<Hero>_Actions` FUNCTION-HEAD line (L49272 … L50763),
  * the `InitTrig` ENTER-RECT registration line + the rect name it binds
    (L49315 `gg_rct_Arthur` … L50801 `gg_rct_Gawain`),
  * the per-slot HeroTypeId rawcode (Arthur `'Harf'` … Gawain `'H014'`),
  * the SPAWN-API divergence (9× `CreateNUnitsAtLocFacingLocBJ`, 1× plain
    `CreateNUnitsAtLoc` + `bj_UNIT_FACING` for Kay @ L49951),
  * and (§5, the materialization correction) Gawain's real ExtrasHook: a neutral
    `'h012'` polymorph caster targeting `gg_unit_H014_0610` + `gg_unit_Yuln_0448`,
    pedestal pair removed via `h__RemoveUnit`.

Those are LIVE-MAP facts but they live in **prose no gate parses**:

  * `verify_hero_select_p2_datatable.py` (fix_specs) MATERIALIZES §2 into a JSON
    record + Init `.j` and verifies that emission — it never reads the catalog .md.
  * `verify_hero_select_p2_loop.py` (fix_specs) COMPILE-proves the generic handler
    the §3 architecture describes — it never reads the catalog's line anchors.
  * `verify_hero_select_phase0_recon_anchors.py` binds the **recon** prose; the
    catalog CORRECTS that recon (§0) and carries its OWN anchor table.
  * `verify_hero_select_p2_runbook_anchors.py` binds the **runbook** counts/range,
    not the catalog's per-slot function-head + enter-rect + rawcode anchors.

So the instant the live extract drifts (a WE re-save renumbers JASS — the staleness
class that already bit B4b and the hero-select recon/runbook L-cites) the catalog
would keep telling P2 "Gawain's pick body starts at L50763, enter-rect at L50801,
type `'H014'`" while the live map disagrees — a SILENT stale-catalog brick feeding
the P2 fill "with zero re-derivation." This binder closes that seam.

EVERY §2/§5 anchor verified byte-exact at first bind (2026-06-18) — no stale cite to
correct; the catalog already self-corrected its one soft attribution in §5. This gate
makes that correctness MACHINE-CHECKED going forward, both directions.

WHAT IT CHECKS (read-only; touches no .w3x and no shippable .j)
--------------------------------------------------------------------------------
  1. The live canonical extract still hashes to the md5 the catalog pins
     (a re-bake is caught immediately, before any per-cite check can false-pass).
  2. FUNCTION-HEAD anchors: each cited line IS `function Trig_<Hero>_Actions takes`,
     AND the catalog prose still carries that `L<line>` cite.
  3. ENTER-RECT anchors: each cited line IS `TriggerRegisterEnterRectSimple(..., gg_rct_<X>)`,
     AND the catalog prose still carries that `L<line>` cite + the `gg_rct_<X>` name.
  4. RAWCODE+API anchors: each slot's first spawn line inside its body is
     `CreateNUnits<api>(1, '<CODE>'` with the expected code + API (Kay diverges to
     plain `CreateNUnitsAtLoc`+`bj_UNIT_FACING`), AND prose carries `'<CODE>'`.
  5. SPAWN divergence: exactly 1 of the 10 slot spawns uses plain `CreateNUnitsAtLoc`
     (Kay @ L49951) and 9 use `...FacingLocBJ`, AND prose carries the `9×`/`Kay L49951`.
  6. GAWAIN extras (§5): `'h012'` / `gg_unit_H014_0610` / `gg_unit_Yuln_0448` /
     `h__RemoveUnit` all present in the live Gawain region [L50763,L50824], AND prose
     (§5) still carries each token.

Exit 0 only if md5 matches AND every anchor holds in BOTH directions.

Run:        python3 verify_hero_select_divergence_catalog_anchors.py
Self-test:  python3 verify_hero_select_divergence_catalog_anchors.py --selftest

STANDALONE by design: prints RESULT and exits 1 on any drift, but is NOT wired into
verify_all.py, so the 178/178 static sweep is unchanged. Sibling of the hero-select
recon + runbook binders; same EXTRACT / md5 / both-ways-binding contract.
"""
import hashlib
import re
import sys
from pathlib import Path

EXTRACT = Path.home() / "Warcraft III" / "KOTR" / "_extract_v050" / "war3map.j"
CATALOG = (Path.home() / "Warcraft III" / "KOTR" / "_crew"
           / "hero_select_pick_triggers_DIVERGENCE_CATALOG_2026-06-17_claude-p.md")

# the md5 the catalog pins the canonical extract to (Grounding header §0)
CATALOG_CLAIMED_MD5 = "967131658fd8d4fb27ee0d7f74e4bd22"

# The dated audit footer this binder appends to the catalog redundantly mentions
# cited L-numbers / tokens; counting it would make the reverse check VACUOUS against
# a body edit (it would still "find" the cite in our own note). The reverse direction
# must bind the catalog BODY P2 fills from, so we strip the note before searching prose.
NOTE_MARKER = "**Machine-checked —"

# --- the 10 pick slots, in live order. (label, act_head_line, fn_name,
#      enter_rect_line, rect_name, hero_rawcode, spawn_api) ---
#   spawn_api: "FacingLocBJ" -> CreateNUnitsAtLocFacingLocBJ ; "AtLoc" -> CreateNUnitsAtLoc
SLOTS = [
    ("Arthur",    49272, "King_Arthur",      49315, "gg_rct_Arthur",     "'Harf'", "FacingLocBJ"),
    ("Guinevere", 49443, "Lady_Guinevere",   49480, "gg_rct_Guinevere",  "'Hvwd'", "FacingLocBJ"),
    ("Nimue",     49608, "Lady_of_the_Lake", 49644, "gg_rct_Nimue",      "'Hjai'", "FacingLocBJ"),
    ("Merlin",    49772, "Merlin",           49816, "gg_rct_Merlin",     "'Hant'", "FacingLocBJ"),
    ("Kay",       49944, "Sir_Kay",          49979, "gg_rct_Kay",        "'Hpb1'", "AtLoc"),
    ("Percival",  50107, "Sir_Percival",     50146, "gg_rct_Percival",   "'Huth'", "FacingLocBJ"),
    ("Galahad",   50274, "Sir_Galahad",      50308, "gg_rct_Galahad",    "'Hpb2'", "FacingLocBJ"),
    ("Lancelot",  50436, "Sir_Lancelot",     50472, "gg_rct_Lancelot",   "'Hart'", "FacingLocBJ"),
    ("Yvain",     50600, "Sir_Yvain",        50635, "gg_rct_Yvain",      "'H013'", "FacingLocBJ"),
    ("Gawain",    50763, "Sir_Gawain",       50801, "gg_rct_Gawain",     "'H014'", "FacingLocBJ"),
]

# Kay's spawn-API divergence is anchored to its own line in the catalog.
KAY_SPAWN_LINE = 49951

# --- Gawain §5 ExtrasHook tokens — must live inside the Gawain region AND in §5 prose
GAWAIN_REGION = (50763, 50824)
GAWAIN_EXTRAS = ["'h012'", "gg_unit_H014_0610", "gg_unit_Yuln_0448", "h__RemoveUnit"]


def catalog_body(catalog_text):
    """The P2-facing catalog body, excluding this binder's own audit footer."""
    return catalog_text.split(NOTE_MARKER, 1)[0]


def spawn_api_on(line):
    """Return 'AtLoc' / 'FacingLocBJ' / None for the spawn API used on a body line."""
    if re.search(r"CreateNUnitsAtLocFacingLocBJ\(1, ", line):
        return "FacingLocBJ"
    if re.search(r"CreateNUnitsAtLoc\(1, ", line):
        return "AtLoc"
    return None


def hero_spawn_line(extract_lines, start, end, code):
    """The CreateNUnits* line (1-based) within [start, end] that spawns this hero's
    own rawcode `code` (e.g. 'H014'). Gawain's body ALSO spawns a neutral 'h012'
    polymorph caster (§5 ExtrasHook) on an earlier CreateNUnitsAtLoc line, so we must
    key off the hero rawcode, not merely the first spawn call."""
    for n in range(start, min(end, len(extract_lines)) + 1):
        ln = extract_lines[n - 1]
        if "CreateNUnitsAtLoc" in ln and f"(1, {code}" in ln:
            return n
    return None


def audit_slots(extract_lines, body):
    rows = []

    def line(n):
        return extract_lines[n - 1] if 0 < n <= len(extract_lines) else "<<EOF>>"

    body_starts = [s[1] for s in SLOTS]

    for idx, (label, act_l, fn, rect_l, rect, code, api) in enumerate(SLOTS):
        body_end = body_starts[idx + 1] - 1 if idx + 1 < len(SLOTS) else GAWAIN_REGION[1]

        # --- function-head anchor ---
        head = line(act_l)
        head_live = head.startswith(f"function Trig_{fn}_Actions takes")
        head_prose = f"L{act_l}" in body
        d = ""
        if not head_live:
            d = f"L{act_l} != Trig_{fn}_Actions ({head.strip()!r})"
        elif not head_prose:
            d = f"catalog prose dropped the L{act_l} function-head cite"
        rows.append((f"head:{label}", head_live, head_prose, d))

        # --- enter-rect anchor ---
        er = line(rect_l)
        er_live = ("TriggerRegisterEnterRectSimple(" in er) and (rect in er)
        er_prose = (f"L{rect_l}" in body) and (rect in body)
        d = ""
        if not er_live:
            d = f"L{rect_l} != EnterRectSimple(...,{rect}) ({er.strip()!r})"
        elif not er_prose:
            d = f"catalog prose dropped L{rect_l} or {rect}"
        rows.append((f"enter-rect:{label}", er_live, er_prose, d))

        # --- rawcode + spawn-API anchor (this hero's own spawn line in the body) ---
        sp_n = hero_spawn_line(extract_lines, act_l, body_end, code)
        sp = line(sp_n) if sp_n else "<<no spawn>>"
        code_ok = (code in sp)
        api_ok = (spawn_api_on(sp) == api)
        raw_live = code_ok and api_ok
        raw_prose = code in body
        d = ""
        if not raw_live:
            bits = []
            if not code_ok:
                bits.append(f"rawcode {code} not on spawn line ({sp.strip()[:60]!r})")
            if not api_ok:
                bits.append(f"spawn API != {api} (got {spawn_api_on(sp)})")
            d = "; ".join(bits)
        elif not raw_prose:
            d = f"catalog prose dropped the {code} rawcode cite"
        rows.append((f"rawcode:{label}", raw_live, raw_prose, d))

    return rows


def audit_spawn_divergence(extract_lines, body):
    """§2 field-5: exactly 1 slot (Kay) uses plain CreateNUnitsAtLoc; 9 use FacingLocBJ."""
    def line(n):
        return extract_lines[n - 1] if 0 < n <= len(extract_lines) else "<<EOF>>"

    body_starts = [s[1] for s in SLOTS]
    apis = []
    for idx, slot in enumerate(SLOTS):
        act_l, code = slot[1], slot[5]
        body_end = body_starts[idx + 1] - 1 if idx + 1 < len(SLOTS) else GAWAIN_REGION[1]
        sp_n = hero_spawn_line(extract_lines, act_l, body_end, code)
        apis.append(spawn_api_on(line(sp_n)) if sp_n else None)
    n_atloc = apis.count("AtLoc")
    n_facing = apis.count("FacingLocBJ")
    kay_line = line(KAY_SPAWN_LINE)
    kay_live = ("CreateNUnitsAtLoc(1, 'Hpb1'" in kay_line) and ("bj_UNIT_FACING" in kay_line)
    live_ok = (n_atloc == 1) and (n_facing == 9) and kay_live
    # reverse: prose carries the divergence counts + Kay's anchored line
    prose_ok = ("9×" in body) and (f"L{KAY_SPAWN_LINE}" in body)
    d = ""
    if not live_ok:
        bits = []
        if n_atloc != 1 or n_facing != 9:
            bits.append(f"live spawn-API split AtLoc={n_atloc} FacingLocBJ={n_facing} (expect 1/9)")
        if not kay_live:
            bits.append(f"L{KAY_SPAWN_LINE} != Kay CreateNUnitsAtLoc+bj_UNIT_FACING ({kay_line.strip()[:70]!r})")
        d = "; ".join(bits)
    elif not prose_ok:
        d = f"catalog prose dropped '9×' or the L{KAY_SPAWN_LINE} Kay anchor"
    return [("spawn-API divergence (1×AtLoc/9×FacingLocBJ)", live_ok, prose_ok, d)]


def audit_gawain_extras(extract_lines, body):
    """§5 corrected ExtrasHook tokens — present in the live Gawain region AND in prose."""
    lo, hi = GAWAIN_REGION
    region = "\n".join(extract_lines[lo - 1:hi])
    rows = []
    for tok in GAWAIN_EXTRAS:
        live_ok = tok in region
        prose_ok = tok in body
        d = ""
        if not live_ok:
            d = f"{tok!r} absent from live Gawain region [L{lo},L{hi}]"
        elif not prose_ok:
            d = f"catalog §5 prose dropped {tok!r}"
        rows.append((f"gawain-extras:{tok}", live_ok, prose_ok, d))
    return rows


def all_rows(extract_text, catalog_text):
    body = catalog_body(catalog_text)
    extract_lines = extract_text.split("\n")
    rows = []
    rows += audit_slots(extract_lines, body)
    rows += audit_spawn_divergence(extract_lines, body)
    rows += audit_gawain_extras(extract_lines, body)
    return rows


def report(rows):
    print(f"{'ANCHOR':<44}{'LIVE':<8}{'PROSE':<8}")
    for label, live_ok, prose_ok, detail in rows:
        print(f"{label:<44}{'OK' if live_ok else 'DRIFT':<8}{'OK' if prose_ok else 'DRIFT':<8}"
              + (f"  -> {detail}" if detail else ""))


def _synthetic():
    """Build a synthetic live extract + catalog that satisfy EVERY anchor (for selftest)."""
    lines = ["x"] * 76000
    for label, act_l, fn, rect_l, rect, code, api in SLOTS:
        lines[act_l - 1] = f"function Trig_{fn}_Actions takes nothing returns nothing"
        lines[rect_l - 1] = (f"    call TriggerRegisterEnterRectSimple(gg_trg_{fn}, {rect})")
        if label == "Kay":
            continue  # Kay's single hero spawn lives on its anchored line (below)
        spawn = "CreateNUnitsAtLocFacingLocBJ" if api == "FacingLocBJ" else "CreateNUnitsAtLoc"
        # place a spawn line a few lines into each body
        lines[act_l + 2] = f"    call {spawn}(1, {code}, p, loc, f)"
    # Kay's anchored divergence line — the ONLY 'Hpb1' spawn (as in the live map)
    lines[KAY_SPAWN_LINE - 1] = ("    call CreateNUnitsAtLoc(1, 'Hpb1', p, "
                                 "GetRandomLocInRect(gg_rct_Arthur_Kay_Lancelot_Appear), bj_UNIT_FACING)")
    # Gawain extras inside its region
    g0 = GAWAIN_REGION[0]
    for k, tok in enumerate(GAWAIN_EXTRAS):
        lines[g0 + 3 + k] = f"    call doit({tok})"
    text = "\n".join(lines)

    # catalog prose that carries every required cite
    prose = []
    for label, act_l, fn, rect_l, rect, code, api in SLOTS:
        prose.append(f"| {label} | L{act_l} | L{rect_l} `{rect}` | {code} |")
    prose.append(f"9× CreateNUnitsAtLocFacingLocBJ, 1× CreateNUnitsAtLoc Kay L{KAY_SPAWN_LINE}")
    prose += [tok for tok in GAWAIN_EXTRAS]
    catalog = "\n".join(prose)
    return text, catalog


def selftest():
    print("=== SELFTEST: baseline all-green + per-category RED-catch (teeth) ===")
    text, catalog = _synthetic()
    base = all_rows(text, catalog)
    base_ok = all(lo and po for _, lo, po, _ in base)
    print(f"  baseline all-green             : {base_ok}")
    if not base_ok:
        for r in base:
            if not (r[1] and r[2]):
                print("    FAIL ROW:", r)
        return 3

    lines = text.split("\n")

    # 1) HEAD live drift: renumber Arthur's body head out from under L49272
    bad = list(lines); bad[49272 - 1] = "x"
    r1 = all_rows("\n".join(bad), catalog)
    caught_head = any(lbl == "head:Arthur" and not lo for lbl, lo, po, d in r1)

    # 2) ENTER-RECT live drift: change the rect name on Gawain's reg line
    bad = list(lines)
    bad[50801 - 1] = "    call TriggerRegisterEnterRectSimple(gg_trg_Sir_Gawain, gg_rct_WRONG)"
    r2 = all_rows("\n".join(bad), catalog)
    caught_rect = any(lbl == "enter-rect:Gawain" and not lo for lbl, lo, po, d in r2)

    # 3) RAWCODE live drift: change Arthur's hero rawcode on its body spawn line
    bad = list(lines)
    bad[49272 + 2] = "    call CreateNUnitsAtLocFacingLocBJ(1, 'XXXX', p, loc, f)"
    r3 = all_rows("\n".join(bad), catalog)
    caught_raw = any(lbl == "rawcode:Arthur" and not lo for lbl, lo, po, d in r3)

    # 4) SPAWN divergence drift: make Kay use FacingLocBJ too (0× AtLoc)
    bad = list(lines)
    bad[KAY_SPAWN_LINE - 1] = "    call CreateNUnitsAtLocFacingLocBJ(1, 'Hpb1', p, loc, f)"
    r4 = all_rows("\n".join(bad), catalog)
    caught_div = any(lbl.startswith("spawn-API divergence") and not lo for lbl, lo, po, d in r4)

    # 5) GAWAIN extras live drift: drop h012 from the region
    bad = text.replace("'h012'", "'ZZZZ'", 1)
    r5 = all_rows(bad, catalog)
    caught_gaw = any(lbl == "gawain-extras:'h012'" and not lo for lbl, lo, po, d in r5)

    # 6) PROSE drop: catalog no longer carries Lancelot's L50436 head cite
    bad_cat = catalog.replace("L50436", "L99999")
    r6 = all_rows(text, bad_cat)
    caught_prose = any(lbl == "head:Lancelot" and not po for lbl, lo, po, d in r6)

    # 7) PROSE drop: catalog no longer carries the 'Hjai' Nimue rawcode
    bad_cat = catalog.replace("'Hjai'", "Nimue-hero")
    r7 = all_rows(text, bad_cat)
    caught_prose2 = any(lbl == "rawcode:Nimue" and not po for lbl, lo, po, d in r7)

    print(f"  head live-drift caught         : {caught_head}")
    print(f"  enter-rect live-drift caught   : {caught_rect}")
    print(f"  rawcode live-drift caught      : {caught_raw}")
    print(f"  spawn-divergence drift caught  : {caught_div}")
    print(f"  gawain-extras drift caught     : {caught_gaw}")
    print(f"  head prose-drop caught         : {caught_prose}")
    print(f"  rawcode prose-drop caught      : {caught_prose2}")
    ok = all([base_ok, caught_head, caught_rect, caught_raw, caught_div,
              caught_gaw, caught_prose, caught_prose2])
    print(f"\nSELFTEST {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 3


def main():
    if "--selftest" in sys.argv:
        return selftest()
    if not EXTRACT.exists():
        print(f"FATAL: live extract not found: {EXTRACT}")
        return 2
    if not CATALOG.exists():
        print(f"FATAL: hero-select divergence catalog not found: {CATALOG}")
        return 2

    raw = EXTRACT.read_bytes()
    md5 = hashlib.md5(raw).hexdigest()
    print(f"live extract : {EXTRACT}")
    print(f"  md5={md5}  (catalog pins {CATALOG_CLAIMED_MD5})")
    if md5 != CATALOG_CLAIMED_MD5:
        print("RESULT: FAIL — live extract md5 DRIFTED from the catalog-pinned hash; "
              "every line/rawcode cite below is now suspect. Re-ground the catalog "
              "against the new bake.")
        return 1

    extract_text = raw.decode("latin-1")
    catalog_text = CATALOG.read_text()
    rows = all_rows(extract_text, catalog_text)
    report(rows)

    fail = [(lbl, d) for lbl, lo, po, d in rows if not (lo and po)]
    fwd_ok = sum(1 for _, lo, _, _ in rows if lo)
    rev_ok = sum(1 for _, _, po, _ in rows if po)
    print(f"\nanchors={len(rows)}  forward(live)={fwd_ok}/{len(rows)}  "
          f"reverse(prose)={rev_ok}/{len(rows)}  md5=OK")
    if fail:
        print("RESULT: FAIL — hero-select divergence-catalog live cites have drifted:")
        for lbl, d in fail:
            print(f"  - {lbl}: {d}")
        return 1
    print(f"RESULT: GREEN — all {len(rows)} live `war3map.j` cites in the hero-select "
          "DIVERGENCE_CATALOG hold vs the md5-pinned extract AND the catalog prose still "
          "carries every cite (10 Trig_<Hero>_Actions function heads L49272-L50763, 10 "
          "EnterRectSimple registrations + rect names L49315-L50801, 10 HeroTypeId "
          "rawcodes, the 1×AtLoc/9×FacingLocBJ spawn divergence @ Kay L49951, and the "
          "Gawain §5 ExtrasHook tokens). The hero-select divergence catalog is bound both ways.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
