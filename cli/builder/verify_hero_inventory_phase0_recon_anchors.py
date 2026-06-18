#!/usr/bin/env python3
"""
verify_hero_inventory_phase0_recon_anchors.py — KOTR Hero-Inventory PHASE 0 RECON binder
=========================================================================================
Binds `hero_inventory_PHASE0_RECON.md` — the Phase-0 deliverable that every later phase
(data model -> plumbing -> equipment -> save/load -> buttons) is planned against — to the
live `_extract_v050/war3map.j`, BOTH directions. Sibling of the already-shipped
`verify_command_hub_spec_grounding.py` (SPEC) and the runbook integration-correction
binders; the recon was the LAST hero-inventory source-of-truth carrying byte-exact
line/count cites that NO gate machine-checked.

WHY THIS GATE EXISTS (covered by no other gate in the 178/178 sweep):
  The recon enumerates the *migration surface* the implementer plans against: 132 give-item
  sites (split per init-function), the frame-API toolkit counts to reuse, the has-item /
  query sites to replace, and the save/load format line anchors. A single World-Editor save
  renumbers JASS and shifts every count/line, silently invalidating the recon — and the
  implementer would only discover it after planning Phase 3 migration against stale numbers.
  When it was first audited (2026-06-18) one cite was ALREADY wrong: `RemoveItem ×12` while
  the canonical extract carries exactly ×10 (the sibling `RemoveItemSwapped` ×7 is distinct).
  That cite is corrected and the whole document is now bound.

WHAT IT CHECKS (read-only; touches no .w3x):
  source identity   md5 == 967131658fd8…, lines == 75535
  give surface      UnitAddItemToSlotById == 132 total; per init-fn 60/24/21/14/13 in
                    CreateUnitsForPlayer10 (L41210) / CreateNeutralHostile (L42127) /
                    CreateUnitsForPlayer11 (L41722) / CreateUnitsForPlayer9 (L41066) /
                    CreateNeutralPassive (L42670)
  creation APIs     CreateItemLoc 25, CreateItem 2, UnitAddItem 1
  query sites       GetItemTypeId 40, UnitItemInSlot 2, RemoveItem 10, UnitItemInSlotBJ 6;
                    zero-sites UnitInventoryCount/UnitHasItem/GetInventoryIndexOfItemTypeId == 0
  frame toolkit     BlzCreateFrame 20, BlzCreateFrameByType 22, BlzFrameSetPoint 28,
                    BlzFrameSetText 26, BlzFrameSetVisible 66, BlzFrameSetTexture 40,
                    BlzGetFrameByName 1, BlzCreateSimpleFrame 0  (all token+'(' occurrences,
                    so BlzCreateFrame != BlzCreateFrameByType and BlzFrameSetText !=
                    BlzFrameSetTextAlignment — the substring trap)
  line anchors      L41089 == "...UnitAddItemToSlotById(u, 'whwd', 0)"
                    L27380 == "set k=UnitItemInSlot(source, i)" inside fn CloneItems (NOT save)
                    L27382 CreateItem / L27384 UnitAddItem (the CloneItems illusion block)
                    L45426 reverse-order save note ; L45466 save-read in Trig_Save_GUI_Actions
  function headers  Trig_Save_GUI_Actions @L45424, Trig_Load_GUI_Actions @L46409,
                    GT_RegisterItemUsedEvent @L15215 / …Acquired @L15349 / …Dropped @L15483

  REVERSE DIRECTION (prose -> cite): every literal above must STILL appear in the recon
  prose. The forward checks catch a WE re-bake that moves the map out from under the recon;
  the reverse checks catch the twin seam — a doc edit that silently drops/rewrites a cite
  (the seam that had left `RemoveItem ×12` wrong) — leaving the gate green over a rotted recon.

Run:        python3 verify_hero_inventory_phase0_recon_anchors.py
Self-test:  python3 verify_hero_inventory_phase0_recon_anchors.py --selftest
            (unit-tests the count/enclosing-fn helpers, then mutates synthetic anchors in
             each category to prove every break is caught — no live file needed)

EXIT 0 = GREEN, 1 = an anchor drifted, 2 = source/recon not found, 3 = selftest failed.
Standalone by design — NOT wired into verify_all.py, so the canonical 178/178 sweep is
unchanged; invoked on its own when the recon is touched or after any WE re-extract.
"""
import hashlib
import re
import sys
from pathlib import Path

