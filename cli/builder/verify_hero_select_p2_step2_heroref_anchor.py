#!/usr/bin/env python3
r"""
verify_hero_select_p2_step2_heroref_anchor.py
================================================================================
KOTR Hero-Select REDESIGN (Track 4) · P2 APPLY-RUNBOOK **STEP-2 deferred
hero-ref enumeration** <-> handler HEROREF authority <-> live extract binder.

WHY THIS GATE EXISTS (a real, uncovered seam on the STEP-2 apply path)
--------------------------------------------------------------------------------
`hero_select_p2_APPLY_RUNBOOK.md` STEP 2 tells the WE operator which per-hero
state the data-uniform `CastleSlot_ApplyPick(i)` spine does NOT collapse and
leaves DEFERRED-by-design. Chief among them is an explicit, named list:

    "the **6 distinct hero-ref globals** (`udg_Arthur`, `udg_guinevere`,
     `udg_PercivalPellinore`, `udg_GalahadGrail`, `udg_SirYvaine`,
     `udg_SirGawain` — enumerated in the handler `HEROREF:` markers)
     ... are **DEFERRED by design**"

That sentence makes THREE checkable claims the operator relies on before deleting
the 10 old `Trig_<Hero>_Actions` triggers:
  1. there are exactly **6** distinct hero-ref globals,
  2. they are *these* 6 names, and
  3. they are the SAME set the handler header enumerates as `HEROREF: udg_<X>`.

If the runbook's list and the handler's `HEROREF:` markers ever diverge — a hero
added/renamed in one but not the other — the operator could delete an old pick
trigger that still owns the only `set udg_<HeroRef> = GetLastCreatedUnit()` for a
hero the new spine never latches, silently orphaning a map-wide hero reference.
Yet NO existing gate binds the runbook's STEP-2 enumeration:

  * `audit_hero_select_p2_equivalence.py` (fix_specs) binds the handler
    `HEROREF:` markers <-> the live pick bodies that latch each ref — it never
    reads the runbook .md, so it cannot catch a runbook list that drifts from the
    handler it cites.
  * `verify_hero_select_p2_runbook_anchors.py` binds the runbook's reuse-global
    occurrence COUNTS + the 10-pick-body line range + the tail rawcodes — NOT
    this STEP-2 deferred-hero-ref list.
  * `verify_hero_select_p2_loop.py` / `verify_castleslot_global_contract.py`
    cover the loop compile + the STEP-0 `CastleSlot_*` contract — a different set
    of globals entirely.

So the STEP-2 "6 distinct hero-ref globals" sentence is an unbound live-map claim.
This binder closes that seam: runbook prose <-> handler authority <-> live extract,
all three directions, exactly the both-ways contract of its Track-4 siblings.

WHAT IT CHECKS (read-only; touches no .w3x and no shippable .j)
--------------------------------------------------------------------------------
  1. The live canonical extract still hashes to the md5 the runbook pins (a
     re-bake is caught before any per-name check can false-pass).
  2. ENUMERATION agreement (both ways):
       - the runbook STEP-2 prose lists exactly N names AND states the count "N",
       - the handler header enumerates exactly the same N `HEROREF: udg_<X>`,
       - runbook set == handler set (no name on one side only).
  3. LIVE presence: each named hero-ref global occurs whole-word >=1 in the live
     extract (a name deferred but absent live is a stale citation).

Exit 0 only if md5 matches AND every name holds in all three directions AND the
two sets are identical AND the stated count matches.

Run:        python3 verify_hero_select_p2_step2_heroref_anchor.py
Self-test:  python3 verify_hero_select_p2_step2_heroref_anchor.py --selftest

Registered in verify_builder_gates.py (the cli/builder aggregate sweep). Sibling
of the other Track-4 binders; same EXTRACT / md5 / both-ways-binding contract.
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
# the sibling runbook-anchors binder uses, so a re-bake trips both.
RUNBOOK_CLAIMED_MD5 = "967131658fd8d4fb27ee0d7f74e4bd22"

HEROREF_MARKER = re.compile(r"HEROREF:\s*(udg_\w+)")


def whole_word_count(text, token):
    return len(re.findall(r"(?<!\w)" + re.escape(token) + r"(?!\w)", text))


def handler_hero_refs(handler_text):
    """The ordered list of hero-ref globals the handler header enumerates as
    `HEROREF: udg_<X>` markers (the deferred-by-design per-hero references)."""
    return HEROREF_MARKER.findall(handler_text)


def runbook_step2(runbook_text):
    """Extract (stated_count, [names]) from the STEP-2 '6 distinct hero-ref
    globals (...)' sentence. Returns (None, []) if the sentence is gone."""
    m = re.search(
        r"(\d+)\s+distinct hero-ref globals\*\*\s*\((.*?)enumerated in the handler",
        runbook_text,
        re.DOTALL,
    )
    if not m:
        return None, []
    stated = int(m.group(1))
    names = re.findall(r"udg_\w+", m.group(2))
    return stated, names


