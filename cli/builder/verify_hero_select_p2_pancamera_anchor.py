#!/usr/bin/env python3
r"""
verify_hero_select_p2_pancamera_anchor.py
================================================================================
KOTR Hero-Select REDESIGN (Track 4) · P2 **per-pick CAMERA-PAN / appear-pan op**
<-> handler authority <-> live extract binder.
Built 2026-06-19 by KOTR Builder (engine claude-p).

WHY THIS GATE EXISTS (a real, uncovered seam on the P2 apply path)
--------------------------------------------------------------------------------
Every one of the 10 hand-written `Trig_<Hero>_Actions` pick bodies pans the picker's
camera to that hero's appear rect at one fixed position on the apply spine (after the
loadout/ally/avail/rescue/invuln transfers, before the name-guard tail):

    call PanCameraToTimedLocForPlayer(GetOwningPlayer(GetTriggerUnit()),
                                      GetRectCenter(gg_rct_<Hero>_Appear), 0.00)

The handler collapses all 10 of those into ONE spine line, turning the lone per-slot
datum (the appear rect's center) into the pre-materialized location
`udg_CastleSlot_CamLoc[i]`:

    call PanCameraToTimedLocForPlayer(picker, udg_CastleSlot_CamLoc[i], 0.00)

This op has TWO traps that make it WORTH a dedicated binder — and that already bit
once (the recon noted a dropped per-slot camera-pan REGRESSION caught + fixed):

  TRAP 1 — the CINEMATIC BOUNDARY (Merlin). Merlin's body carries THREE
  PanCameraToTimedLocForPlayer calls, not one: the covered appear-pan (the FIRST,
  to gg_rct_Arthur_Kay_Lancelot_Appear, BEFORE any sleep), PLUS two EXTRA cinematic
  pans (gg_rct_It_Begins, gg_rct_Merlin_Appear) interleaved with `TriggerSleepAction`
  beats. Those two are async cinematic — the synchronous pick spine never sleeps — so
  they ride the per-slot ExtrasHook cinematic tail, NOT the data-uniform spine. A naive
  per-body pan count would see Merlin=3 and either reject the uniform-1 claim or, worse,
  fold the two cinematic pans into CamLoc and pan every picker through Merlin's intro.
  The covered appear-pan is precisely the pan(s) BEFORE the body's FIRST
  `TriggerSleepAction` (all 9 regular bodies have no sleep, so their single pan is
  covered; Merlin has exactly 1 pan pre-sleep + 2 post-sleep).

  TRAP 2 — the rect is per-slot data but NOT distinct. SIX slots share
  gg_rct_Arthur_Kay_Lancelot_Appear (Arthur, Kay, Lancelot, Yvain, Gawain, and Merlin's
  covered pan); only Guinevere/Nimue/Percival/Galahad have their own. So — unlike the
  SetPlayerName TRIGSTR or the announce TRIGSTR — the per-slot datum here is NOT all-
  distinct; it is a fixed MULTISET. A binder that demanded distinctness (copy-pasted from
  a sibling) would false-RED; one that ignored the rect entirely would miss a mis-bind.

The handler makes several checkable claims the WE operator relies on before deleting the
10 old bodies:
  1. EVERY pick body carries exactly 1 COVERED appear-pan (pre-sleep) — 10 total,
  2. the covered pan is the arg-UNIFORM PanCameraToTimedLocForPlayer(GetOwningPlayer(
     GetTriggerUnit()), GetRectCenter(<rect>), 0.00) — only the rect is per-slot data,
  3. each covered pan's rect is a gg_rct_*_Appear rect, and the 10 form the exact
     expected multiset (Arthur_Kay_Lancelot shared ×6 + 4 distinct),
  4. Merlin's 2 EXTRA pans are POST-sleep (cinematic, deferred to ExtrasHook) and the
     other 9 bodies have ZERO post-sleep pans — the cinematic-boundary faithfulness.
If any drift, the operator could drop a slot's pan (silent — a null CamLoc compiles and
just pans to (0,0)), mis-bind the rect, or fold Merlin's cinematic pans into the spine —
and no other gate would catch it:
  * `verify_hero_select_p2_generated_j.py` / `verify_hero_select_p2_datatable.py` bind
    the MATERIALIZED CamLoc column vs the catalog JSON — they prove the BAKED column is
    internally consistent, NOT that it matches the live bodies' pan op nor the handler's
    cinematic-boundary claim.
  * `verify_hero_select_p2_setplayername_anchor.py` / `_announce_anchor.py` /
    `_spawnability_anchor.py` / `_item_loadout_anchor.py` / `_avail_anchor.py` /
    `_allyrescueinvuln_anchor.py` bind the OTHER spine op families (a DIFFERENT op at a
    different position); none reads the camera pan nor the TriggerSleepAction boundary.
  * `verify_hero_select_p2_merlin_extrashook_anchor.py` binds Merlin's cinematic CLUSTER
    as a deferred ExtrasHook unit — it proves the 2 extra pans LIVE in the cinematic tail,
    not that the body's ONE pre-sleep pan is the covered spine op the handler reproduces.
  * `verify_hero_select_p2_loop.py` / `audit_hero_select_p2_equivalence.py` compile +
    op-equivalence-prove the handler; they never read the runbook .md.

So this gate closes the seam the established Track-4 way: it binds the runbook CamLoc
claim <-> handler header + spine authority <-> live extract pan op, both ways, against
the md5-pinned canonical extract — the DENSE-UNIFORM, per-PLAYER (camera is the only
desync-relevant op, hence the desync-safe pick path), CINEMATIC-BOUNDARY-SCOPED sibling
of the announce/name/item/ally/avail/rescue/invuln/spawn-ability binders. CRUCIAL TEETH:
the live extract has 25 PanCameraToTimedLocForPlayer calls total, only 12 in the 10 pick
bodies (10 covered + Merlin's 2 cinematic). A flat grep would inflate the family ~2x.
This gate BODY-SCOPES to the 10 pick bodies AND cinematic-scopes to the pre-sleep region
so only the real covered appear-pan counts.

WHAT IT CHECKS (read-only; touches no .w3x and no shippable .j)
--------------------------------------------------------------------------------
  0. md5 pin: the live extract still hashes to the runbook-pinned md5 (a re-bake trips it).
  1. all 10 hand-written hero pick bodies are present in the live extract.
  2. every-slot: ALL 10 pick bodies carry exactly 1 COVERED (pre-sleep) appear-pan
     (live, body+cinematic-scoped) <-> handler "per-pick camera pan" <-> runbook
     "pans the picker's camera to the appear rect".
  3. total: covered appear-pan count == 10 (live) <-> handler "call
     PanCameraToTimedLocForPlayer(picker, udg_CastleSlot_CamLoc[i], 0.00)" <-> runbook
     `CastleSlot_CamLoc`.
  4. uniform-form: every covered pan == PanCameraToTimedLocForPlayer(GetOwningPlayer(
     GetTriggerUnit()), GetRectCenter(<rect>), 0.00) (only the rect per-hero) (live) <->
     handler "PanCameraToTimedLocForPlayer(picker, GetRectCenter(<appear rect>), 0.00)".
  5. appear-rect multiset: each covered pan's rect is a gg_rct_*_Appear rect, and the 10
     form the exact expected multiset (Arthur_Kay_Lancelot ×6 + 4 distinct) (live) <->
     handler "udg_CastleSlot_CamLoc[i]" <-> runbook "per-slot camera target =
     `GetRectCenter(<Appear rect>)`".
  6. cinematic-deferred: Merlin carries exactly 2 POST-sleep pans (cinematic, deferred to
     the ExtrasHook) and the other 9 bodies have ZERO post-sleep pans (live) <-> handler
     "Merlin's two EXTRA cinematic pans (TriggerSleepAction-gated) are NOT this op" + "they
     ride the per-slot ExtrasHook cinematic tail" <-> runbook ExtrasHook cinematic claim.

Run:        python3 verify_hero_select_p2_pancamera_anchor.py
Self-test:  python3 verify_hero_select_p2_pancamera_anchor.py --selftest
            (parser unit-tests + a per-direction RED-catch so the gate has teeth,
             incl. body-scoped + cinematic-scoped exclusion of out-of-body / post-sleep
             pans and a folded-cinematic-pan RED-catch)
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

# DENSE-UNIFORM: every one of the 10 slots pans exactly once (the COVERED appear-pan).
EXPECTED_OCCUPANTS = {h for _, h in HERO_FUNCS}            # all 10
EXPECTED_TOTAL = len(HERO_FUNCS)                           # 10

# the per-slot covered appear rect (the lone per-hero datum). NOT all-distinct: SIX slots
# share gg_rct_Arthur_Kay_Lancelot_Appear (the central castle pan), only 4 are unique.
EXPECTED_RECT = {
    "Arthur": "gg_rct_Arthur_Kay_Lancelot_Appear",
    "Guinevere": "gg_rct_Guinevere_Appear",
    "Nimue": "gg_rct_Nimue_Appear",
    "Merlin": "gg_rct_Arthur_Kay_Lancelot_Appear",     # Merlin's COVERED pan (pre-sleep)
    "Kay": "gg_rct_Arthur_Kay_Lancelot_Appear",
    "Percival": "gg_rct_Percival_Appear",
    "Galahad": "gg_rct_Galahad_Appear",
    "Lancelot": "gg_rct_Arthur_Kay_Lancelot_Appear",
    "Yvain": "gg_rct_Arthur_Kay_Lancelot_Appear",
    "Gawain": "gg_rct_Arthur_Kay_Lancelot_Appear",
}
# Merlin is the ONLY slot with cinematic (post-sleep) extra pans; all others have zero.
EXPECTED_CINEMATIC_PANS = {"Merlin": 2}

# the exact, arg-uniform pan signature the live pick bodies use
# (canonicalized: the appear rect -> gg_rct_<...>).
PAN_SIG = ("call PanCameraToTimedLocForPlayer(GetOwningPlayer(GetTriggerUnit()), "
           "GetRectCenter(<rect>), 0.00)")

# the handler spine line (post // strip + whitespace collapse). The pan collapses the 10
# per-slot appear-pans; the per-hero rect-center generalizes to udg_CastleSlot_CamLoc[i].
PAN_SPINE = "call PanCameraToTimedLocForPlayer(picker, udg_CastleSlot_CamLoc[i], 0.00)"

# any covered-form PanCameraToTimedLocForPlayer(GetOwningPlayer(GetTriggerUnit()),
# GetRectCenter(gg_rct_...), 0.00). The player-expr is captured (NOT pre-filtered) so a
# non-uniform player arg is visible; the rect name is captured as the per-slot datum.
_PAN_RE = re.compile(
    r'call PanCameraToTimedLocForPlayer\((.*?),\s*GetRectCenter\((gg_rct_\w+)\),\s*0\.00\)')


def body_of(extract_text, func):
    """The body text of one function, or None if gone. Anchored on the exact
    `function <name> takes nothing returns ...` ... `endfunction` span so the 13 out-of-body
    PanCameraToTimedLocForPlayer calls can never leak in."""
    m = re.search(
        r"function " + re.escape(func) + r" takes nothing returns \w+(.*?)\nendfunction",
        extract_text, re.DOTALL)
    return m.group(1) if m else None


def _split_cinematic(body):
    """Split a body at its FIRST TriggerSleepAction: (pre_sleep, post_sleep). The covered
    synchronous pick spine never sleeps, so the covered appear-pan(s) live in pre_sleep and
    any cinematic (async) pans live in post_sleep. Bodies with no sleep -> (whole, '')."""
    i = body.find("call TriggerSleepAction")
    if i < 0:
        return body, ""
    return body[:i], body[i:]


def _covered_pans(body):
    """The canonicalized covered (pre-sleep) pan one-liners + their rect names, in order."""
    pre, _ = _split_cinematic(body)
    out = []
    for m in _PAN_RE.finditer(pre):
        canon = re.sub(r"GetRectCenter\(gg_rct_\w+\)", "GetRectCenter(<rect>)",
                       m.group(0).strip())
        out.append((canon, m.group(2)))
    return out


def _cinematic_pan_count(body):
    """How many PanCameraToTimedLocForPlayer calls live AFTER the first TriggerSleepAction
    (the async cinematic pans, deferred to the ExtrasHook — NOT the covered spine op)."""
    _, post = _split_cinematic(body)
    return len(_PAN_RE.findall(post))


def live_facts(extract_text):
    """Per-body covered-pan facts, BODY-SCOPED to the 10 pick bodies AND cinematic-scoped to
    the pre-sleep region. Every value independently checkable so a single mutation trips
    exactly one anchor."""
    count = {}         # hero -> # covered (pre-sleep) pans
    pan = {}           # hero -> canonicalized covered pan one-liner (first)
    rect = {}          # hero -> covered appear-rect name (first)
    cinematic = {}     # hero -> # post-sleep cinematic pans (deferred)
    missing = []
    for func, hero in HERO_FUNCS:
        b = body_of(extract_text, func)
        if b is None:
            missing.append(hero)
            continue
        cps = _covered_pans(b)
        count[hero] = len(cps)
        pan[hero] = cps[0][0] if cps else None
        rect[hero] = cps[0][1] if cps else None
        cinematic[hero] = _cinematic_pan_count(b)
    return {
        "n_found": len(count),
        "missing": missing,
        "count": count,
        "pan": pan,
        "rect": rect,
        "cinematic": cinematic,
    }


def _occupants(d):
    """heroes whose covered-pan count is >= 1."""
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

    # 2) every-slot: ALL 10 carry exactly 1 COVERED (pre-sleep) appear-pan (dense-uniform)
    occ = _occupants(f["count"])
    one_each = all(v == 1 for v in f["count"].values()) and len(f["count"]) == 10
    live_ok = occ == EXPECTED_OCCUPANTS and one_each
    row("cam:every-slot=1", live_ok,
        "per-pick camera pan" in hd,
        "pans the picker's camera to the appear rect" in rbf, True,
        "" if live_ok else f"covered-pan occupants={sorted(occ)} counts={f['count']}")

    # 3) total: covered appear-pan count == 10
    total = sum(f["count"].values())
    live_ok = total == EXPECTED_TOTAL
    row("cam:total=10", live_ok,
        PAN_SPINE in hd,
        "`CastleSlot_CamLoc`" in rbf, True,
        "" if live_ok else f"live covered-pan total={total} (expected {EXPECTED_TOTAL})")

    # 4) uniform-form: every covered pan uses the SAME arg form GetOwningPlayer(
    #    GetTriggerUnit()) + GetRectCenter(<rect>) + 0.00 — only the rect per-hero (real
    #    teeth: a pan with a different player/duration is captured here and trips).
    pans = [p for p in f["pan"].values() if p is not None]
    live_ok = len(pans) == 10 and all(p == PAN_SIG for p in pans)
    row("cam:uniform-form", live_ok,
        "PanCameraToTimedLocForPlayer(picker, GetRectCenter(<appear rect>), 0.00)" in hd,
        "pans the picker's camera to the appear rect" in rbf, True,
        "" if live_ok else f"a live covered pan is not the uniform {PAN_SIG!r}: "
        f"{ {h: p for h, p in f['pan'].items() if p != PAN_SIG} }")

    # 5) appear-rect multiset: each covered pan's rect is a gg_rct_*_Appear rect AND the 10
    #    form the exact expected MULTISET (Arthur_Kay_Lancelot ×6 + 4 distinct). NOT a
    #    distinct check — six slots legitimately share the central castle pan.
    rects = f["rect"]
    all_appear = (len(rects) == 10
                  and all(r is not None and r.endswith("_Appear") for r in rects.values()))
    matches_multiset = rects == EXPECTED_RECT
    live_ok = all_appear and matches_multiset
    row("cam:appear-rect-multiset", live_ok,
        "udg_CastleSlot_CamLoc[i]" in hd,
        "per-slot camera target = `GetRectCenter(<Appear rect>)`" in rbf, True,
        "" if live_ok else f"appear-rect multiset drift: "
        f"{ {h: r for h, r in rects.items() if r != EXPECTED_RECT.get(h)} }")

    # 6) cinematic-deferred: Merlin has exactly 2 POST-sleep cinematic pans, the other 9
    #    have ZERO — the TriggerSleepAction boundary that keeps the cinematic OFF the spine.
    cine = f["cinematic"]
    expected_cine = {h: EXPECTED_CINEMATIC_PANS.get(h, 0) for _, h in HERO_FUNCS}
    live_ok = len(cine) == 10 and cine == expected_cine
    row("cam:cinematic-deferred", live_ok,
        ("Merlin's two EXTRA cinematic pans (TriggerSleepAction-gated) are NOT this op" in hd
         and "they ride the per-slot ExtrasHook cinematic tail" in hd),
        "intro CINEMATIC tail" in rbf or "intro cinematic" in rbf, True,
        "" if live_ok else f"post-sleep cinematic-pan distribution drift: "
        f"{ {h: c for h, c in cine.items() if c != expected_cine.get(h)} }")
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
    selftest baseline + the fixtures each RED-catch mutates. Encodes the real dense-uniform
    covered-pan distribution (every slot 1 pre-sleep pan; Merlin +2 post-sleep cinematic
    pans; the 6×Arthur_Kay_Lancelot multiset) AND plants OUT-OF-BODY pan calls so the
    body-scope exclusion is exercised."""
    bodies = []
    for n, (func, hero) in enumerate(HERO_FUNCS):
        rect = EXPECTED_RECT[hero]
        body = (
            f"function {func} takes nothing returns nothing\n"
            f"    call PanCameraToTimedLocForPlayer(GetOwningPlayer(GetTriggerUnit()), GetRectCenter({rect}), 0.00)\n")
        if hero == "Merlin":
            # the async cinematic tail: 2 EXTRA pans interleaved with TriggerSleepActions.
            body += (
                "    call TriggerSleepAction(3.00)\n"
                "    call PanCameraToTimedLocForPlayer(GetOwningPlayer(GetTriggerUnit()), GetRectCenter(gg_rct_It_Begins), 0.00)\n"
                "    call TriggerSleepAction(2.00)\n"
                "    call PanCameraToTimedLocForPlayer(GetOwningPlayer(GetTriggerUnit()), GetRectCenter(gg_rct_Merlin_Appear), 0.00)\n"
                "    call TriggerSleepAction(3.00)\n")
        body += "endfunction\n"
        bodies.append(body)
    # out-of-body pans (other map cinematics) — MUST NOT count.
    bodies.append(
        "function Trig_Intro_Cine_Actions takes nothing returns nothing\n"
        "    call PanCameraToTimedLocForPlayer(Player(0), GetRectCenter(gg_rct_Title_Appear), 0.00)\n"
        "    call PanCameraToTimedLocForPlayer(Player(1), GetRectCenter(gg_rct_Outro_Appear), 0.00)\n"
        "endfunction\n")
    extract = "\n".join(bodies)
    handler = (
        "//  Replaces the SHARED mechanics of the 10 hand-written Trig_<Hero>_Actions pick bodies.\n"
        "//  per-pick camera pan — faithful to every body's PanCameraToTimedLocForPlayer(picker,\n"
        "//  GetRectCenter(<appear rect>), 0.00) at this exact position. The single per-slot datum is\n"
        "//  the appear rect, carried as the pre-centered location udg_CastleSlot_CamLoc[i].\n"
        "//  Merlin's two EXTRA cinematic pans (TriggerSleepAction-gated) are NOT this op.\n"
        "//  Instead they ride the per-slot ExtrasHook cinematic tail, by design.\n"
        "    call PanCameraToTimedLocForPlayer(picker, udg_CastleSlot_CamLoc[i], 0.00)\n"
    )
    runbook = (
        "## STEP 2 — Wire the pedestals ... the 10 hand-written pick bodies\n"
        "| `CastleSlot_CamLoc` | location **array** | (none) | P2 | per-slot camera target = `GetRectCenter(<Appear rect>)` (data-init fills) |\n"
        "Merlin -> the intro CINEMATIC tail (3x TriggerSleepAction pacing the two extra camera pans).\n"
        "Smoke: ... pans the picker's camera to the appear rect, broadcasts the right announce line "
        "to all players ...\n"
    )
    return extract, runbook, handler


