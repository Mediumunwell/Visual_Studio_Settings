#!/usr/bin/env python3
"""
verify_hero_select_p2_runbook_anchors.py
================================================================================
KOTR Hero-Select REDESIGN (Track 4) · P2 APPLY-RUNBOOK PROSE <-> LIVE-EXTRACT binder.

WHY THIS GATE EXISTS (a real, uncovered seam — the Track-4 twin of the
companion-AI runbook binder + the hero-inv runbook binders #1/#2/#3)
--------------------------------------------------------------------------------
`hero_select_p2_APPLY_RUNBOOK.md` is the single ordered checklist Evan follows to
land the data-driven pick collapse (the generic `CastleSlot_ApplyPick(i)` that
replaces the 10 hand-written `Trig_<Hero>_Actions` pick bodies). To justify each
paste's integration point it pins LIVE `war3map.j` facts:

  * the byte-exact LINE RANGE of the 10 hand-written pick bodies it collapses,
  * the OCCURRENCE COUNTS of the canonical reuse-globals it tells the operator
    NOT to redeclare (`udg_SavePlayerHero` (40), `udg_SaveLoadEvent_Player` (209),
    `udg_SaveTempUnit` (48), `udg_Player1`..`udg_Player8` (21 each)),
  * the REF COUNTS of the two pre-existing map triggers the handler arms
    (`gg_trg_HeroPickAssignTalentTree` (21), `gg_trg_Flurry_AI` (9, bare)),
  * the rawcodes behind the irregular tails (`'LInf'`/`'h012'`/`'BTLF'`) and
    Percival's 4 `'nheb'` invuln mobs.

Those are LIVE-MAP facts but they live in **prose no gate parses**:

  * `verify_castleslot_global_contract.py` binds the STEP-0 var TABLE <-> the
    generated `.j` (names + types) — NOT these live cites.
  * `verify_runbook_globals.py` (fix_specs) guards STEP-0 global PRESENCE/ABSENCE
    for all 4 runbooks — it proves a reuse-global EXISTS, never that the runbook's
    stated OCCURRENCE COUNT still matches, nor the pick-body line range.
  * `verify_hero_select_p2_loop.py` / `audit_hero_select_p2_equivalence.py`
    compile + equivalence-prove the handler; they never read the runbook .md.
  * `verify_hero_select_phase0_recon_anchors.py` binds the **recon** prose <->
    live — NOT this runbook's copies of the same/adjacent cites.

So the moment the live extract drifts (a WE re-save renumbers JASS — the staleness
class that already bit B4b, and that this runbook had ALREADY suffered on its range
cite, below) the runbook would keep telling the operator "the 10 pick bodies are at
L49272–50920" or "udg_SaveLoadEvent_Player occurs 209×" while the live map disagrees
— a SILENT stale-runbook brick on the integration path. This binder closes that seam.

ONE CITE WAS STALE AT FIRST BIND (corrected in the runbook, dated 2026-06-18):
  * 10-pick-body line range: runbook said **L49272–50920**, but L50920 overshoots
    the 10th body (`Trig_Sir_Gawain_Actions` `endfunction` @ L50811) by 3 functions
    into the DEFERRED `Trig_newArthur/newGuinevere/newNimue` human-re-pick triggers
    (first non-pick header `Trig_newArthur_Actions` @ L50817). Corrected to
    **L49272–50811** — the exact span of the 10 named-hero bodies the equivalence
    audit grounds. The other 13 counts + the rawcodes verified unchanged.

WHAT IT CHECKS (read-only; touches no .w3x and no shippable .j)
--------------------------------------------------------------------------------
  1. The live canonical extract still hashes to the md5 the runbook pins
     (a re-bake is caught immediately, before any per-cite check can false-pass).
  2. COUNT anchors: each cited token's whole-word OCCURRENCE COUNT in the live
     extract == the runbook's stated count, AND the runbook prose still binds
     that token to that count (`TOKEN` ... `(COUNT`).
  3. RANGE anchor: L49272 is `function Trig_King_Arthur_Actions`, L50811 is the
     `endfunction` closing the 10th body, L50817 is the first NON-pick header,
     and exactly the 10 named-hero `Trig_<Hero>_Actions` bodies lie in
     [49272, 50811] — AND the prose still carries `L49272` and `50811`.
  4. PRESENCE anchors: the irregular-tail rawcodes (`'LInf'`/`'h012'`/`'BTLF'`)
     and Percival's 4 `'nheb'` mobs are present live (nheb byte-exact count 4),
     AND the prose still carries each rawcode literal.

Exit 0 only if md5 matches AND every anchor holds in both directions.

Run:        python3 verify_hero_select_p2_runbook_anchors.py
Self-test:  python3 verify_hero_select_p2_runbook_anchors.py --selftest

STANDALONE by design: prints RESULT and exits 1 on any drift, but is NOT wired
into verify_all.py, so the 178/178 static sweep is unchanged. Sibling of the
companion-AI runbook binder + the hero-inv runbook binders; same
EXTRACT / md5 / both-ways-binding contract.
"""
import hashlib
import re
import sys
from pathlib import Path

