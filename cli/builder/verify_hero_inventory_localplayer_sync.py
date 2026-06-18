#!/usr/bin/env python3
# verify_hero_inventory_localplayer_sync.py
# =============================================================================
# KOTR builder diagnostic (engine claude-p, 2026-06-18) — STANDALONE, READ-ONLY.
#
# Catches a SECOND-ORDER desync that pjass and all 178 fidelity/type/coverage
# gates miss, and that the Phase-6 .md's own desync audit missed:
#
#   The hero-inventory menu bar opens a screen ONLY on the pressing client:
#       function Menu_OnButtonUsed ...
#           call UnitRemoveItem(u,it)            // SYNCED re-seat  (fine)
#           call UnitAddItemToSlotById(u,iid,h)  // SYNCED re-seat  (fine)
#           if GetLocalPlayer() == p then
#               call Menu_OpenScreen(p, u, iid)  // <-- LOCAL ONLY
#           endif
#
#   Menu_OpenScreen -> Bag_Open / Sheet_Open -> IInventory_forHero /
#   IEquipment_forHero, and those getters LAZILY ALLOCATE SYNCED STATE the
#   first time a hero's record is touched:
#       function IInventory_forHero takes unit hero returns integer
#           ...
#           if inv == 0 then
#               set inv = IInventory_create()        // set Inv_alloc=Inv_alloc+1  (SYNCED counter)
#               set Inv_owner[inv] = hero            // SYNCED global array write
#               call SaveInteger(INV_HT, id, 0, inv) // SYNCED hashtable write
#           endif
#
#   A brand-new hero that has NOT yet picked up an item (the only other,
#   unconditional, allocator is the Phase-3 pickup path) and presses the
#   Inventory/Equipment menu button performs that FIRST allocation on the
#   OPENER'S CLIENT ALONE -> Inv_alloc / Eq_alloc / INV_HT / EQ_HT diverge ->
#   the next synced read (a shop add, a save) desyncs.  Exactly the spec's #1
#   risk ("never branch state on GetLocalPlayer"; "equipment bit you before").
#
# RULE THIS TOOL ENFORCES
#   For every lazy-allocating model getter G (auto-detected: a function whose
#   body contains a `<X>_create(` call AND a `Save*(` write under an `if .. == 0`
#   guard), if G is reachable from a menu dispatch that is invoked ONLY inside an
#   `if GetLocalPlayer()` block, then the dispatching trigger handler MUST also
#   call G (or an explicit prealloc helper) UNCONDITIONALLY — outside every
#   GetLocalPlayer gate — so the synced allocation runs on all clients first.
#
#   Current deliverable: NO such unconditional prealloc exists -> EXIT 2 (RED).
#   After Evan applies the one-click fix (STAGED_FOR_EVAN.md) it goes EXIT 0.
#
# This is a standalone diagnostic (like companion_ai_copies.py / pulse_ghost_
# detector.py); it is intentionally NOT wired into verify_all.py, so the
# 178/178 sweep stays GREEN while this RED stands as the hard evidence.
#
#   python3 verify_hero_inventory_localplayer_sync.py            # live deliverable
#   python3 verify_hero_inventory_localplayer_sync.py --selftest # RED/GREEN proof
# READ-ONLY: never writes/edits any .j/.md/.w3x.
# =============================================================================
import os
import re
import sys

FIXSPECS = "/home/mediumunwell/Systems_Migration/kotr/fix_specs"
COMBINED = [
    "hero_inventory_PHASE1_COMBINED.j",
    "hero_inventory_PHASE2_COMBINED.j",
    "hero_inventory_PHASE3_COMBINED.j",
    "hero_inventory_PHASE4_COMBINED.j",
    "hero_inventory_PHASE5_COMBINED.j",
    "hero_inventory_PHASE6_COMBINED.j",
    "hero_inventory_PHASE7_COMBINED.j",
]

FUNC_RE = re.compile(r"^\s*function\s+(\w+)\s+takes\b")
ENDFUNC_RE = re.compile(r"^\s*endfunction\b")
CALL_RE = re.compile(r"\b(\w+)\s*\(")          # any identifier immediately followed by '('
CREATE_RE = re.compile(r"\b(\w+_create)\s*\(")
SAVE_RE = re.compile(r"\bSave\w*\s*\(")
ZEROGUARD_RE = re.compile(r"\bif\b.*==\s*0\b.*\bthen\b")
GLP_OPEN_RE = re.compile(r"\bif\b.*\bGetLocalPlayer\s*\(\s*\)")
IF_RE = re.compile(r"^\s*if\b")
ENDIF_RE = re.compile(r"^\s*endif\b")