def all_rows(extract_text, runbook_text, handler_text):
    """Per-name rows (label, live_ok, handler_ok, prose_ok, detail) +
    aggregate set/count rows appended at the end."""
    stated, rb_names = runbook_step2(runbook_text)
    hd_names = handler_hero_refs(handler_text)
    rb_set, hd_set = set(rb_names), set(hd_names)
    universe = sorted(rb_set | hd_set)

    rows = []
    for name in universe:
        live = whole_word_count(extract_text, name)
        live_ok = live >= 1
        handler_ok = name in hd_set
        prose_ok = name in rb_set
        detail = ""
        if not live_ok:
            detail = f"hero-ref {name!r} absent from live extract (whole-word count 0)"
        elif not handler_ok:
            detail = f"{name!r} in runbook STEP-2 but NOT a handler HEROREF: marker"
        elif not prose_ok:
            detail = f"{name!r} a handler HEROREF: marker but NOT in runbook STEP-2 list"
        rows.append(("ref:" + name, live_ok, handler_ok, prose_ok, detail))

    # aggregate: stated count matches the actual list length (both sources)
    count_live_ok = stated is not None and stated == len(hd_names)
    count_prose_ok = stated is not None and stated == len(rb_names)
    cdetail = ""
    if stated is None:
        cdetail = "runbook STEP-2 '<N> distinct hero-ref globals' sentence not found"
    elif not count_live_ok:
        cdetail = f"runbook states {stated} but handler has {len(hd_names)} HEROREF markers"
    elif not count_prose_ok:
        cdetail = f"runbook states {stated} but only lists {len(rb_names)} names"
    rows.append(("count:6-distinct", count_live_ok, count_live_ok, count_prose_ok, cdetail))

    # aggregate: the two SETS are identical (no name on one side only)
    set_ok = bool(rb_set) and rb_set == hd_set
    sdetail = ""
    if not set_ok:
        only_rb = sorted(rb_set - hd_set)
        only_hd = sorted(hd_set - rb_set)
        bits = []
        if only_rb:
            bits.append(f"runbook-only: {only_rb}")
        if only_hd:
            bits.append(f"handler-only: {only_hd}")
        if not rb_set:
            bits.append("runbook enumeration empty")
        sdetail = "; ".join(bits) or "sets differ"
    rows.append(("set:runbook==handler", set_ok, set_ok, set_ok, sdetail))
    return rows


def report(rows):
    print(f"{'ANCHOR':<30}{'LIVE':<8}{'HANDLER':<10}{'PROSE':<8}")
    for label, live_ok, handler_ok, prose_ok, detail in rows:
        print(f"{label:<30}{'OK' if live_ok else 'DRIFT':<8}"
              f"{'OK' if handler_ok else 'DRIFT':<10}"
              f"{'OK' if prose_ok else 'DRIFT':<8}"
              + (f"  -> {detail}" if detail else ""))


def _synth_ok():
    """Build a synthetic (extract, runbook, handler) triple that satisfies every
    anchor — the selftest baseline + the fixtures each RED-catch mutates."""
    names = ["udg_Arthur", "udg_guinevere", "udg_PercivalPellinore",
             "udg_GalahadGrail", "udg_SirYvaine", "udg_SirGawain"]
    extract = " ".join(names)  # each present whole-word once
    handler = "header\n" + "\n".join(f"//   HEROREF: {n}   (x)" for n in names)
    runbook = ("blah **6 distinct hero-ref globals** (`" + "`, `".join(names)
               + "` — enumerated in the handler `HEROREF:` markers) DEFERRED")
    return extract, runbook, handler, names