EXTRACT = Path.home() / "Warcraft III" / "KOTR" / "_extract_v050" / "war3map.j"
RUNBOOK = Path.home() / "Warcraft III" / "KOTR" / "_crew" / "hero_select_p2_APPLY_RUNBOOK.md"

# the md5 the runbook pins the canonical extract to (Grounding header)
RUNBOOK_CLAIMED_MD5 = "967131658fd8d4fb27ee0d7f74e4bd22"

# The dated audit note this binder appends to the runbook redundantly mentions
# the corrected cites; counting it would make the reverse check VACUOUS against a
# body edit (it would still "find" the cite in our own note). The reverse
# direction must bind the integration BODY the operator actually follows, so we
# strip the note before searching prose.
NOTE_MARKER = "**Re-ground note —"

# --- COUNT anchors: (label, token, claimed count, kind) ---
#   kind "word"       : whole-word occurrences `(?<!\w)TOKEN(?!\w)` — the runbook's
#                       own "(N) = grep occurrences" semantics, correctly excluding
#                       siblings (gg_trg_Flurry_AI's `_Copy` twin; udg_Player1 vs
#                       udg_Player10..12). Reverse: prose binds `TOKEN` ... `(COUNT`.
#   kind "placements" : DISTINCT `gg_unit_<TOKEN>_<NNNN>` unit placements — a "mobs"
#                       count, where the rawcode appears 2× per create line
#                       (unit-type + skin). Reverse: prose carries `COUNT ... TOKEN`.
COUNT_ANCHORS = [
    ("reuse SavePlayerHero",        "udg_SavePlayerHero",               40,  "word"),
    ("reuse SaveLoadEvent_Player",  "udg_SaveLoadEvent_Player",        209,  "word"),
    ("reuse SaveTempUnit",          "udg_SaveTempUnit",                 48,  "word"),
    ("reuse Player1",               "udg_Player1",                      21,  "word"),
    ("reuse Player2",               "udg_Player2",                      21,  "word"),
    ("reuse Player3",               "udg_Player3",                      21,  "word"),
    ("reuse Player4",               "udg_Player4",                      21,  "word"),
    ("reuse Player5",               "udg_Player5",                      21,  "word"),
    ("reuse Player6",               "udg_Player6",                      21,  "word"),
    ("reuse Player7",               "udg_Player7",                      21,  "word"),
    ("reuse Player8",               "udg_Player8",                      21,  "word"),
    ("armed trig TalentTree",       "gg_trg_HeroPickAssignTalentTree",  21,  "word"),
    ("armed trig Flurry_AI (bare)", "gg_trg_Flurry_AI",                  9,  "word"),
    ("Percival invuln nheb mobs",   "nheb",                              4,  "placements"),
]

# --- PRESENCE anchors: rawcode literal must appear live AND in prose ---
PRESENCE_ANCHORS = [
    ("Yvain spawn-ability LInf", "'LInf'"),
    ("Gawain polymorph h012",    "'h012'"),
    ("timed-life BTLF",          "'BTLF'"),
]

