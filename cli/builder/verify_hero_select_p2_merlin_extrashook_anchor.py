#!/usr/bin/env python3
r"""
verify_hero_select_p2_merlin_extrashook_anchor.py
================================================================================
KOTR Hero-Select REDESIGN (Track 4) · P2 **Merlin ExtrasHook cinematic tail**
<-> handler header authority <-> live extract binder.

WHY THIS GATE EXISTS (a real, uncovered seam on the STEP-2 apply path)
--------------------------------------------------------------------------------
`hero_select_p2_APPLY_RUNBOOK.md` STEP 2 tells the WE operator to *create the 2
ExtrasHook triggers* before deleting the 10 old `Trig_<Hero>_Actions` bodies. One
of the two is Merlin's intro cinematic, which STEP-2 describes coarsely:

    "**Merlin** -> the intro cinematic tail (3x `TriggerSleepAction` pacing the
     two extra camera pans + the floating \"Merlin thought\" text tag)"

and the handler header (`hero_select_p2_loop_handler.j`) describes precisely:

    "TriggerSleepAction x3 (3s/2s/3s) pacing two EXTRA camera pans
     (gg_rct_It_Begins, gg_rct_Merlin_Appear) + a floating \"Merlin thought\"
     text tag (CreateTextTagLocBJ -> DestroyTextTagBJ). The synchronous pick
     spine never sleeps, so this whole cinematic rides the ExtrasHook ... the
     body's ONE appear-pan stays the covered spine PanCamera."

That ExtrasHook is what the operator must hand-rebuild in STEP 2 (the data-uniform
`CastleSlot_ApplyPick(i)` spine deliberately does NOT collapse it). If the prose
ever drifts from the live Merlin body — a sleep count changed, an extra pan rect
renamed, the text tag dropped, or the spine appear-pan no longer first — the
operator would rebuild the wrong cinematic, OR (worse) move a spine op into the
async tail and desync the pick. Yet the GAWAIN ExtrasHook is the only one bound:

  * `verify_hero_select_divergence_catalog_anchors.py` binds Gawain's §5
    ExtrasHook tokens ('h012' / gg_unit_H014_0610 / gg_unit_Yuln_0448 /
    h__RemoveUnit) both ways — it never reads Merlin's cinematic structure.
  * `audit_hero_select_p2_equivalence.py` (fix_specs) proves each Merlin op is
    DEFERRED via the cinematic-tail rule, but it reads no runbook/handler PROSE,
    so it cannot catch a runbook or handler header that drifts from the body.
  * `verify_hero_select_p2_step2_heroref_anchor.py` binds the 6 deferred
    hero-ref globals — a different STEP-2 claim entirely.

So Merlin's "3x sleep / two extra pans / Merlin-thought tag / spine-pan-first"
structure is an unbound live-map claim. This binder closes that seam: runbook
prose <-> handler authority <-> live extract, the same both-ways contract as its
Track-4 siblings. (Runbook STEP-2 states only the COARSE shape — sleep count,
"two extra pans", the text tag — so the named-rect / duration anchors are bound
handler<->live only; those carry prose_required=False and report PROSE as 'n/a'.)

WHAT IT CHECKS (read-only; touches no .w3x and no shippable .j)
--------------------------------------------------------------------------------
  1. The live canonical extract still hashes to the md5 the runbook pins.
  2. The live Merlin body (function Trig_Merlin_Actions ... endfunction):
       - has exactly 3 TriggerSleepAction calls,
       - whose ordered durations are 3.00 / 2.00 / 3.00,
       - has exactly 2 camera pans AFTER the first sleep (the cinematic tail),
       - to gg_rct_It_Begins and gg_rct_Merlin_Appear,
       - a "Merlin thought" text tag (CreateTextTagLocBJ on gg_rct_Merlin_Thought
         + a DestroyTextTagBJ),
       - and the body's FIRST camera pan (the spine appear-pan) sits BEFORE the
         first TriggerSleepAction (i.e. the spine never sleeps).
  3. Each anchor agrees with the handler header, and the COARSE anchors agree
     with the runbook STEP-2 Merlin clause.

Exit 0 only if md5 matches AND every required direction holds for every anchor.

Run:        python3 verify_hero_select_p2_merlin_extrashook_anchor.py
Self-test:  python3 verify_hero_select_p2_merlin_extrashook_anchor.py --selftest

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
# the sibling Track-4 binders use, so a re-bake trips them all together.
RUNBOOK_CLAIMED_MD5 = "967131658fd8d4fb27ee0d7f74e4bd22"

MERLIN_FUNC = re.compile(
    r"function Trig_Merlin_Actions takes nothing returns nothing(.*?)\nendfunction",
    re.DOTALL,
)
SLEEP = re.compile(r"call TriggerSleepAction\(([\d.]+)\)")
# ordered camera-pan target rects in the Merlin body
PAN_RECT = re.compile(
    r"call PanCameraToTimedLocForPlayer\([^,]+,\s*GetRectCenter\((gg_rct_\w+)\)")


def merlin_body(extract_text):
    """The Trig_Merlin_Actions body text (between header and its endfunction), or
    None if the function is gone."""
    m = MERLIN_FUNC.search(extract_text)
    return m.group(1) if m else None


def live_facts(body):
    """Structural facts extracted from the live Merlin body. Returns a dict; every
    value is independently checkable so a single mutation trips exactly one anchor."""
    if body is None:
        return None
    sleeps = SLEEP.findall(body)                       # ['3.00','2.00','3.00']
    first_sleep_pos = None
    ms = SLEEP.search(body)
    if ms:
        first_sleep_pos = ms.start()
    # pans split by whether they precede the first sleep (spine) or follow it (tail)
    spine_pans, tail_pans = [], []
    for mp in PAN_RECT.finditer(body):
        (spine_pans if first_sleep_pos is not None and mp.start() < first_sleep_pos
         else tail_pans).append(mp.group(1))
    return {
        "sleeps": sleeps,
        "n_sleeps": len(sleeps),
        "tail_pans": tail_pans,
        "spine_pans": spine_pans,
        "has_thought_tag": bool(
            re.search(r"CreateTextTagLocBJ\([^\n]*gg_rct_Merlin_Thought", body))
            and "DestroyTextTagBJ" in body,
        "spine_pan_first": (first_sleep_pos is not None and len(spine_pans) >= 1),
    }


def runbook_merlin_clause(runbook_text):
    """The STEP-2 Merlin ExtrasHook clause, or '' if gone."""
    m = re.search(r"\*\*Merlin\*\*.*?text tag\)", runbook_text, re.DOTALL)
    return m.group(0) if m else ""


def all_rows(extract_text, runbook_text, handler_text):
    """Per-anchor rows: (label, live_ok, handler_ok, prose_ok, prose_required, detail)."""
    f = live_facts(merlin_body(extract_text))
    rb = runbook_merlin_clause(runbook_text)
    # normalize the handler COMMENT text: strip `//` line-markers + collapse
    # whitespace so wrapped claims ("two\n//   EXTRA camera pans") match contiguously.
    hd = re.sub(r"\s+", " ", re.sub(r"//+", " ", handler_text))
    rows = []

    def row(label, live_ok, handler_ok, prose_ok, prose_required, detail=""):
        rows.append((label, live_ok, handler_ok, prose_ok, prose_required, detail))

    if f is None:
        row("merlin-body:present", False, "function Trig_Merlin_Actions" in hd,
            "Merlin" in rb, True,
            "function Trig_Merlin_Actions ... endfunction not found in live extract")
        return rows

    # 1) exactly 3 TriggerSleepAction (COARSE — runbook states "3x", handler "x3")
    live_ok = f["n_sleeps"] == 3
    row("sleep:count=3", live_ok,
        ("TriggerSleepAction ×3" in hd) or ("TriggerSleepAction x3" in hd),
        bool(re.search(r"3×\s*`?TriggerSleepAction", rb)), True,
        "" if live_ok else f"live Merlin body has {f['n_sleeps']} TriggerSleepAction calls, not 3")

    # 2) the ordered durations are 3.00 / 2.00 / 3.00 (PRECISE — handler only)
    live_ok = f["sleeps"] == ["3.00", "2.00", "3.00"]
    row("sleep:durations=3/2/3", live_ok, "(3s/2s/3s)" in hd, False, False,
        "" if live_ok else f"live sleep durations {f['sleeps']} != ['3.00','2.00','3.00']")

    # 3) exactly two EXTRA (post-first-sleep) camera pans (COARSE — both prose)
    live_ok = len(f["tail_pans"]) == 2
    row("extra-pans:count=2", live_ok,
        "two EXTRA camera pans" in hd, "two extra camera pans" in rb, True,
        "" if live_ok else f"live tail (post-sleep) pans = {f['tail_pans']} (expected 2)")

    # 4/5) the two extra pans target gg_rct_It_Begins + gg_rct_Merlin_Appear (PRECISE — handler)
    for rect in ("gg_rct_It_Begins", "gg_rct_Merlin_Appear"):
        live_ok = rect in f["tail_pans"]
        row(f"extra-pan:{rect}", live_ok, rect in hd, False, False,
            "" if live_ok else f"{rect} not among live tail pans {f['tail_pans']}")

    # 6) the floating "Merlin thought" text tag (COARSE — both prose)
    row("text-tag:Merlin_Thought", f["has_thought_tag"],
        ("CreateTextTagLocBJ" in hd and "DestroyTextTagBJ" in hd
         and re.search(r'Merlin[\s/"]+thought', hd) is not None),
        ("Merlin thought" in rb and "text tag" in rb), True,
        "" if f["has_thought_tag"]
        else "live body missing CreateTextTagLocBJ(gg_rct_Merlin_Thought) + DestroyTextTagBJ")

    # 7) the spine appear-pan sits BEFORE the first sleep (PRECISE — handler)
    row("spine-pan:before-first-sleep", f["spine_pan_first"],
        "spine never sleeps" in hd or "ONE appear-pan stays the covered spine" in hd,
        False, False,
        "" if f["spine_pan_first"]
        else "no camera pan precedes the first TriggerSleepAction (spine pan not first)")
    return rows


def _passed(live_ok, handler_ok, prose_ok, prose_required):
    return bool(live_ok) and bool(handler_ok) and (bool(prose_ok) or not prose_required)


def report(rows):
    print(f"{'ANCHOR':<32}{'LIVE':<8}{'HANDLER':<10}{'PROSE':<8}")
    for label, live_ok, handler_ok, prose_ok, prose_required, detail in rows:
        prose_cell = ("OK" if prose_ok else "DRIFT") if prose_required else "n/a"
        print(f"{label:<32}{'OK' if live_ok else 'DRIFT':<8}"
              f"{'OK' if handler_ok else 'DRIFT':<10}"
              f"{prose_cell:<8}"
              + (f"  -> {detail}" if detail else ""))


def _synth_ok():
    """A synthetic (extract, runbook, handler) triple satisfying every anchor — the
    selftest baseline + the fixtures each RED-catch mutates."""
    body = (
        "function Trig_Merlin_Actions takes nothing returns nothing\n"
        "    call PanCameraToTimedLocForPlayer(P, GetRectCenter(gg_rct_Arthur_Kay_Lancelot_Appear), 0.00)\n"
        "    call TriggerSleepAction(3.00)\n"
        "    call PanCameraToTimedLocForPlayer(P, GetRectCenter(gg_rct_It_Begins), 0.00)\n"
        "    call TriggerSleepAction(2.00)\n"
        "    call PanCameraToTimedLocForPlayer(P, GetRectCenter(gg_rct_Merlin_Appear), 0.00)\n"
        "    call CreateTextTagLocBJ(\"TRIGSTR_410\", GetRectCenter(gg_rct_Merlin_Thought), 0.00, 10.00, 100, 100, 100, 0)\n"
        "    call TriggerSleepAction(3.00)\n"
        "    call DestroyTextTagBJ(GetLastCreatedTextTag())\n"
        "endfunction\n"
    )
    handler = (
        "//  MERLIN — TriggerSleepAction ×3 (3s/2s/3s) pacing two EXTRA camera pans "
        "(gg_rct_It_Begins, gg_rct_Merlin_Appear) + a floating \"Merlin thought\" text tag "
        "(CreateTextTagLocBJ -> DestroyTextTagBJ). The synchronous pick spine never sleeps; "
        "the body's ONE appear-pan stays the covered spine PanCamera.\n"
    )
    runbook = (
        "STEP 2 ... **Merlin** -> the intro cinematic tail (3× `TriggerSleepAction` "
        "pacing the two extra camera pans + the floating \"Merlin thought\" text tag)\n"
    )
    return body, runbook, handler


def selftest():
    print("=== SELFTEST: parser unit-tests + per-direction RED-catch (teeth) ===")
    body, runbook, handler = _synth_ok()

    # parser sanity
    f = live_facts(merlin_body(body))
    assert f is not None and f["sleeps"] == ["3.00", "2.00", "3.00"], f
    assert f["tail_pans"] == ["gg_rct_It_Begins", "gg_rct_Merlin_Appear"], f["tail_pans"]
    assert f["spine_pans"] == ["gg_rct_Arthur_Kay_Lancelot_Appear"], f["spine_pans"]
    assert f["has_thought_tag"] and f["spine_pan_first"], f

    base = all_rows(body, runbook, handler)
    base_ok = all(_passed(l, h, p, pr) for _, l, h, p, pr, _ in base)
    print(f"  baseline all-green             : {base_ok}")
    assert base_ok, [r for r in base if not _passed(r[1], r[2], r[3], r[4])]

    def caught(rows, label):
        for lbl, l, h, p, pr, d in rows:
            if lbl == label:
                return not _passed(l, h, p, pr)
        return False

    # 1) LIVE: a sleep is dropped -> count != 3
    bad = body.replace("    call TriggerSleepAction(2.00)\n", "")
    c_count = caught(all_rows(bad, runbook, handler), "sleep:count=3")

    # 2) LIVE: a sleep duration is retimed -> durations drift
    bad = body.replace("TriggerSleepAction(2.00)", "TriggerSleepAction(9.00)")
    c_dur = caught(all_rows(bad, runbook, handler), "sleep:durations=3/2/3")

    # 3) LIVE: an extra pan rect renamed -> named-pan anchor + count both unaffected? count stays 2
    bad = body.replace("gg_rct_It_Begins", "gg_rct_RENAMED")
    rows3 = all_rows(bad, runbook, handler)
    c_pan = caught(rows3, "extra-pan:gg_rct_It_Begins")

    # 4) LIVE: an extra pan moved before the first sleep -> tail count drops to 1
    bad = body.replace(
        "    call TriggerSleepAction(3.00)\n"
        "    call PanCameraToTimedLocForPlayer(P, GetRectCenter(gg_rct_It_Begins), 0.00)\n",
        "    call PanCameraToTimedLocForPlayer(P, GetRectCenter(gg_rct_It_Begins), 0.00)\n"
        "    call TriggerSleepAction(3.00)\n")
    c_paircount = caught(all_rows(bad, runbook, handler), "extra-pans:count=2")

    # 5) LIVE: text tag removed
    bad = body.replace(
        "    call CreateTextTagLocBJ(\"TRIGSTR_410\", GetRectCenter(gg_rct_Merlin_Thought), 0.00, 10.00, 100, 100, 100, 0)\n", "")
    c_tag = caught(all_rows(bad, runbook, handler), "text-tag:Merlin_Thought")

    # 6) LIVE: spine pan removed -> spine-pan-first fails
    bad = body.replace(
        "    call PanCameraToTimedLocForPlayer(P, GetRectCenter(gg_rct_Arthur_Kay_Lancelot_Appear), 0.00)\n", "")
    c_spine = caught(all_rows(bad, runbook, handler), "spine-pan:before-first-sleep")

    # 7) HANDLER drift: header drops the "x3" claim
    bad_h = handler.replace("TriggerSleepAction ×3", "TriggerSleepAction times-three")
    c_hdr = caught(all_rows(body, runbook, bad_h), "sleep:count=3")

    # 8) PROSE drift: runbook drops the text-tag claim (a required prose anchor)
    bad_rb = runbook.replace("+ the floating \"Merlin thought\" text tag", "")
    c_prose = caught(all_rows(body, bad_rb, handler), "text-tag:Merlin_Thought")

    # 9) BODY gone entirely
    c_gone = caught(all_rows("nothing here", runbook, handler), "merlin-body:present")

    for name, val in [
        ("live sleep-count drift", c_count), ("live duration drift", c_dur),
        ("live pan-rename drift", c_pan), ("live tail-pan-count drift", c_paircount),
        ("live text-tag drop", c_tag), ("live spine-pan drop", c_spine),
        ("handler x3 drift", c_hdr), ("prose text-tag drop", c_prose),
        ("merlin body gone", c_gone),
    ]:
        print(f"  {name:<26}caught : {val}")
    ok = base_ok and all([c_count, c_dur, c_pan, c_paircount, c_tag, c_spine,
                          c_hdr, c_prose, c_gone])
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
              "Merlin's ExtrasHook cinematic cites are now suspect. Re-ground vs the new bake.")
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
        print("RESULT: FAIL — hero-select P2 Merlin ExtrasHook cinematic tail drifted:")
        for lbl, d in fail:
            print(f"  - {lbl}: {d}")
        return 1
    print("RESULT: GREEN — Merlin's STEP-2 ExtrasHook cinematic tail is bound vs the "
          "md5-pinned extract: the live Trig_Merlin_Actions body has exactly 3 "
          "TriggerSleepAction calls (3.00/2.00/3.00) pacing two EXTRA camera pans "
          "(gg_rct_It_Begins, gg_rct_Merlin_Appear) + the 'Merlin thought' text tag, with "
          "the spine appear-pan BEFORE the first sleep — and that structure matches the "
          "handler header AND the runbook STEP-2 Merlin clause. The operator's hand-rebuilt "
          "Merlin cinematic cannot silently drift from the body it replaces.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