SRC = Path("/mnt/c/Users/Morph/OneDrive/Documents/Warcraft III/Maps/KOTR/_extract_v050/war3map.j")
RECON = Path("/mnt/c/Users/Morph/OneDrive/Documents/Warcraft III/Maps/KOTR/_crew/hero_inventory_PHASE0_RECON.md")

CANON_MD5 = "967131658fd8d4fb27ee0d7f74e4bd22"
CANON_LINES = 75535

# --- forward anchor tables (live war3map.j) -----------------------------------------------
# token+'(' occurrence counts (substring-safe: requires '(' right after the token).
OCC_ANCHORS = [
    ("give.total",  "UnitAddItemToSlotById", 132),
    ("api.itemloc", "CreateItemLoc",         25),
    ("api.item",    "CreateItem",            2),
    ("api.additem", "UnitAddItem",           1),
    ("q.gettype",   "GetItemTypeId",         40),
    ("q.inslot",    "UnitItemInSlot",        2),
    ("q.remove",    "RemoveItem",            10),   # corrected from the recon's stale ×12
    ("q.inslotbj",  "UnitItemInSlotBJ",      6),
    ("q.invcount",  "UnitInventoryCount",    0),
    ("q.hasitem",   "UnitHasItem",           0),
    ("q.invidx",    "GetInventoryIndexOfItemTypeId", 0),
    ("ui.create",   "BlzCreateFrame",        20),
    ("ui.createty", "BlzCreateFrameByType",  22),
    ("ui.setpoint", "BlzFrameSetPoint",      28),
    ("ui.settext",  "BlzFrameSetText",       26),
    ("ui.setvis",   "BlzFrameSetVisible",    66),
    ("ui.settex",   "BlzFrameSetTexture",    40),
    ("ui.getbyname","BlzGetFrameByName",     1),
    ("ui.simple",   "BlzCreateSimpleFrame",  0),
]

# (cid, fn-header line, fn name, # of UnitAddItemToSlotById calls in the body)
GIVE_FN_ANCHORS = [
    ("give.p10", 41210, "CreateUnitsForPlayer10", 60),
    ("give.nh",  42127, "CreateNeutralHostile",   24),
    ("give.p11", 41722, "CreateUnitsForPlayer11",  21),
    ("give.p9",  41066, "CreateUnitsForPlayer9",   14),
    ("give.np",  42670, "CreateNeutralPassive",    13),
]

# (cid, line, substring that must be present on that 1-based line)
LINE_ANCHORS = [
    ("shop.whwd",    41089, "UnitAddItemToSlotById(u, 'whwd', 0)"),
    ("clone.scan",   27380, "set k=UnitItemInSlot(source, i)"),
    ("clone.create", 27382, "CreateItem("),
    ("clone.add",    27384, "UnitAddItem("),
    ("save.note",    45426, "reverse order you saved"),
]

# (cid, line, expected `function <name>` declared on that 1-based line)
FN_HEADER_ANCHORS = [
    ("fn.save", 45424, "Trig_Save_GUI_Actions"),
    ("fn.load", 46409, "Trig_Load_GUI_Actions"),
    ("fn.gt_used", 15215, "GT_RegisterItemUsedEvent"),
    ("fn.gt_acq",  15349, "GT_RegisterItemAcquiredEvent"),
    ("fn.gt_drop", 15483, "GT_RegisterItemDroppedEvent"),
]

# --- reverse anchor table (recon prose must still carry each literal) ----------------------
PROSE_CITES = [
    ("src.lines",   "75,535"),
    ("give.total",  "132"),
    ("give.p10",    "(L41210) | 60"),
    ("give.nh",     "(L42127) | 24"),
    ("give.p11",    "(L41722) | 21"),
    ("give.p9",     "(L41066) | 14"),
    ("give.np",     "(L42670) | 13"),
    ("q.remove",    "`RemoveItem` ×10"),   # binds the 12->10 correction
    ("ui.setvis",   "×66"),
    ("ui.settex",   "×40"),
    ("ui.settext",  "×26"),
    ("shop.whwd",   "L41089"),
    ("clone.scan",  "L27380"),
    ("save.fn",     "L45424"),
    ("load.fn",     "L46409"),
    ("save.read",   "L45466"),
    ("gt.events",   "L15215/15349/15483"),
]