def strip_comment(line):
    # JASS line comments start with //. (No block comments in these files.)
    i = line.find("//")
    return line[:i] if i >= 0 else line


def parse_funcs(text):
    """Return {name: [code lines (comment-stripped)]} for every function."""
    funcs = {}
    cur = None
    body = []
    for raw in text.splitlines():
        line = strip_comment(raw)
        m = FUNC_RE.match(line)
        if m:
            cur = m.group(1)
            body = []
            continue
        if cur is not None and ENDFUNC_RE.match(line):
            funcs[cur] = body
            cur = None
            continue
        if cur is not None:
            body.append(line)
    return funcs


def is_lazy_getter(body):
    """True if the body lazily allocates synced state under an `== 0` guard."""
    text = "\n".join(body)
    if not ZEROGUARD_RE.search(text):
        return False
    return bool(CREATE_RE.search(text) and SAVE_RE.search(text))


def calls_in(body):
    """Set of function names called anywhere in a body."""
    names = set()
    for line in body:
        for m in CALL_RE.finditer(line):
            names.add(m.group(1))
    return names


def gated_calls(body):
    """(gated, unconditional) sets of called names, split by GetLocalPlayer nesting.

    A call is 'gated' if it lexically sits inside an `if GetLocalPlayer()...` block.
    Naive if/endif depth tracking is sufficient for this hand-written JASS (no
    one-line if).  We mark the depth at which a GLP gate opened and treat every
    call at >= that depth as gated until the matching endif closes it.
    """
    gated, uncond = set(), set()
    glp_depths = []          # stack of depths where a GLP gate is currently open
    depth = 0
    for line in body:
        opened_glp = bool(IF_RE.match(line) and GLP_OPEN_RE.search(line))
        if IF_RE.match(line):
            depth += 1
            if opened_glp:
                glp_depths.append(depth)
        names = {m.group(1) for m in CALL_RE.finditer(line)}
        names -= {"GetLocalPlayer", "GetTriggerPlayer", "GetTriggerUnit",
                  "GetManipulatedItem", "GetItemTypeId", "GetPlayerId"}
        target = gated if glp_depths else uncond
        target |= names
        if ENDIF_RE.match(line):
            if glp_depths and depth == glp_depths[-1]:
                glp_depths.pop()
            depth -= 1
    return gated, uncond


def reaches(start, funcs, targets, seen=None):
    """True if any function in `targets` is reachable from `start` via calls."""
    if seen is None:
        seen = set()
    if start in seen or start not in funcs:
        return False
    seen.add(start)
    if start in targets:
        return True
    for callee in calls_in(funcs[start]):
        if callee in targets:
            return True
        if reaches(callee, funcs, targets, seen):
            return True
    return False


def audit(funcs):
    """Return (ok, findings[]). ok=True means no gated-only lazy allocation."""
    findings = []
    lazy = {n for n, b in funcs.items() if is_lazy_getter(b)}
    if not lazy:
        findings.append("WARN: no lazy-allocating getter detected — "
                        "model may have changed; re-ground before trusting GREEN.")
        return True, findings
    findings.append("lazy-allocating synced getters: " + ", ".join(sorted(lazy)))

    # Find the menu trigger handler(s) that gate a dispatch behind GetLocalPlayer.
    handlers = [n for n in funcs
                if n.startswith("Menu_On") and GLP_OPEN_RE.search("\n".join(funcs[n]))]
    if not handlers:
        findings.append("WARN: no GetLocalPlayer-gated Menu_On* handler found — "
                        "Phase-6 dispatch shape changed; re-ground.")
        return True, findings

    bad = False
    for h in handlers:
        gated, uncond = gated_calls(funcs[h])
        # Does any gated dispatch transitively reach a lazy getter?
        gated_reaches = sorted(g for g in gated if reaches(g, funcs, lazy))
        if not gated_reaches:
            findings.append(f"{h}: gated calls reach no lazy getter — OK")
            continue
        # Is the lazy allocation forced unconditionally before the gate?
        uncond_prealloc = any(reaches(u, funcs, lazy) or u in lazy for u in uncond)
        if uncond_prealloc:
            findings.append(f"{h}: gated {gated_reaches} reach lazy getter, "
                            f"but an UNCONDITIONAL prealloc is present — OK")
        else:
            bad = True
            findings.append(
                f"{h}: DESYNC — gated dispatch {gated_reaches} reaches lazy "
                f"synced getter ({', '.join(sorted(lazy))}) with NO unconditional "
                f"prealloc before the GetLocalPlayer gate -> first allocation runs "
                f"on the opener's client alone (Inv_alloc/Eq_alloc/INV_HT diverge).")
    return (not bad), findings