def selftest():
    print("=== SELFTEST: parser unit-tests + per-direction RED-catch (teeth) ===")
    extract, runbook, handler = _synth_ok()

    # parser sanity (body-scoped: the out-of-body cine func is NOT in HERO_FUNCS;
    # cinematic-scoped: Merlin's 2 post-sleep pans are NOT covered)
    f = live_facts(extract)
    assert f["n_found"] == 10 and not f["missing"], f
    assert _occupants(f["count"]) == EXPECTED_OCCUPANTS, _occupants(f["count"])
    assert sum(f["count"].values()) == EXPECTED_TOTAL, f["count"]
    assert all(p == PAN_SIG for p in f["pan"].values()), f["pan"]
    assert f["rect"] == EXPECTED_RECT, f["rect"]
    assert f["cinematic"]["Merlin"] == 2 and all(
        f["cinematic"][h] == 0 for _, h in HERO_FUNCS if h != "Merlin"), f["cinematic"]

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

    # 2) LIVE: drop a slot's covered pan -> every-slot + total trip
    bad = re.sub(
        r"    call PanCameraToTimedLocForPlayer\(GetOwningPlayer\(GetTriggerUnit\(\)\), GetRectCenter\(gg_rct_Guinevere_Appear\), 0\.00\)\n",
        "", extract)
    c_every = caught(all_rows(bad, runbook, handler), "cam:every-slot=1")
    c_total = caught(all_rows(bad, runbook, handler), "cam:total=10")

    # 3) LIVE: a slot's covered rect mis-bound -> appear-rect multiset trips
    bad = extract.replace("GetRectCenter(gg_rct_Percival_Appear)",
                          "GetRectCenter(gg_rct_Galahad_Appear)")
    c_multiset = caught(all_rows(bad, runbook, handler), "cam:appear-rect-multiset")

    # 4) LIVE: a covered pan uses a different player expr -> uniform-form trips
    bad = extract.replace(
        "call PanCameraToTimedLocForPlayer(GetOwningPlayer(GetTriggerUnit()), GetRectCenter(gg_rct_Nimue_Appear), 0.00)",
        "call PanCameraToTimedLocForPlayer(Player(5), GetRectCenter(gg_rct_Nimue_Appear), 0.00)", 1)
    c_uni = caught(all_rows(bad, runbook, handler), "cam:uniform-form")

    # 5) LIVE: a covered pan uses a non-zero duration -> uniform-form trips (regex won't
    #    match 1.50, so the pan is lost -> form/every-slot/total all react; assert form)
    bad = extract.replace(
        "call PanCameraToTimedLocForPlayer(GetOwningPlayer(GetTriggerUnit()), GetRectCenter(gg_rct_Galahad_Appear), 0.00)",
        "call PanCameraToTimedLocForPlayer(GetOwningPlayer(GetTriggerUnit()), GetRectCenter(gg_rct_Galahad_Appear), 1.50)", 1)
    c_dur = caught(all_rows(bad, runbook, handler), "cam:every-slot=1")

    # 6) LIVE: FOLD a cinematic pan into the spine — move Merlin's It_Begins pan BEFORE the
    #    first sleep (now 2 pre-sleep pans). cinematic-deferred (post=1) AND every-slot
    #    (Merlin=2 covered) both trip — the central cinematic-boundary teeth.
    bad = extract.replace(
        "    call PanCameraToTimedLocForPlayer(GetOwningPlayer(GetTriggerUnit()), GetRectCenter(gg_rct_Arthur_Kay_Lancelot_Appear), 0.00)\n"
        "    call TriggerSleepAction(3.00)\n"
        "    call PanCameraToTimedLocForPlayer(GetOwningPlayer(GetTriggerUnit()), GetRectCenter(gg_rct_It_Begins), 0.00)\n",
        "    call PanCameraToTimedLocForPlayer(GetOwningPlayer(GetTriggerUnit()), GetRectCenter(gg_rct_Arthur_Kay_Lancelot_Appear), 0.00)\n"
        "    call PanCameraToTimedLocForPlayer(GetOwningPlayer(GetTriggerUnit()), GetRectCenter(gg_rct_It_Begins), 0.00)\n"
        "    call TriggerSleepAction(3.00)\n")
    c_fold_cine = caught(all_rows(bad, runbook, handler), "cam:cinematic-deferred")
    c_fold_every = caught(all_rows(bad, runbook, handler), "cam:every-slot=1")

    # 7) LIVE: give a REGULAR slot a post-sleep cinematic pan -> cinematic-deferred trips
    bad = extract.replace(
        "function Trig_Sir_Kay_Actions takes nothing returns nothing\n"
        "    call PanCameraToTimedLocForPlayer(GetOwningPlayer(GetTriggerUnit()), GetRectCenter(gg_rct_Arthur_Kay_Lancelot_Appear), 0.00)\n"
        "endfunction\n",
        "function Trig_Sir_Kay_Actions takes nothing returns nothing\n"
        "    call PanCameraToTimedLocForPlayer(GetOwningPlayer(GetTriggerUnit()), GetRectCenter(gg_rct_Arthur_Kay_Lancelot_Appear), 0.00)\n"
        "    call TriggerSleepAction(1.00)\n"
        "    call PanCameraToTimedLocForPlayer(GetOwningPlayer(GetTriggerUnit()), GetRectCenter(gg_rct_Stray_Appear), 0.00)\n"
        "endfunction\n")
    c_stray_cine = caught(all_rows(bad, runbook, handler), "cam:cinematic-deferred")

    # 8) BODY-SCOPE TEETH: plant ANOTHER out-of-body covered-form pan (a func NOT in
    #    HERO_FUNCS). A correctly body-scoped gate must IGNORE it — total/every-slot stay
    #    GREEN. (If scoping regressed to a flat grep, this would inflate the family + trip.)
    bad = extract + (
        "\nfunction Trig_Extra_Quest_Actions takes nothing returns nothing\n"
        "    call PanCameraToTimedLocForPlayer(GetOwningPlayer(GetTriggerUnit()), GetRectCenter(gg_rct_Quest_Appear), 0.00)\n"
        "endfunction\n")
    c_scope = (not caught(all_rows(bad, runbook, handler), "cam:total=10")
               and not caught(all_rows(bad, runbook, handler), "cam:every-slot=1"))

    # 9) HANDLER drift: spine drops the CamLoc pan line -> total trips
    bad_h = handler.replace(PAN_SPINE, "call PanCameraToTimedLocForPlayer(picker, udg_WRONG_CamLoc[i], 0.00)")
    c_htot = caught(all_rows(extract, runbook, bad_h), "cam:total=10")

    # 10) HANDLER drift: header drops the cinematic-deferred claim -> cinematic-deferred trips
    bad_h = handler.replace("they ride the per-slot ExtrasHook cinematic tail",
                            "they are folded into the spine")
    c_hcine = caught(all_rows(extract, runbook, bad_h), "cam:cinematic-deferred")

    # 11) HANDLER drift: header drops the CamLoc datum claim -> appear-rect-multiset trips
    bad_h = handler.replace("udg_CastleSlot_CamLoc[i]", "udg_CastleSlot_WrongLoc[i]")
    c_hrect = caught(all_rows(extract, runbook, bad_h), "cam:appear-rect-multiset")

    # 12) PROSE drift: runbook drops the CamLoc target row -> appear-rect-multiset trips
    bad_rb = runbook.replace("per-slot camera target = `GetRectCenter(<Appear rect>)`",
                             "per-slot camera target = (some other dim)")
    c_prose = caught(all_rows(extract, bad_rb, handler), "cam:appear-rect-multiset")

    # 13) PROSE drift: runbook drops the cinematic claim -> cinematic-deferred trips
    bad_rb = runbook.replace("intro CINEMATIC tail", "intro something tail")
    c_prcine = caught(all_rows(extract, bad_rb, handler), "cam:cinematic-deferred")

    for name, val in [
        ("live body deleted", c_bodies), ("live drop pan every-slot", c_every),
        ("live drop pan total", c_total), ("live rect mis-bind (multiset)", c_multiset),
        ("live non-uniform player-expr", c_uni), ("live non-zero duration", c_dur),
        ("live fold cinematic pan (cine)", c_fold_cine),
        ("live fold cinematic pan (every-slot)", c_fold_every),
        ("live stray cinematic on regular slot", c_stray_cine),
        ("body-scope holds (out-of-body ignored)", c_scope),
        ("handler CamLoc-spine drift", c_htot), ("handler cinematic-claim drift", c_hcine),
        ("handler CamLoc-datum drift", c_hrect),
        ("prose CamLoc-row drop", c_prose), ("prose cinematic-claim drop", c_prcine),
    ]:
        print(f"  {name:<42}caught : {val}")
    ok = base_ok and all([c_bodies, c_every, c_total, c_multiset, c_uni, c_dur, c_fold_cine,
                          c_fold_every, c_stray_cine, c_scope, c_htot, c_hcine, c_hrect,
                          c_prose, c_prcine])
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
              "the camera-pan op cites are now suspect. Re-ground vs the new bake.")
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
        print("RESULT: FAIL — hero-select P2 camera-pan / appear-pan op drifted:")
        for lbl, d in fail:
            print(f"  - {lbl}: {d}")
        return 1
    print("RESULT: GREEN — the per-pick camera pan is bound vs the md5-pinned extract: all 10 live "
          "pick bodies are present; EVERY slot carries exactly 1 COVERED (pre-TriggerSleepAction) "
          "appear-pan (10 total — body-scoped past the 13 out-of-body PanCameraToTimedLocForPlayer "
          "calls AND cinematic-scoped past Merlin's 2 post-sleep cinematic pans); every covered pan "
          "is the arg-uniform PanCameraToTimedLocForPlayer(GetOwningPlayer(GetTriggerUnit()), "
          "GetRectCenter(<rect>), 0.00), and the 10 appear rects form the exact expected multiset "
          "(gg_rct_Arthur_Kay_Lancelot_Appear shared by 6 slots + 4 distinct) — matching the "
          "handler's collapse to ONE PanCameraToTimedLocForPlayer(picker, udg_CastleSlot_CamLoc[i], "
          "0.00) AND the runbook CamLoc 'per-slot camera target = GetRectCenter(<Appear rect>)' / "
          "'pans the picker's camera to the appear rect' claims, with Merlin's 2 cinematic pans "
          "correctly DEFERRED to the ExtrasHook (the synchronous spine never sleeps). The operator's "
          "STEP-1 CamLoc column cannot silently drift from the bodies it replaces, and the "
          "cinematic-boundary (no async pan leaking onto the spine) is locked.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