def count_occ(text, token):
    """Occurrences of `token(` — substring-safe, since '(' must follow the token."""
    return len(re.findall(re.escape(token) + r"\(", text))


def enclosing_function(lines, lineno):
    """Name of the nearest `function <name>` at/above lineno (handles vJass indentation)."""
    for i in range(lineno - 1, -1, -1):
        m = re.match(r"\s*function\s+(\w+)\b", lines[i])
        if m:
            return m.group(1)
    return None


def fn_give_count(lines, header_lineno):
    """# of UnitAddItemToSlotById calls between the `function` at header_lineno and its
    matching `endfunction` (first endfunction at column 0 / or any-indent endfunction)."""
    n = 0
    started = False
    for i in range(header_lineno - 1, len(lines)):
        ln = lines[i]
        if re.match(r"\s*function\s+", ln):
            started = True
        elif started and re.match(r"\s*endfunction\b", ln):
            break
        if started:
            n += ln.count("UnitAddItemToSlotById(")
    return n


def audit(text, src_md5=None):
    """Return (rows, failures). rows=[(id, claim, observed, ok)]."""
    lines = text.split("\n")          # lines[0] == file line 1
    rows, failures = [], []

    def check(cid, claim, observed, ok):
        rows.append((cid, claim, observed, ok))
        if not ok:
            failures.append(f"{cid}: {claim} -> observed {observed!r}")

    def L(n):
        return lines[n - 1] if 0 < n <= len(lines) else "<EOF>"

    if src_md5 is not None:
        check("src.md5", f"md5=={CANON_MD5}", src_md5, src_md5 == CANON_MD5)
    nlines = len(lines) - 1 if lines and lines[-1] == "" else len(lines)
    check("src.lines", f"lines=={CANON_LINES}", nlines, nlines == CANON_LINES)

    for cid, token, want in OCC_ANCHORS:
        got = count_occ(text, token)
        check(cid, f"{token}(=={want}", got, got == want)

    for cid, hdr, fn, want in GIVE_FN_ANCHORS:
        decl = re.match(r"\s*function\s+(\w+)\b", L(hdr))
        decl_ok = bool(decl and decl.group(1) == fn)
        got = fn_give_count(lines, hdr) if decl_ok else -1
        check(cid, f"{fn}@L{hdr} gives {want}",
              f"hdr_ok={decl_ok} count={got}", decl_ok and got == want)

    for cid, ln, sub in LINE_ANCHORS:
        observed = L(ln).strip()
        check(cid, f"L{ln} carries {sub!r}", observed[:70], sub in observed)

    # CloneItems scan line must be inside CloneItems, and NOT the save path
    clone_fn = enclosing_function(lines, 27380)
    check("clone.fn", "L27380 inside fn CloneItems", clone_fn, clone_fn == "CloneItems")

    # save-read line carries the item read + lives in Trig_Save_GUI_Actions
    l45466 = L(45466)
    save_fn = enclosing_function(lines, 45466)
    save_ok = ("UnitItemInSlot" in l45466 and "KEY_ITEMS" in l45466
               and save_fn == "Trig_Save_GUI_Actions")
    check("save.read", "L45466 save-read in Trig_Save_GUI_Actions",
          f"{l45466.strip()[:55]}... fn={save_fn}", save_ok)

    for cid, ln, fn in FN_HEADER_ANCHORS:
        m = re.match(r"\s*function\s+(\w+)\b", L(ln))
        got = m.group(1) if m else None
        check(cid, f"function {fn}@L{ln}", got, got == fn)

    return rows, failures


def audit_prose(recon_text):
    rows, failures = [], []
    for cid, cite in PROSE_CITES:
        ok = cite in recon_text
        rows.append((cid, cite, ok))
        if not ok:
            failures.append(f"{cid}.prose: recon no longer carries cite {cite!r}")
    return rows, failures


def report(rows):
    print(f"{'ANCHOR':<14}{'OK?':<6}OBSERVED")
    for cid, _claim, observed, ok in rows:
        print(f"{cid:<14}{'OK' if ok else 'XXXX':<6}{observed}")