def selftest():
    print("=== SELFTEST: parser unit-tests + per-direction RED-catch (teeth) ===")
    extract, runbook, handler, names = _synth_ok()

    # parser sanity
    assert handler_hero_refs(handler) == names, handler_hero_refs(handler)
    stated, rb_names = runbook_step2(runbook)
    assert stated == 6 and rb_names == names, (stated, rb_names)

    base = all_rows(extract, runbook, handler)
    base_ok = all(l and h and p for _, l, h, p, _ in base)
    print(f"  baseline all-green             : {base_ok}")
    assert base_ok, [r for r in base if not (r[1] and r[2] and r[3])]

    # 1) LIVE drift: a deferred name vanishes from the extract
    bad1 = extract.replace("udg_SirGawain", "udg_NOPE")
    r1 = all_rows(bad1, runbook, handler)
    caught_live = any(lbl == "ref:udg_SirGawain" and not l for lbl, l, h, p, d in r1)

    # 2) HANDLER drop: runbook lists a name the handler no longer marks
    bad_handler = handler.replace("HEROREF: udg_SirYvaine", "noop udg_SirYvaine")
    r2 = all_rows(extract, runbook, bad_handler)
    caught_handler = any(lbl == "ref:udg_SirYvaine" and not h for lbl, l, h, p, d in r2)
    caught_set2 = any(lbl == "set:runbook==handler" and not l for lbl, l, h, p, d in r2)

    # 3) PROSE drop: handler marks a name the runbook list dropped
    bad_runbook = runbook.replace("`udg_GalahadGrail`, ", "")
    r3 = all_rows(extract, bad_runbook, handler)
    caught_prose = any(lbl == "ref:udg_GalahadGrail" and not p for lbl, l, h, p, d in r3)

    # 4) COUNT drift: runbook says 6 but only 5 are actually marked/listed
    five_handler = handler.replace("\n//   HEROREF: udg_SirGawain   (x)", "")
    five_runbook = runbook.replace("`udg_SirGawain` — ", "— ")
    r4 = all_rows(extract, five_runbook, five_handler)
    caught_count = any(lbl == "count:6-distinct" and not l for lbl, l, h, p, d in r4)

    # 5) SET mismatch with EQUAL sizes (a rename on one side only)
    ren_handler = handler.replace("HEROREF: udg_Arthur", "HEROREF: udg_KingArthur")
    r5 = all_rows(extract + " udg_KingArthur", runbook, ren_handler)
    caught_set = any(lbl == "set:runbook==handler" and not l for lbl, l, h, p, d in r5)

    print(f"  live-drift caught              : {caught_live}")
    print(f"  handler-drop caught           : {caught_handler}")
    print(f"  set-mismatch(via drop) caught : {caught_set2}")
    print(f"  prose-drop caught             : {caught_prose}")
    print(f"  count-drift caught            : {caught_count}")
    print(f"  set-mismatch(rename) caught   : {caught_set}")
    ok = all([base_ok, caught_live, caught_handler, caught_set2,
              caught_prose, caught_count, caught_set])
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
              "the STEP-2 deferred-hero-ref cites are now suspect. Re-ground vs the new bake.")
        return 1

    extract_text = raw.decode("latin-1")
    runbook_text = RUNBOOK.read_text()
    handler_text = HANDLER.read_text()
    rows = all_rows(extract_text, runbook_text, handler_text)
    report(rows)

    fail = [(lbl, d) for lbl, l, h, p, d in rows if not (l and h and p)]
    live_ok = sum(1 for _, l, _, _, _ in rows if l)
    hand_ok = sum(1 for _, _, h, _, _ in rows if h)
    prose_ok = sum(1 for _, _, _, p, _ in rows if p)
    print(f"\nanchors={len(rows)}  live={live_ok}/{len(rows)}  "
          f"handler={hand_ok}/{len(rows)}  prose={prose_ok}/{len(rows)}  md5=OK")
    if fail:
        print("RESULT: FAIL — hero-select P2 STEP-2 deferred-hero-ref enumeration drifted:")
        for lbl, d in fail:
            print(f"  - {lbl}: {d}")
        return 1
    print(f"RESULT: GREEN — STEP-2's '6 distinct hero-ref globals' enumeration in "
          "hero_select_p2_APPLY_RUNBOOK.md is bound three ways vs the md5-pinned extract: "
          "the runbook list == the handler HEROREF: markers (set + stated count 6), and "
          "every named hero-ref (udg_Arthur / udg_guinevere / udg_PercivalPellinore / "
          "udg_GalahadGrail / udg_SirYvaine / udg_SirGawain) is present in the live "
          "war3map.j. The deferred-by-design list cannot silently drift from the handler "
          "it cites before the operator deletes the 10 old pick triggers.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
