#!/usr/bin/env python3
"""
verify_we_diffs_runbook_anchors.py
================================================================================
KOTR we_diffs (bug-fix B1..DESYNC2) · APPLY-RUNBOOK PROSE <-> LIVE-EXTRACT binder.

WHY THIS GATE EXISTS (a real, uncovered seam — the bug-fix twin of the already
bound companion-AI + hero-inventory APPLY-RUNBOOK binders)
--------------------------------------------------------------------------------
`we_diffs_APPLY_RUNBOOK.md` is the single ordered checklist Evan follows to land
all twelve v0.50 bug-fixes (B1, B1b, B4, B4b, B2, B8, B3, B6, B11, B10, B5B7, B9,
LEAK, DESYNC2) in ONE World-Editor sitting. Unlike the companion-AI runbook it
deliberately pins **NO absolute line numbers** — its own golden rule is "World
Editor renumbers JASS on every save, so ALWAYS re-locate by GUI element (trigger
name), never by line." So the facts it commits to — and that an operator's whole
sitting depends on — are the **named trigger / library / spawn-raw anchors it
declares "confirmed live"**, plus the md5 the grounding header pins.

Those are LIVE-MAP facts, but they live in **prose no gate parses**:

  * `fix_specs/verify_all.py` (178/178) compiles the PASTE SET — it never reads
    this GUI runbook .md, and knows nothing of these trigger NAMES.
  * The per-B `*_REGROUNDED_TO_LIVE_EXTRACT` certs ground each individual diff —
    none binds this master runbook's roll-up of the anchors.
  * The companion-AI / hero-inv / hero-select runbook binders bind THEIR runbooks;
    none touches the bug-fix runbook.

So the moment the live extract drifts (a WE re-save renames or deletes a trigger,
the exact staleness class that already bit the companion runbook's NONEXISTENT
`gg_rct_Camelot_1` cite — see verify_companion_ai_runbook_anchors.py), or someone
edits this runbook to point at a trigger that no longer exists, the operator would
be sent hunting for a GUI element the live map no longer has — a SILENT
stale-runbook brick on the bug-fix integration path. This binder closes that seam.

WHAT IT BINDS (read-only; touches no .w3x and no shippable .j)
--------------------------------------------------------------------------------
  0. The live canonical extract still hashes to the md5 the runbook's Grounding
     header pins (a re-bake is caught immediately, before any anchor can false-pass).
  1. Eight GUI trigger anchors (B1/B1b/B4 GetFinishQuests, B4b QuestGen_Main, B4
     Talktome_Talks, B2 Quest_Kills_Under_Arches, B8 Cheese, B3 Bringmeitems_Items,
     B6/B11/B10 limit_break_continues, B9 BK_Cast): each `gg_trg_<name>` is declared
     EXACTLY ONCE in the live extract (forward — present and unambiguous), AND the
     runbook body still names it (reverse).
  3. Three custom-script anchors (LEAK CombinedCameraSliderSystem; the B11 "library
     callback to KEEP" s__HFlame_LB_Dmg_LS; the DESYNC2 LoadSaveSlot read path):
     present in the live extract AND named in the runbook body.
  4. Four B2 cheese-wave spawn raws ('nenf','nomg','nogm','nogl'): present in the
     live extract AND named in the runbook body.
  5. The B5B7 dual fact the runbook leans on: the Flurry clone 'H00I' IS referenced
     in the live `.j` (as MH_Dummy_Type), WHILE its sound-set field `usnd` is NOT in
     the `.j` at all (count 0) — proving the runbook's claim that the sound-set
     silence is an Object-Editor step, not a trigger edit. Reverse: 'H00I' is named.

NOT bound (and why — honesty for the next engine): the parenthetical grep
"ref counts" the runbook shows per group ("(22 refs)", "(43)", ...) are NOT bound.
They do not reproduce against the md5-pinned extract under any counting method
(line `grep -c`, occurrence `grep -o`, prefixed or bare), and the runbook itself
frames them as informal and warns they "drift the moment you apply the first fix."
Binding a number I cannot reproduce would force a false RED on a fact I cannot
confirm is wrong vs my-count-being-wrong. The reproducible, sitting-critical
commitments are the anchor NAMES and the md5 — those are what this binder pins.

Exit 0 only if md5 matches AND every anchor holds in both directions.

Run:        python3 verify_we_diffs_runbook_anchors.py
Self-test:  python3 verify_we_diffs_runbook_anchors.py --selftest

STANDALONE by design (sibling of the companion-AI / hero-inv runbook binders):
prints RESULT and exits 1 on any drift, NOT wired into fix_specs/verify_all.py, so
the 178/178 static sweep is unchanged. It IS registered in verify_builder_gates.py
(the cli/builder aggregate sweep), whose discovery cross-check would otherwise flag
it as unregistered rot.
"""
import hashlib
import sys
from pathlib import Path

