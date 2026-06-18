#!/usr/bin/env python3
"""
verify_hero_select_p2_crew_vs_authority.py
================================================================================
KOTR hero-select P2 · OPERATOR PASTE BLOB <-> PJASS-COMPILED AUTHORITY binder.

WHY THIS GATE EXISTS (the exact seam the dropped-camera-pan regression slipped
through on 2026-06-18)
--------------------------------------------------------------------------------
There are TWO independently-generated copies of the `InitCastleSlotData` data
body, produced by TWO different scripts from the live extract:

  A. `_crew/hero_select_p2_InitCastleSlotData.generated.j` — the blob an operator
     literally pastes into the World Editor. Emitted by
     `fix_specs/verify_hero_select_p2_datatable.py` (the `extract_slot` path).

  B. `fix_specs/hero_select_p2_loop_data.gen.j` — the AUTHORITY: regenerated every
     run of `fix_specs/verify_hero_select_p2_loop.py`, COMPILED clean against the
     operator's real pjass.exe alongside the generic handler, and grounded
     statement-for-statement against the live bodies by
     `audit_hero_select_p2_equivalence.py`. It is emitted by the loop gate's OWN
     emission code with its OWN `extract_cam_rect` (it does NOT trust the datatable
     generator's CamRect).

These two paths are supposed to carry byte-identical `set udg_CastleSlot_*` data.
NOTHING checked that they did. On 2026-06-18 the authority (B) carried all 10
per-slot `udg_CastleSlot_CamLoc[i]` camera-pan fills while the paste blob (A)
DROPPED every one of them — because A's generator never captured the per-body
`PanCameraToTimedLocForPlayer`. The `_crew` self-binder
(`verify_hero_select_p2_generated_j.py`) stayed GREEN the whole time: it only
checks blob<->its-own-JSON consistency, so a pair that is mutually consistent yet
COLLECTIVELY stale vs the compiled authority is invisible to it. An operator would
have pasted A and shipped heroes that spawn with no camera pan — a silent gameplay
regression vs all 10 original triggers.

This binder closes that seam: it asserts the operator's paste blob (A) carries the
EXACT same ordered `set udg_CastleSlot_<field>[<idx>] = <rhs>` data lines as the
pjass-compiled, equivalence-audited authority (B). Either independent generator
drifting from the other — the precise CamLoc failure mode — is now a hard RED.

WHAT IT BINDS (read-only; touches no .w3x and no shippable .j)
--------------------------------------------------------------------------------
  Inside `function InitCastleSlotData ... endfunction` of BOTH files:
   1. SEQUENCE: the ordered list of `set udg_CastleSlot_*` lines (whitespace-
      normalized) is element-for-element identical (catches a reorder / an inserted
      or deleted line on either side).
   2. KEYS: the SET of `(field, index)` keys is identical in both (catches a dropped
      assignment even if the surviving lines happen to still line up — e.g. all 10
      CamLoc lines missing from A only).
   3. VALUES: for every shared key the right-hand side is byte-identical (catches a
      mis-pointed value — wrong appear rect, wrong span offset, wrong rawcode).

This binder is DELIBERATELY independent of `verify_hero_select_p2_generated_j.py`:
that one ties A to its own datatable JSON; this one ties A to the COMPILED AUTHORITY
B. Both must hold for the paste blob to be trustworthy.

Run:        python3 verify_hero_select_p2_crew_vs_authority.py
Self-test:  python3 verify_hero_select_p2_crew_vs_authority.py --selftest

STANDALONE by design (sibling of the other Track-4 binders): prints RESULT and
exits 1 on any drift, NOT wired into fix_specs/verify_all.py (the 178/178 static
sweep is unchanged). It IS registered in verify_builder_gates.py (the cli/builder
aggregate sweep), whose discovery cross-check would otherwise flag it as
unregistered rot.
"""
import re
import sys
from pathlib import Path

CREW_BLOB = (Path.home() / "Warcraft III" / "KOTR" / "_crew"
             / "hero_select_p2_InitCastleSlotData.generated.j")
AUTHORITY = (Path.home() / "Systems_Migration" / "kotr" / "fix_specs"
             / "hero_select_p2_loop_data.gen.j")

# `set udg_CastleSlot_<Field>[<idx>] = <rhs>` — the only lines this gate compares.
_SET = re.compile(r"^\s*set\s+udg_CastleSlot_(\w+)\[(\d+)\]\s*=\s*(.+?)\s*$")
_FUNC = re.compile(r"^\s*function\s+InitCastleSlotData\b")
_ENDFUNC = re.compile(r"^\s*endfunction\b")


