#!/usr/bin/env python3
"""
verify_command_hub_spec_grounding.py — KOTR Hero-Inventory Command Hub, SPEC-GROUNDING gate
============================================================================================
Turns the one-time 2026-06-15 prose grounding (`hero_inventory_VERIFY_grounding_*.md`) of
`hero_inventory_command_hub_SPEC.md`'s "Grounded current-state (v0.50)" block into a
re-runnable executable gate against the live source.

WHY THIS GATE EXISTS (covered by no other gate in the 178/178 sweep):
  The whole 8-phase hero-inventory build (model -> plumbing -> equipment -> save/load ->
  buttons -> errantry) is anchored on a handful of line/count cites in the SPEC. The sweep
  validates paste/runbook/parity — it never re-checks that the SPEC's *grounding anchors*
  still describe the real `war3map.j`. A World-Editor save renumbers JASS, so a single
  intervening save silently invalidates "save loop @ L45466", "shop block @ L41089",
  "CloneItems @ L27380", etc. — and no implementer would notice until they paste into the
  wrong place. This gate fails RED the moment any anchor drifts.

WHAT IT CHECKS (read-only; touches no .w3x):
  source identity   md5 == 967131658fd8d4fb27ee0d7f74e4bd22 , lines == 75535
  (1) talent refs               grep -ic talent              == 3236
  (2) no equipment system       grep -ic equip               == 0
  (3) give-item migration surf. grep -c UnitAddItemToSlotById == 132
  (4) shop block start          L41089 == UnitAddItemToSlotById(u,'whwd',0)
  (5) shop 'srtl' example       L41162 == UnitAddItemToSlotById(u,'srtl',0)
  (6) save-read loop            L45466 reads UnitItemInSlot + KEY_ITEMS, inside Trig_Save_GUI_Actions
  (7) CloneItems disambig       L27380 == 'set k=UnitItemInSlot(source, i)', inside function CloneItems
                                 (i.e. L27380 is NOT the save path)

Run:        python3 verify_command_hub_spec_grounding.py
Self-test:  python3 verify_command_hub_spec_grounding.py --selftest
            (mutates an in-memory copy of the source so each anchor is broken in turn and
             proves every break is caught — RED-catch proof, no live file needed)

EXIT 0 = GREEN (every anchor holds), 1 = a grounding anchor drifted, 2 = source not found,
3 = selftest failed. Standalone by design — NOT wired into verify_all.py, so the canonical
178/178 sweep stays GREEN; this gate is invoked on its own when the SPEC grounding is touched
or after any WE save that re-extracts war3map.j.
"""
import hashlib
import re
import sys
from pathlib import Path

SRC = (Path.home() / ".." / ".." / "mnt" / "c" / "Users" / "Morph" / "OneDrive"
       / "Documents" / "Warcraft III" / "Maps" / "KOTR" / "_extract_v050" / "war3map.j")
# Resolve via the canonical mount path (the OneDrive working copy the sweep cites).
SRC = Path("/mnt/c/Users/Morph/OneDrive/Documents/Warcraft III/Maps/KOTR/_extract_v050/war3map.j")

CANON_MD5 = "967131658fd8d4fb27ee0d7f74e4bd22"
CANON_LINES = 75535


def enclosing_function(lines, lineno):
    """Name of the nearest `function <name>` at/above lineno (handles vJass-indented funcs)."""
    for i in range(lineno - 1, -1, -1):
        m = re.match(r"\s*function\s+(\w+)\b", lines[i])
        if m:
            return m.group(1)
    return None


def audit(text, src_md5=None):
    """Return (rows, failures). rows=[(id, claim, observed, ok)].
    `src_md5` is the md5 of the RAW BYTES of the source (computed by the caller, since text
    has been newline-decoded and would not match `md5sum`). Pass None to skip the md5 anchor
    (selftest path — synthetic content has no canonical hash)."""
    lines = text.split("\n")          # lines[0] == file line 1
    low_lines = [ln.lower() for ln in lines]
    rows, failures = [], []

    def check(cid, claim, observed, ok):
        rows.append((cid, claim, observed, ok))
        if not ok:
            failures.append(f"{cid}: {claim} -> observed {observed!r}")

    def L(n):                          # 1-based file line
        return lines[n - 1] if 0 < n <= len(lines) else "<EOF>"

    def grep_ic(substr):               # mimic `grep -ic`: count of matching LINES, case-insens.
        s = substr.lower()
        return sum(1 for ln in low_lines if s in ln)

    def grep_c(substr):                # mimic `grep -c`: count of matching LINES, case-sensitive.
        return sum(1 for ln in lines if substr in ln)

    if src_md5 is not None:
        check("src.md5", f"md5=={CANON_MD5}", src_md5, src_md5 == CANON_MD5)
    # newline-terminated file => split yields one trailing '' element
    nlines = len(lines) - 1 if lines and lines[-1] == "" else len(lines)
    check("src.lines", f"lines=={CANON_LINES}", nlines, nlines == CANON_LINES)

    talent = grep_ic("talent")
    check("1.talent", "talent refs==3236", talent, talent == 3236)

    equip = grep_ic("equip")
    check("2.equip", "equip hits==0", equip, equip == 0)

    give = grep_c("UnitAddItemToSlotById")
    check("3.giveitems", "UnitAddItemToSlotById==132", give, give == 132)

    l41089 = L(41089).strip()
    check("4.shopstart", "L41089 shop block 'whwd'", l41089,
          "UnitAddItemToSlotById(u, 'whwd', 0)" in l41089)

    l41162 = L(41162).strip()
    check("5.shopsrtl", "L41162 shop 'srtl'", l41162,
          "UnitAddItemToSlotById(u, 'srtl', 0)" in l41162)

    l45466 = L(45466)
    save_ok = ("UnitItemInSlot" in l45466 and "KEY_ITEMS" in l45466
               and enclosing_function(lines, 45466) == "Trig_Save_GUI_Actions")
    check("6.saveloop", "L45466 save-read in Trig_Save_GUI_Actions",
          f"{l45466.strip()[:60]}... fn={enclosing_function(lines, 45466)}", save_ok)

    l27380 = L(27380).strip()
    clone_ok = (l27380 == "set k=UnitItemInSlot(source, i)"
                and enclosing_function(lines, 27380) == "CloneItems")
    check("7.cloneitems", "L27380 is CloneItems (NOT save path)",
          f"{l27380} fn={enclosing_function(lines, 27380)}", clone_ok)

    return rows, failures