EXTRACT = Path.home() / "Warcraft III" / "KOTR" / "_extract_v050" / "war3map.j"
RUNBOOK = Path.home() / "Warcraft III" / "KOTR" / "_crew" / "we_diffs_APPLY_RUNBOOK.md"

# the md5 the runbook's Grounding header pins the canonical extract to
RUNBOOK_CLAIMED_MD5 = "967131658fd8d4fb27ee0d7f74e4bd22"

# Anchor kinds:
#   "trig"   forward = `trigger gg_trg_<key>= null` appears EXACTLY ONCE in extract;
#            reverse  = `gg_trg_<key>` present in runbook body.
#   "script" forward = <key> substring present (count > 0) in extract;
#            reverse  = <key> present in runbook body.
#   "raw"    forward = `'<key>'` present in extract; reverse = <key> present in body.
#   "h00i"   special dual fact (see below); reverse = "H00I" present in body.
#
# (label, kind, key, B-fix it anchors)
ANCHORS = [
    # --- GUI trigger anchors (the runbook's "Trigger anchors confirmed live" lines) ---
    ("GetFinishQuests",          "trig",   "GetFinishQuests",          "B1/B1b/B4 turn-in giver"),
    ("QuestGen_Main",            "trig",   "QuestGen_Main",            "B4b offer path"),
    ("Talktome_Talks",           "trig",   "Talktome_Talks",           "B4 second turn-in giver"),
    ("Quest_Kills_Under_Arches", "trig",   "Quest_Kills_Under_Arches", "B2 cheese supply spawn"),
    ("Cheese",                   "trig",   "Cheese",                   "B8 pickup-gate condition"),
    ("Bringmeitems_Items",       "trig",   "Bringmeitems_Items",       "B3 item-charge credit"),
    ("limit_break_continues",    "trig",   "limit_break_continues",    "B6/B11/B10 chain-hop loop"),
    ("BK_Cast",                  "trig",   "BK_Cast",                  "B9 old Black-Knight driver"),
    # --- custom-script anchors ---
    ("CombinedCameraSliderSystem", "script", "CombinedCameraSliderSystem", "LEAK boolexpr cache"),
    ("s__HFlame_LB_Dmg_LS",        "script", "s__HFlame_LB_Dmg_LS",        "B11 library callback to KEEP"),
    ("LoadSaveSlot",               "script", "LoadSaveSlot",               "DESYNC2 read path"),
    # --- B2 cheese-wave spawn raws ---
    ("spawn 'nenf'", "raw", "nenf", "B2 thief restored to ogre wave"),
    ("spawn 'nomg'", "raw", "nomg", "B2 ogre-only wave member"),
    ("spawn 'nogm'", "raw", "nogm", "B2 ogre-only wave member"),
    ("spawn 'nogl'", "raw", "nogl", "B2 graduated wave / Quest_Mobs1"),
    # --- B5B7 dual fact ---
    ("Flurry clone 'H00I' (OE-soundset)", "h00i", "H00I", "B5B7 sound-set is OE-only"),
]


# The dated re-ground note this binder appends to the runbook must NOT satisfy the
# reverse check (that would make it vacuous against a body edit). Strip it first —
# bind the operator-facing BODY only, exactly like the companion-AI runbook binder.
NOTE_MARKER = "**Re-ground note (we_diffs runbook binder)"