def extract_sets(text, label):
    """Return the ordered list of (field, idx, rhs) from InitCastleSlotData's body.

    Scoped to within `function InitCastleSlotData ... endfunction` so a stray
    CastleSlot assignment elsewhere in the file can't pollute the comparison. If the
    function is absent the whole-file CastleSlot sets are used (the _crew blob IS the
    bare function with no wrapping `function` header in some bakes) — but only when no
    function delimiter is present at all.
    """
    lines = text.splitlines()
    in_fn = False
    saw_fn = False
    seq = []
    for ln in lines:
        if _FUNC.match(ln):
            in_fn, saw_fn = True, True
            continue
        if in_fn and _ENDFUNC.match(ln):
            in_fn = False
            continue
        if in_fn:
            m = _SET.match(ln)
            if m:
                seq.append((m.group(1), int(m.group(2)), m.group(3)))
    if not saw_fn:
        # no function delimiter anywhere -> treat every CastleSlot set as in-body
        for ln in lines:
            m = _SET.match(ln)
            if m:
                seq.append((m.group(1), int(m.group(2)), m.group(3)))
    return seq


def audit(crew_seq, auth_seq):
    """Return list of (category, label, ok, detail) checks."""
    checks = []

    def add(cat, label, ok, detail=""):
        checks.append((cat, label, ok, detail))

    # --- presence: both sides actually produced data lines ---
    add("present", "crew blob has data lines", len(crew_seq) > 0,
        f"crew lines={len(crew_seq)}")
    add("present", "authority has data lines", len(auth_seq) > 0,
        f"auth lines={len(auth_seq)}")

    # --- 1. SEQUENCE: ordered, element-for-element identical ---
    add("seq", "same line count", len(crew_seq) == len(auth_seq),
        f"crew={len(crew_seq)} auth={len(auth_seq)}")
    mism = []
    for k in range(min(len(crew_seq), len(auth_seq))):
        if crew_seq[k] != auth_seq[k]:
            cf, ci, cr = crew_seq[k]
            af, ai, ar = auth_seq[k]
            mism.append(f"[{k}] crew={cf}[{ci}]={cr!r} auth={af}[{ai}]={ar!r}")
    add("seq", "ordered lines identical", not mism,
        "; ".join(mism[:4]) + (" ..." if len(mism) > 4 else ""))

    # --- 2. KEYS: same (field, idx) set both ways ---
    crew_keys = {(f, i) for f, i, _ in crew_seq}
    auth_keys = {(f, i) for f, i, _ in auth_seq}
    only_auth = sorted(auth_keys - crew_keys)
    only_crew = sorted(crew_keys - auth_keys)
    add("keys", "no assignment missing from crew blob", not only_auth,
        f"in authority but DROPPED from paste blob: {only_auth[:8]}"
        + (" ..." if len(only_auth) > 8 else ""))
    add("keys", "no extra assignment in crew blob", not only_crew,
        f"in paste blob but not authority: {only_crew[:8]}"
        + (" ..." if len(only_crew) > 8 else ""))

    # --- 3. VALUES: shared keys carry byte-identical RHS ---
    crew_map = {(f, i): r for f, i, r in crew_seq}
    auth_map = {(f, i): r for f, i, r in auth_seq}
    vdrift = []
    for key in sorted(crew_keys & auth_keys):
        if crew_map[key] != auth_map[key]:
            vdrift.append(f"{key[0]}[{key[1]}] crew={crew_map[key]!r} "
                          f"auth={auth_map[key]!r}")
    add("value", "shared keys byte-identical RHS", not vdrift,
        "; ".join(vdrift[:4]) + (" ..." if len(vdrift) > 4 else ""))

    return checks


def report(checks):
    for cat in ("present", "seq", "keys", "value"):
        rows = [c for c in checks if c[0] == cat]
        if not rows:
            continue
        npass = sum(1 for _, _, ok, _ in rows if ok)
        print(f"[{cat:<7}] {npass}/{len(rows)} ok")
        for _cat, label, ok, detail in rows:
            if not ok:
                print(f"    DRIFT {label}: {detail}")