# --- RANGE anchor: the 10 hand-written pick bodies ---
RANGE_START = 49272            # function Trig_King_Arthur_Actions
RANGE_END = 50811              # endfunction of the 10th body (Trig_Sir_Gawain_Actions)
RANGE_FIRST_NONPICK = 50817    # function Trig_newArthur_Actions (deferred re-pick)
NAMED_BODIES = [               # the 10 the equivalence audit grounds, in live order
    "King_Arthur", "Lady_Guinevere", "Lady_of_the_Lake", "Merlin", "Sir_Kay",
    "Sir_Percival", "Sir_Galahad", "Sir_Lancelot", "Sir_Yvain", "Sir_Gawain",
]
ACT_HDR = re.compile(r'^function Trig_(.+)_Actions takes')


def whole_word_count(text, token):
    return len(re.findall(r'(?<!\w)' + re.escape(token) + r'(?!\w)', text))


def runbook_body(runbook_text):
    """The operator-facing body, excluding this binder's own audit note."""
    return runbook_text.split(NOTE_MARKER, 1)[0]


def audit_counts(extract_text, body):
    rows = []
    for label, token, claimed, kind in COUNT_ANCHORS:
        if kind == "placements":
            live = len(set(re.findall(r'gg_unit_' + re.escape(token) + r'_\d+', extract_text)))
            live_ok = live == claimed
            # reverse: prose carries `COUNT ... token` (e.g. "4 nheb mobs")
            prose_ok = bool(re.search(str(claimed) + r'\D{0,8}' + re.escape(token), body))
            countdesc = "distinct placements"
        else:
            live = whole_word_count(extract_text, token)
            live_ok = live == claimed
            # reverse: prose binds TOKEN to its parenthesised (COUNT nearby.
            prose_ok = _near(body, token, claimed)
            countdesc = "whole-word count"
        detail = ""
        if not live_ok:
            detail = f"live {countdesc}={live}, runbook claims {claimed}"
        elif not prose_ok:
            detail = f"runbook prose no longer binds {token!r} to count ({claimed})"
        rows.append((label, live_ok, prose_ok, detail))
    return rows


def _near(body, token, claimed, window=60):
    """Fallback: a `(COUNT` appears within `window` chars after the token."""
    for m in re.finditer(re.escape(token), body):
        seg = body[m.end():m.end() + window]
        if re.search(r'\(\s*' + str(claimed) + r'\b', seg):
            return True
    return False


def audit_presence(extract_text, body):
    rows = []
    for label, lit in PRESENCE_ANCHORS:
        live_ok = lit in extract_text
        prose_ok = lit in body
        detail = ""
        if not live_ok:
            detail = f"rawcode {lit!r} absent from live extract"
        elif not prose_ok:
            detail = f"runbook prose no longer carries {lit!r}"
        rows.append((label, live_ok, prose_ok, detail))
    return rows


def audit_range(extract_lines, body):
    """Return (live_ok, prose_ok, detail) for the 10-pick-body range anchor."""
    def line(n):
        return extract_lines[n - 1] if 0 < n <= len(extract_lines) else "<<EOF>>"

    start_ok = line(RANGE_START).startswith("function Trig_King_Arthur_Actions takes")
    end_ok = line(RANGE_END).strip() == "endfunction"
    nonpick_ok = line(RANGE_FIRST_NONPICK).startswith("function Trig_newArthur_Actions takes")
    found = []
    for i, l in enumerate(extract_lines):
        m = ACT_HDR.match(l)
        if m and RANGE_START <= i + 1 <= RANGE_END:
            found.append(m.group(1))
    bodies_ok = found == NAMED_BODIES
    live_ok = start_ok and end_ok and nonpick_ok and bodies_ok

    # reverse: prose must carry the corrected range (both endpoints)
    prose_ok = (f"L{RANGE_START}" in body) and (str(RANGE_END) in body)

    detail = ""
    if not live_ok:
        bits = []
        if not start_ok:
            bits.append(f"L{RANGE_START} != Trig_King_Arthur_Actions ({line(RANGE_START).strip()!r})")
        if not end_ok:
            bits.append(f"L{RANGE_END} != endfunction ({line(RANGE_END).strip()!r})")
        if not nonpick_ok:
            bits.append(f"L{RANGE_FIRST_NONPICK} != Trig_newArthur_Actions ({line(RANGE_FIRST_NONPICK).strip()!r})")
        if not bodies_ok:
            bits.append(f"bodies in range={found} (expected {NAMED_BODIES})")
        detail = "; ".join(bits)
    elif not prose_ok:
        detail = f"runbook prose no longer carries the L{RANGE_START}-{RANGE_END} range"
    return live_ok, prose_ok, detail