def runbook_body(runbook_text: str) -> str:
    return runbook_text.split(NOTE_MARKER, 1)[0]


def _forward_ok(kind, key, extract_text):
    """Return (ok, detail) for the live-extract direction."""
    if kind == "trig":
        decl = f"trigger gg_trg_{key}= null"
        n = extract_text.count(decl)
        if n == 1:
            return True, ""
        return False, f"`{decl}` declared {n}x in live extract (want exactly 1)"
    if kind == "script":
        if key in extract_text:
            return True, ""
        return False, f"custom-script anchor {key!r} not found in live extract"
    if kind == "raw":
        tok = f"'{key}'"
        if tok in extract_text:
            return True, ""
        return False, f"spawn raw {tok} not found in live extract"
    if kind == "h00i":
        present = f"'{key}'" in extract_text
        usnd_absent = ("usnd" not in extract_text)
        if present and usnd_absent:
            return True, ""
        why = []
        if not present:
            why.append("'H00I' not referenced in .j")
        if not usnd_absent:
            why.append("sound-set field `usnd` IS in .j (runbook says OE-only)")
        return False, "; ".join(why)
    return False, f"unknown anchor kind {kind!r}"


def _reverse_token(kind, key):
    """The string the runbook body must still carry."""
    if kind == "trig":
        return f"gg_trg_{key}"
    return key  # script / raw / h00i name as written in prose


def audit_anchors(extract_text, runbook_text):
    """Return list of (label, live_ok, prose_ok, detail)."""
    body = runbook_body(runbook_text)
    rows = []
    for label, kind, key, _bfix in ANCHORS:
        live_ok, fdetail = _forward_ok(kind, key, extract_text)
        token = _reverse_token(kind, key)
        prose_ok = token in body
        detail = ""
        if not live_ok:
            detail = fdetail
        elif not prose_ok:
            detail = f"runbook body no longer names {token!r}"
        rows.append((label, live_ok, prose_ok, detail))
    return rows


def report(rows):
    print(f"{'ANCHOR':<34}{'B-FIX':<28}{'LIVE':<7}{'PROSE':<7}")
    for (label, _kind, _key, bfix), (_, live_ok, prose_ok, detail) in zip(ANCHORS, rows):
        bf = bfix if len(bfix) <= 26 else bfix[:23] + "..."
        print(f"{label:<34}{bf:<28}{'OK' if live_ok else 'DRIFT':<7}"
              f"{'OK' if prose_ok else 'DRIFT':<7}" + (f"  -> {detail}" if detail else ""))