def selftest():
    print("=== SELFTEST: crew-blob <-> compiled-authority binder has teeth "
          "(seq / keys / value / count) ===")
    # A small but structurally faithful pair: identical CastleSlot data, different
    # wrapping (the authority has a globals extern block + no slot comments; the crew
    # blob has slot comments) — exactly the real shape.
    DATA = [
        "set udg_CastleSlot_HeroType[0]='Harf'",
        'set udg_CastleSlot_NameStr[0]="TRIGSTR_839"',
        "set udg_CastleSlot_CamLoc[0]=GetRectCenter(gg_rct_Arthur_Kay_Lancelot_Appear)",
        "set udg_CastleSlot_HeroType[1]='Hvwd'",
        "set udg_CastleSlot_CamLoc[1]=GetRectCenter(gg_rct_Guinevere_Appear)",
        "set udg_CastleSlot_Item[0]='I005'",
    ]

    def crew_blob(lines):
        out = ["// AUTO-GENERATED — DO NOT hand-edit.",
               "function InitCastleSlotData takes nothing returns nothing"]
        for i, l in enumerate(lines):
            if l.startswith("set udg_CastleSlot_HeroType"):
                out.append(f"    // --- slot {l.split('[')[1][0]} ---")
            out.append("    " + l)
        out.append("    // owner=udg_x claim=udg_onex pedestal=['gg_unit_y']")
        out.append("endfunction")
        return "\n".join(out)

    def authority(lines):
        out = ["globals", "    unit gg_unit_x = null", "endglobals",
               "function InitCastleSlotData takes nothing returns nothing"]
        out += ["    " + l for l in lines]
        out.append("endfunction")
        return "\n".join(out)

    good_crew = crew_blob(DATA)
    good_auth = authority(DATA)
    base = audit(extract_sets(good_crew, "crew"), extract_sets(good_auth, "auth"))
    assert all(ok for _, _, ok, _ in base), \
        "baseline should pass: " + str([(l, d) for c, l, ok, d in base if not ok])

    def caught(crew_text=None, auth_text=None, cat=None):
        rows = audit(extract_sets(crew_text if crew_text is not None else good_crew, "c"),
                     extract_sets(auth_text if auth_text is not None else good_auth, "a"))
        return any((cat is None or c == cat) and not ok for c, l, ok, dt in rows)

    # 1) THE ORIGINAL DEFECT: every CamLoc dropped from the paste blob only.
    crew_no_cam = "\n".join(l for l in good_crew.splitlines()
                            if "udg_CastleSlot_CamLoc" not in l)
    c_camdrop = caught(crew_text=crew_no_cam)                       # keys + seq + count
    c_camdrop_keys = caught(crew_text=crew_no_cam, cat="keys")
    # 2) one CamLoc points at the WRONG appear rect on the authority side.
    auth_wrong = good_auth.replace("gg_rct_Guinevere_Appear", "gg_rct_Nimue_Appear")
    c_value = caught(auth_text=auth_wrong, cat="value")
    # 3) a span offset hand-edited in the paste blob.
    crew_badspan = good_crew.replace("HeroType[1]='Hvwd'", "HeroType[1]='ZZZZ'")
    c_seq = caught(crew_text=crew_badspan, cat="seq")
    # 4) an EXTRA stray assignment inserted into the paste blob.
    crew_extra = good_crew.replace(
        "endfunction", "    set udg_CastleSlot_HeroType[2]='Hjai'\nendfunction")
    c_extra = caught(crew_text=crew_extra, cat="keys")
    # 5) a reorder of two lines on the authority side (same keys/values, wrong order).
    al = good_auth.splitlines()
    # swap the two CamLoc-adjacent HeroType lines region: move Item line up front
    al2 = [l for l in al if "udg_CastleSlot_Item[0]" not in l]
    insert_at = next(k for k, l in enumerate(al2) if "InitCastleSlotData" in l) + 1
    al2.insert(insert_at, "    set udg_CastleSlot_Item[0]='I005'")
    c_reorder = caught(auth_text="\n".join(al2), cat="seq")

    print(f"  CamLoc-drop (paste blob) caught : {c_camdrop} (keys cat: {c_camdrop_keys})")
    print(f"  wrong-appear-rect value caught   : {c_value}")
    print(f"  span/scalar hand-edit caught     : {c_seq}")
    print(f"  extra stray assignment caught    : {c_extra}")
    print(f"  authority reorder caught         : {c_reorder}")
    ok = all([c_camdrop, c_camdrop_keys, c_value, c_seq, c_extra, c_reorder])
    print(f"\nSELFTEST {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 3


def main():
    if "--selftest" in sys.argv:
        return selftest()
    for p, what in ((CREW_BLOB, "crew paste blob"), (AUTHORITY, "compiled authority")):
        if not p.exists():
            print(f"FATAL: {what} not found: {p}")
            return 2

    crew_seq = extract_sets(CREW_BLOB.read_text(), "crew")
    auth_seq = extract_sets(AUTHORITY.read_text(), "auth")

    print(f"crew paste blob   : {CREW_BLOB}")
    print(f"  ({len(crew_seq)} udg_CastleSlot_* data lines)")
    print(f"compiled authority: {AUTHORITY}")
    print(f"  ({len(auth_seq)} udg_CastleSlot_* data lines)\n")

    checks = audit(crew_seq, auth_seq)
    report(checks)

    fail = [(c, l, d) for c, l, ok, d in checks if not ok]
    npass = len(checks) - len(fail)
    print(f"\nchecks={len(checks)}  pass={npass}  fail={len(fail)}")
    if fail:
        print("RESULT: FAIL — the operator's hero-select P2 paste blob has drifted "
              "from the pjass-compiled, equivalence-audited authority "
              "(hero_select_p2_loop_data.gen.j):")
        for c, l, d in fail:
            print(f"  - [{c}] {l}: {d}")
        return 1
    print(f"RESULT: GREEN — all {len(checks)} checks hold: the operator's paste blob "
          f"({len(crew_seq)} udg_CastleSlot_* data lines) is byte-identical, line-for-"
          "line and key-for-value, to the pjass-compiled / equivalence-audited "
          "authority. The two INDEPENDENT generators (datatable extract_slot vs the "
          "loop gate's own extract_cam_rect emission) agree, so the dropped-camera-pan "
          "class of regression — a self-consistent paste blob that is collectively "
          "stale vs the compiled authority — can no longer ship unseen.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