def report(rows):
    print(f"{'ANCHOR':<14}{'OK?':<6}OBSERVED")
    for cid, _claim, observed, ok in rows:
        print(f"{cid:<14}{'OK' if ok else 'XXXX':<6}{observed}")


def selftest():
    print("=== SELFTEST: mutate each anchor in turn, prove every break is caught ===")
    # Synthetic source that PASSES every CONTENT anchor (md5 skipped — synthetic has no
    # canonical hash). grep -ic/-c are LINE counts, so each anchor occupies whole lines.
    base = ["x"] * CANON_LINES
    base[41089 - 1] = "    call UnitAddItemToSlotById(u, 'whwd', 0)"
    base[41162 - 1] = "    call UnitAddItemToSlotById(u, 'srtl', 0)"
    base[45424 - 1] = "function Trig_Save_GUI_Actions takes nothing returns nothing"
    base[45466 - 1] = "set v=LoadInteger(h, KEY_ITEMS, GetItemTypeId(UnitItemInSlot(u, i)))"
    base[27373 - 1] = "    function CloneItems takes unit source,unit target returns nothing"
    base[27380 - 1] = "set k=UnitItemInSlot(source, i)"
    # exact grep -ic/-c LINE counts, OVERWRITTEN IN PLACE so the synthetic stays CANON_LINES
    # long (keeps the src.lines anchor green). 3236 lines containing 'talent'; the 2 shop
    # lines above already contain UnitAddItemToSlotById, so 130 more give lines -> 132.
    TALENT0 = 100                                    # 0-based; clear of all 6 placed anchors
    for i in range(TALENT0, TALENT0 + 3236):
        base[i] = "talent"
    GIVE0 = 50000                                    # 0-based; clear of anchors + talent block
    for i in range(GIVE0, GIVE0 + (132 - 2)):
        base[i] = "UnitAddItemToSlotById"
    text = "\n".join(base) + "\n"

    rows, failures = audit(text, src_md5=None)       # md5 skipped on synthetic
    clean_content_ok = (len(failures) == 0)
    print(f"  clean synthetic: ALL content anchors GREEN? {clean_content_ok}")
    if not clean_content_ok:
        for f in failures:
            print("   - unexpected:", f)

    caught = {}
    breaks = {
        "1.talent": (TALENT0 + 1, "nota_t4l3nt_line"),   # 3236 -> 3235
        "3.giveitems": (GIVE0 + 1, "notacall"),          # 132 -> 131
        "4.shopstart": (41089, "    call X"),
        "5.shopsrtl": (41162, "    call X"),
        "6.saveloop": (45466, "set v=0  // gutted"),
        "7.cloneitems": (27380, "set k=0  // gutted"),
    }
    for cid, (ln, repl) in breaks.items():
        mut = list(base)
        mut[ln - 1] = repl
        _rows, fails = audit("\n".join(mut) + "\n", src_md5=None)
        caught[cid] = any(f.startswith(cid + ":") for f in fails)
        print(f"  break {cid:<13} @L{ln:<6} -> caught? {caught[cid]}")

    ok = clean_content_ok and all(caught.values())
    print(f"\nSELFTEST {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 3


def main():
    if "--selftest" in sys.argv:
        return selftest()
    if not SRC.exists():
        print(f"FATAL: live source not found: {SRC}")
        return 2
    raw = SRC.read_bytes()                               # md5 must match `md5sum` (raw bytes)
    src_md5 = hashlib.md5(raw).hexdigest()
    text = raw.decode("utf-8", "surrogatepass").replace("\r\n", "\n")  # CRLF -> LF for content
    rows, failures = audit(text, src_md5=src_md5)
    report(rows)
    print(f"\nsource: {SRC}")
    if failures:
        print(f"\nRESULT: FAIL — {len(failures)} SPEC-grounding anchor(s) drifted:")
        for f in failures:
            print("  -", f)
        print("Re-ground the SPEC against the current war3map.j before any implementer builds on it.")
        return 1
    print("\nRESULT: GREEN — all 9 hero-inventory SPEC grounding anchors hold verbatim "
          f"vs live source (md5 {CANON_MD5}, {CANON_LINES} lines).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