def all_rows(extract_text, runbook_text):
    body = runbook_body(runbook_text)
    extract_lines = extract_text.split("\n")
    rows = []
    rows += [("count:" + lbl, lo, po, d) for lbl, lo, po, d in audit_counts(extract_text, body)]
    rl, rp, rd = audit_range(extract_lines, body)
    rows.append(("range:10-pick-bodies", rl, rp, rd))
    rows += [("rawcode:" + lbl, lo, po, d) for lbl, lo, po, d in audit_presence(extract_text, body)]
    return rows


def report(rows):
    print(f"{'ANCHOR':<34}{'LIVE':<8}{'PROSE':<8}")
    for label, live_ok, prose_ok, detail in rows:
        print(f"{label:<34}{'OK' if live_ok else 'DRIFT':<8}{'OK' if prose_ok else 'DRIFT':<8}"
              + (f"  -> {detail}" if detail else ""))


def selftest():
    print("=== SELFTEST: counter unit-tests + per-category RED-catch (teeth) ===")
    # whole-word counter must exclude siblings
    synth = "gg_trg_Flurry_AI gg_trg_Flurry_AI_Copy gg_trg_Flurry_AI)"
    assert whole_word_count(synth, "gg_trg_Flurry_AI") == 2, "must exclude _Copy sibling"
    assert whole_word_count("udg_Player1 udg_Player10 udg_Player1,", "udg_Player1") == 2

    # build a synthetic live text + runbook that satisfy EVERY anchor
    lines = ["x"] * 76000
    lines[RANGE_START - 1] = "function Trig_King_Arthur_Actions takes nothing returns nothing"
    # place the 10 named headers spread across the range
    slots = [RANGE_START] + [RANGE_START + 100 * k for k in range(1, 10)]
    for n, name in zip(slots, NAMED_BODIES):
        lines[n - 1] = f"function Trig_{name}_Actions takes nothing returns nothing"
    lines[RANGE_END - 1] = "endfunction"
    lines[RANGE_FIRST_NONPICK - 1] = "function Trig_newArthur_Actions takes nothing returns nothing"
    text = "\n".join(lines)
    # append exact live evidence for each count token + presence rawcodes
    extra = []
    prose_counts = []
    for _, token, claimed, kind in COUNT_ANCHORS:
        if kind == "placements":
            extra += [f"gg_unit_{token}_{1000 + k}" for k in range(claimed)]
            prose_counts.append(f"Percival's {claimed} {token} mobs")
        else:
            extra += [token] * claimed
            prose_counts.append(f"`{token}` ({claimed})")
    for _, lit in PRESENCE_ANCHORS:
        extra.append(lit)
    text = text + "\n" + " ".join(extra)

    runbook = (f"the 10 bodies L{RANGE_START}–50811 ... "
               + " ".join(prose_counts) + " "
               + " ".join(lit for _, lit in PRESENCE_ANCHORS))
    base = all_rows(text, runbook)
    base_ok = all(lo and po for _, lo, po, _ in base)
    print(f"  baseline all-green             : {base_ok}")
    assert base_ok, [r for r in base if not (r[1] and r[2])]

    # 1) COUNT drift: drop one udg_SaveLoadEvent_Player occurrence
    bad = text.replace("udg_SaveLoadEvent_Player", "", 1)
    r1 = all_rows(bad, runbook)
    caught_count = any(lbl == "count:reuse SaveLoadEvent_Player" and not lo for lbl, lo, po, d in r1)

    # 2) RANGE drift: move the 10th body header out of range (renumbered past end)
    bad_lines = list(lines)
    bad_lines[slots[-1] - 1] = "x"
    bad_lines[RANGE_END + 50] = "function Trig_Sir_Gawain_Actions takes nothing returns nothing"
    bad_text = "\n".join(bad_lines) + "\n" + " ".join(extra)
    r2 = all_rows(bad_text, runbook)
    caught_range = any(lbl == "range:10-pick-bodies" and not lo for lbl, lo, po, d in r2)

    # 3) PROSE drop: runbook no longer carries the corrected range endpoint
    bad_runbook = runbook.replace("50811", "99999")
    r3 = all_rows(text, bad_runbook)
    caught_range_prose = any(lbl == "range:10-pick-bodies" and not po for lbl, lo, po, d in r3)

    # 4) PROSE drop: runbook no longer binds a count token to its number
    bad_runbook2 = runbook.replace("`udg_SavePlayerHero` (40)", "udg_SavePlayerHero exists")
    r4 = all_rows(text, bad_runbook2)
    caught_count_prose = any(lbl == "count:reuse SavePlayerHero" and not po for lbl, lo, po, d in r4)

    # 5) PRESENCE drift: rawcode vanished from live
    bad5 = text.replace("'h012'", "'XXXX'")
    r5 = all_rows(bad5, runbook)
    caught_presence = any(lbl == "rawcode:Gawain polymorph h012" and not lo for lbl, lo, po, d in r5)

    print(f"  count-drift caught             : {caught_count}")
    print(f"  range-drift caught             : {caught_range}")
    print(f"  range prose-drop caught        : {caught_range_prose}")
    print(f"  count prose-drop caught        : {caught_count_prose}")
    print(f"  presence-drift caught          : {caught_presence}")
    ok = all([base_ok, caught_count, caught_range, caught_range_prose,
              caught_count_prose, caught_presence])
    print(f"\nSELFTEST {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 3


def main():
    if "--selftest" in sys.argv:
        return selftest()
    if not EXTRACT.exists():
        print(f"FATAL: live extract not found: {EXTRACT}")
        return 2
    if not RUNBOOK.exists():
        print(f"FATAL: hero-select P2 runbook not found: {RUNBOOK}")
        return 2

    raw = EXTRACT.read_bytes()
    md5 = hashlib.md5(raw).hexdigest()
    print(f"live extract : {EXTRACT}")
    print(f"  md5={md5}  (runbook pins {RUNBOOK_CLAIMED_MD5})")
    if md5 != RUNBOOK_CLAIMED_MD5:
        print("RESULT: FAIL — live extract md5 DRIFTED from the runbook-pinned hash; "
              "every count/line cite below is now suspect. Re-ground the runbook against the new bake.")
        return 1

    extract_text = raw.decode("latin-1")
    runbook_text = RUNBOOK.read_text()
    rows = all_rows(extract_text, runbook_text)
    report(rows)

    fail = [(lbl, d) for lbl, lo, po, d in rows if not (lo and po)]
    fwd_ok = sum(1 for _, lo, _, _ in rows if lo)
    rev_ok = sum(1 for _, _, po, _ in rows if po)
    print(f"\nanchors={len(rows)}  forward(live)={fwd_ok}/{len(rows)}  "
          f"reverse(prose)={rev_ok}/{len(rows)}  md5=OK")
    if fail:
        print("RESULT: FAIL — hero-select P2 runbook live cites have drifted:")
        for lbl, d in fail:
            print(f"  - {lbl}: {d}")
        return 1
    print(f"RESULT: GREEN — all {len(rows)} live `war3map.j` cites in "
          "hero_select_p2_APPLY_RUNBOOK.md hold vs the md5-pinned extract AND the "
          "runbook prose still carries every cite (10-pick-body range L49272-50811, "
          "11 reuse-global occurrence counts, 2 armed-trigger ref counts, Percival's "
          "4 nheb mobs, + the LInf/h012/BTLF tail rawcodes). The hero-select P2 apply "
          "runbook is bound both ways.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