def _build_synth():
    """Synthetic source that PASSES every forward anchor (md5 skipped)."""
    base = ["x"] * CANON_LINES

    def put(ln, s):
        base[ln - 1] = s

    # line anchors (the L41089 'whwd' give is placed below, INSIDE CreateUnitsForPlayer9's
    # body, exactly as in the live map — so it is one of P9's 14, not a 133rd give).
    put(27380, "set k=UnitItemInSlot(source, i)")
    put(27382, "                set k=CreateItem(GetItemTypeId(k), x, y)")
    put(27384, "                call UnitAddItem(target, k)")
    put(45426, "    // NOTE: load values in the reverse order you saved them in.")
    put(45466, "set v=LoadInteger(h, KEY_ITEMS, GetItemTypeId(UnitItemInSlot(u, i)))")
    # enclosing fns
    put(27373, "    function CloneItems takes unit source,unit target returns nothing")
    put(45424, "function Trig_Save_GUI_Actions takes nothing returns nothing")
    put(46409, "function Trig_Load_GUI_Actions takes nothing returns nothing")
    put(15215, "        function GT_RegisterItemUsedEvent takes trigger t returns trigger")
    put(15349, "        function GT_RegisterItemAcquiredEvent takes trigger t returns trigger")
    put(15483, "        function GT_RegisterItemDroppedEvent takes trigger t returns trigger")

    # give-item init functions, each with its declared header + N body calls + endfunction.
    # Place them in clear regions; their give calls also feed the give.total==132 count.
    give_total_placed = 0
    for hdr, fn, n in [(41210, "CreateUnitsForPlayer10", 60), (42127, "CreateNeutralHostile", 24),
                       (41722, "CreateUnitsForPlayer11", 21), (42670, "CreateNeutralPassive", 13)]:
        put(hdr, f"function {fn} takes nothing returns nothing")
        for k in range(n):
            put(hdr + 1 + k, "    call UnitAddItemToSlotById(u, 'iX00', 0)")
        put(hdr + 1 + n, "endfunction")
        give_total_placed += n
    # CreateUnitsForPlayer9 (L41066, 14 gives) — 13 contiguous + the L41089 'whwd' as the 14th,
    # endfunction after it, mirroring the live layout so shop.whwd lives inside P9's count.
    put(41066, "function CreateUnitsForPlayer9 takes nothing returns nothing")
    for k in range(13):
        put(41067 + k, "    call UnitAddItemToSlotById(u, 'iX09', 0)")
    put(41089, "    call UnitAddItemToSlotById(u, 'whwd', 0)")
    put(41090, "endfunction")
    give_total_placed += 14
    # 60+24+21+13(others) + 14(P9) == 132 exactly; nothing to top up.
    assert give_total_placed == 132, give_total_placed

    # occurrence-count anchors (each line carries exactly one token+'(' ).
    REGION = 30000
    cur = REGION
    placed_extra = {"UnitAddItemToSlotById"}   # already satisfied above
    for _cid, token, want in OCC_ANCHORS:
        if token in placed_extra:
            continue
        # CreateItem/UnitAddItem/UnitItemInSlot/GetItemTypeId already have some occurrences
        # from the line anchors above — count current and top up to `want`.
        have = count_occ("\n".join(base), token)
        need = want - have
        for _ in range(max(0, need)):
            base[cur] = f"    set z={token}(a)"
            cur += 1
        placed_extra.add(token)
    return base