def selftest():
    print("=== SELFTEST: forward+reverse binding has teeth (trig-dup / script-gone / "
          "raw-gone / H00I-usnd / prose-drop) ===")
    # Build a synthetic extract + runbook body that satisfy EVERY anchor.
    extract = []
    body = "we_diffs synthetic runbook body\n"
    for label, kind, key, _bf in ANCHORS:
        if kind == "trig":
            extract.append(f"trigger gg_trg_{key}= null")
            body += f"`gg_trg_{key}` confirmed live\n"
        elif kind == "script":
            extract.append(f"call {key}()")
            body += f"`{key}` anchor\n"
        elif kind == "raw":
            extract.append(f"set x='{key}'")
            body += f"creates `{key}`\n"
        elif kind == "h00i":
            extract.append(f"set udg_MH_Dummy_Type='{key}'")  # present, and NO usnd anywhere
            body += f"Flurry clone `{key}`\n"
    extract_text = "\n".join(extract)
    base = audit_anchors(extract_text, body)
    assert all(r[1] and r[2] for r in base), "baseline anchors should all pass both ways"

    # 1) DUPLICATE a trigger decl (re-save split one trigger into two) -> forward DRIFT
    dup = extract_text + "\ntrigger gg_trg_BK_Cast= null"
    caught_dup = any(lbl == "BK_Cast" and not lo for lbl, lo, po, d in audit_anchors(dup, body))

    # 2) DELETE a custom-script anchor -> forward DRIFT
    gone = extract_text.replace("call CombinedCameraSliderSystem()", "call SomethingElse()")
    caught_script = any(lbl == "CombinedCameraSliderSystem" and not lo
                        for lbl, lo, po, d in audit_anchors(gone, body))

    # 3) DELETE a spawn raw -> forward DRIFT
    norraw = extract_text.replace("set x='nenf'", "set x='zzzz'")
    caught_raw = any(lbl == "spawn 'nenf'" and not lo
                     for lbl, lo, po, d in audit_anchors(norraw, body))

    # 4) H00I: a re-bake that LEAKS the sound-set field usnd into the .j -> forward DRIFT
    leaked = extract_text + '\nset usnd="HeroPaladin"'
    caught_h00i = any(lbl.startswith("Flurry clone") and not lo
                      for lbl, lo, po, d in audit_anchors(leaked, body))

    # 5) DROP a trigger name from the runbook body (live unchanged) -> reverse DRIFT
    bad_body = body.replace("`gg_trg_GetFinishQuests`", "(removed)")
    caught_prose = any(lbl == "GetFinishQuests" and not po
                       for lbl, lo, po, d in audit_anchors(extract_text, bad_body))

    print(f"  trigger-duplicate caught   : {caught_dup}")
    print(f"  script-deleted caught      : {caught_script}")
    print(f"  spawn-raw-deleted caught   : {caught_raw}")
    print(f"  H00I usnd-leak caught      : {caught_h00i}")
    print(f"  prose-name-drop caught     : {caught_prose}")
    ok = all([caught_dup, caught_script, caught_raw, caught_h00i, caught_prose])
    print(f"\nSELFTEST {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 3


def main():
    if "--selftest" in sys.argv:
        return selftest()
    if not EXTRACT.exists():
        print(f"FATAL: live extract not found: {EXTRACT}")
        return 2
    if not RUNBOOK.exists():
        print(f"FATAL: we_diffs runbook not found: {RUNBOOK}")
        return 2

    raw = EXTRACT.read_bytes()
    md5 = hashlib.md5(raw).hexdigest()
    print(f"live extract : {EXTRACT}")
    print(f"  md5={md5}  (runbook pins {RUNBOOK_CLAIMED_MD5})")
    if md5 != RUNBOOK_CLAIMED_MD5:
        print("RESULT: FAIL — live extract md5 DRIFTED from the runbook-pinned hash; "
              "every trigger/raw anchor below is now suspect. Re-ground the runbook "
              "against the new bake.")
        return 1

    extract_text = raw.decode("latin-1")
    runbook_text = RUNBOOK.read_text()
    rows = audit_anchors(extract_text, runbook_text)
    report(rows)

    fail = [(lbl, d) for lbl, lo, po, d in rows if not (lo and po)]
    fwd_ok = sum(1 for _, lo, _, _ in rows if lo)
    rev_ok = sum(1 for _, _, po, _ in rows if po)
    print(f"\nanchors={len(rows)}  forward(live)={fwd_ok}/{len(rows)}  "
          f"reverse(prose)={rev_ok}/{len(rows)}  md5=OK")
    if fail:
        print("RESULT: FAIL — we_diffs apply-runbook anchors have drifted:")
        for lbl, d in fail:
            print(f"  - {lbl}: {d}")
        return 1
    print(f"RESULT: GREEN — all {len(rows)} we_diffs APPLY-RUNBOOK GUI anchors hold vs the "
          "md5-pinned live extract AND the runbook body still names every one: the 8 "
          "trigger anchors (each declared exactly once — GetFinishQuests, QuestGen_Main, "
          "Talktome_Talks, Quest_Kills_Under_Arches, Cheese, Bringmeitems_Items, "
          "limit_break_continues, BK_Cast), the 3 custom-script anchors "
          "(CombinedCameraSliderSystem, s__HFlame_LB_Dmg_LS, LoadSaveSlot), the 4 B2 "
          "cheese-wave spawn raws (nenf/nomg/nogm/nogl), and the B5B7 dual fact "
          "('H00I' in the .j while its sound-set `usnd` is OE-only). The bug-fix apply "
          "runbook is bound both ways.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