def load_live():
    missing = [f for f in COMBINED if not os.path.isfile(os.path.join(FIXSPECS, f))]
    if missing:
        print("ERROR: missing deliverable files: " + ", ".join(missing), file=sys.stderr)
        sys.exit(3)
    text = ""
    for f in COMBINED:
        with open(os.path.join(FIXSPECS, f), encoding="utf-8", errors="replace") as fh:
            text += fh.read() + "\n"
    return text


# --- synthetic fixtures for --selftest ---------------------------------------
_LAZY = """
function IInventory_create takes nothing returns integer
    set Inv_alloc = Inv_alloc + 1
    return Inv_alloc
endfunction
function IInventory_forHero takes unit hero returns integer
    local integer id = GetHandleId(hero)
    local integer inv = LoadInteger(INV_HT, id, 0)
    if inv == 0 then
        set inv = IInventory_create()
        set Inv_owner[inv] = hero
        call SaveInteger(INV_HT, id, 0, inv)
    endif
    return inv
endfunction
function Bag_Open takes player p, unit hero returns nothing
    local integer inv = IInventory_forHero(hero)
    if GetLocalPlayer() != p then
        return
    endif
    call BlzFrameSetVisible(BagMainFrame, true)
endfunction
function Menu_OpenScreen takes player p, unit hero, integer iid returns nothing
    call Bag_Open(p, hero)
endfunction
"""

_BUGGY_HANDLER = """
function Menu_OnButtonUsed takes nothing returns boolean
    local unit u = GetTriggerUnit()
    local item it = GetManipulatedItem()
    local player p = GetTriggerPlayer()
    local integer iid = GetItemTypeId(it)
    call UnitRemoveItem(u, it)
    call UnitAddItemToSlotById(u, iid, 1)
    if GetLocalPlayer() == p then
        call Menu_OpenScreen(p, u, iid)
    endif
    return false
endfunction
"""

_FIXED_HANDLER = """
function Menu_OnButtonUsed takes nothing returns boolean
    local unit u = GetTriggerUnit()
    local item it = GetManipulatedItem()
    local player p = GetTriggerPlayer()
    local integer iid = GetItemTypeId(it)
    call UnitRemoveItem(u, it)
    call UnitAddItemToSlotById(u, iid, 1)
    call IInventory_forHero(u)
    if GetLocalPlayer() == p then
        call Menu_OpenScreen(p, u, iid)
    endif
    return false
endfunction
"""


def selftest():
    fails = 0

    def check(label, text, expect_ok):
        nonlocal fails
        ok, findings = audit(parse_funcs(text))
        status = "PASS" if ok == expect_ok else "FAIL"
        if ok != expect_ok:
            fails += 1
        print(f"  [{status}] {label}: ok={ok} (expected {expect_ok})")
        for fnd in findings:
            print("        - " + fnd)

    print("=== selftest ===")
    check("buggy: gated-only lazy alloc", _LAZY + _BUGGY_HANDLER, expect_ok=False)
    check("fixed: unconditional prealloc", _LAZY + _FIXED_HANDLER, expect_ok=True)
    # negative control: no lazy getter at all -> OK (with WARN)
    check("control: no lazy getter", _BUGGY_HANDLER.replace("Menu_OpenScreen", "Noop"),
          expect_ok=True)
    if fails:
        print(f"SELFTEST FAILED ({fails})")
        return 1
    print("SELFTEST PASS (3/3)")
    return 0


def main():
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    text = load_live()
    ok, findings = audit(parse_funcs(text))
    print("=== hero-inventory GetLocalPlayer / lazy-alloc sync audit ===")
    for f in findings:
        print(" - " + f)
    if ok:
        print("RESULT: GREEN — no gated-only lazy synced allocation. EXIT 0")
        sys.exit(0)
    print("RESULT: RED — latent multiplayer desync (gated-only lazy alloc). EXIT 2")
    print("FIX (one-click, staged for Evan): add an UNCONDITIONAL "
          "`call IInventory_forHero(u)` / `call IEquipment_forHero(u)` in "
          "Menu_OnButtonUsed BEFORE the `if GetLocalPlayer()==p` gate "
          "(mirror in PHASE6 .md + COMBINED.j to keep fidelity green).")
    sys.exit(2)


if __name__ == "__main__":
    main()