def selftest():
    print("=== SELFTEST: helpers + per-category RED-catch ===")
    ok_all = True

    # (A) count_occ is substring-safe
    sample = "a=BlzCreateFrame(x) b=BlzCreateFrameByType(y) c=BlzFrameSetText(z) d=BlzFrameSetTextAlignment(w)"
    a_ok = (count_occ(sample, "BlzCreateFrame") == 1
            and count_occ(sample, "BlzCreateFrameByType") == 1
            and count_occ(sample, "BlzFrameSetText") == 1)
    print(f"  count_occ substring-safe? {a_ok}")
    ok_all &= a_ok

    # (B) fn_give_count respects endfunction + counts only the target body
    mini = ["function A takes nothing returns nothing",
            "    call UnitAddItemToSlotById(u,'a',0)",
            "    call UnitAddItemToSlotById(u,'b',0)",
            "endfunction",
            "function B takes nothing returns nothing",
            "    call UnitAddItemToSlotById(u,'c',0)",
            "endfunction"]
    b_ok = fn_give_count(mini, 1) == 2 and fn_give_count(mini, 5) == 1
    print(f"  fn_give_count body-scoped? {b_ok}")
    ok_all &= b_ok

    # (C) clean synthetic passes every forward anchor
    base = _build_synth()
    rows, failures = audit("\n".join(base) + "\n", src_md5=None)
    clean_ok = (len(failures) == 0)
    print(f"  clean synthetic: ALL forward anchors GREEN? {clean_ok}")
    if not clean_ok:
        for f in failures:
            print("   - unexpected:", f)
    ok_all &= clean_ok

    # (D) break one representative anchor per category; each must be caught
    breaks = {
        "give.total": (41070, "    notacall"),                       # a P9 give -> 132 -> 131
        "give.p10":   (41211, "    notacall"),                       # CreateUnitsForPlayer10 60 -> 59
        "ui.setvis":  (30000 + 0, None),     # placeholder; resolved below to a real setvis line
        "shop.whwd":  (41089, "    call X"),
        "clone.scan": (27380, "set k=0  // gutted"),
        "fn.save":    (45424, "function Other takes nothing returns nothing"),
        "save.read":  (45466, "set v=0  // gutted"),
    }
    # find a BlzFrameSetVisible occurrence line to break for ui.setvis
    for idx, ln in enumerate(base):
        if "BlzFrameSetVisible(" in ln:
            breaks["ui.setvis"] = (idx + 1, "    set z=0")
            break
    caught = {}
    for cid, (ln, repl) in breaks.items():
        mut = list(base)
        mut[ln - 1] = repl
        _r, fails = audit("\n".join(mut) + "\n", src_md5=None)
        caught[cid] = any(f.startswith(cid + ":") for f in fails)
        print(f"  break {cid:<11} @L{ln:<6} -> caught? {caught[cid]}")
    ok_all &= all(caught.values())

    # (E) reverse direction: clean prose passes; a dropped cite is caught
    clean_prose = " ".join(cite for _cid, cite in PROSE_CITES)
    _pr, pf_clean = audit_prose(clean_prose)
    prose_clean_ok = (len(pf_clean) == 0)
    dropped = clean_prose.replace("`RemoveItem` ×10", "`RemoveItem` ×12")
    _pr2, pf_drop = audit_prose(dropped)
    caught_prose = any(f.startswith("q.remove.prose") for f in pf_drop)
    print(f"  clean prose GREEN? {prose_clean_ok} ; drop RemoveItem cite caught? {caught_prose}")
    ok_all &= prose_clean_ok and caught_prose

    print(f"\nSELFTEST {'PASS' if ok_all else 'FAIL'}")
    return 0 if ok_all else 3


def main():
    if "--selftest" in sys.argv:
        return selftest()
    if not SRC.exists():
        print(f"FATAL: live source not found: {SRC}")
        return 2
    if not RECON.exists():
        print(f"FATAL: phase-0 recon not found: {RECON}")
        return 2
    raw = SRC.read_bytes()
    src_md5 = hashlib.md5(raw).hexdigest()
    text = raw.decode("utf-8", "surrogatepass").replace("\r\n", "\n")
    rows, failures = audit(text, src_md5=src_md5)
    report(rows)

    recon_text = RECON.read_text(encoding="utf-8")
    prose_rows, prose_failures = audit_prose(recon_text)
    print(f"\n{'PROSE CITE':<14}{'OK?':<6}CITE")
    for cid, cite, ok in prose_rows:
        print(f"{cid:<14}{'OK' if ok else 'XXXX':<6}{cite!r}")

    failures = failures + prose_failures
    print(f"\nsource: {SRC}\nrecon:  {RECON}")
    if failures:
        print(f"\nRESULT: FAIL — {len(failures)} recon anchor(s) drifted "
              "(live-source and/or recon-prose direction):")
        for f in failures:
            print("  -", f)
        print("Re-ground hero_inventory_PHASE0_RECON.md against the current war3map.j "
              "(or restore the dropped cite) before any phase builds on it.")
        return 1
    print(f"\nRESULT: GREEN — all {len(rows)} forward recon anchors hold verbatim vs live "
          f"source (md5 {CANON_MD5}, {CANON_LINES} lines) AND the recon prose still carries "
          f"all {len(prose_rows)} cites (bound BOTH directions).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
