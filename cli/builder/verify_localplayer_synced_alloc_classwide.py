#!/usr/bin/env python3
# verify_localplayer_synced_alloc_classwide.py
# =============================================================================
# KOTR builder diagnostic (engine claude-p, 2026-06-18) — STANDALONE, READ-ONLY.
#
# COMPLETENESS / BLAST-RADIUS audit for the Phase-6 desync found 2026-06-18:
#   "lazy synced-MODEL allocation reachable ONLY behind a GetLocalPlayer gate"
#   (see verify_hero_inventory_localplayer_sync.py + STAGED_FOR_EVAN.md).
#
# That prior detector proved the bug exists and is the SOLE such site WITHIN the
# 7 hero-inventory phases.  The open question it left unanswered:
#
#     Does the SAME desync class lurk in ANY OTHER shippable track
#     (B1..B11, companion_ai, desync2_localization, leak_camera, hero_select_p2)?
#     If so, those tracks need the same unconditional-prealloc fix too.
#
# This audit answers it with hard evidence by re-applying the *already-trusted*
# reachability rule (imported verbatim from the prior detector — no re-derivation)
# to EVERY shippable program, not just hero-inventory:
#
#   1. lazy synced-MODEL getter  := a function whose body contains `<X>_create(`
#      AND `Save*(` under an `if .. == 0` guard (the IInventory/IEquipment shape).
#   2. a track is RED iff some GetLocalPlayer-gated dispatch transitively reaches
#      such a getter with NO unconditional prealloc before the gate.
#
# RESULT (live, 2026-06-18):
#   * hero_inventory (7 phases linked) -> RED at Menu_OnButtonUsed  (== the
#     already-staged fix; reproduces the prior detector exactly).
#   * EVERY other shippable track -> GREEN: they contain NO lazy synced-model
#     getter at all (so the class cannot exist there).  The only other real
#     GetLocalPlayer code in the whole set is desync2_localization's two file-read
#     gates, which read into a LOCAL string + BlzSendSyncData (textbook-correct),
#     and PHASE1's SHOW_WEAPON_FX, an `effect` handle written/read ONLY inside
#     GLP gates and never touched by synced logic (the documented local-cosmetic
#     idiom — NOT a synced-model getter, so correctly out of class).
#
#   => The Phase-6 Menu_OnButtonUsed site is the ONE-AND-ONLY instance of this
#      desync class in the entire 36-file shippable set.  The staged one-click fix
#      is complete; no other track needs the prealloc treatment.
#
# This is a deliverable completeness audit, NOT a new pjass micro-gate; like its
# siblings (companion_ai_copies.py / pulse_ghost_detector.py /
# verify_hero_inventory_localplayer_sync.py) it is intentionally NOT wired into
# verify_all.py, so the 178/178 sweep stays GREEN.  It exits 2 (RED) live purely
# because hero-inventory's staged-but-not-yet-applied fix is still pending — i.e.
# it tracks the SAME open item, now proven class-wide.
#
#   python3 verify_localplayer_synced_alloc_classwide.py            # live
#   python3 verify_localplayer_synced_alloc_classwide.py --selftest # RED/GREEN proof
# READ-ONLY: never writes/edits any .j/.md/.w3x.
# =============================================================================
import glob
import os
import sys

# Reuse the trusted, self-tested detection core verbatim (no re-derivation).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from verify_hero_inventory_localplayer_sync import (  # noqa: E402
    audit,
    parse_funcs,
    is_lazy_getter,
)

FIXSPECS = "/home/mediumunwell/Systems_Migration/kotr/fix_specs"

# Hero-inventory is one program spread across 7 phases — it MUST be linked so
# cross-phase reachability (Menu_OnButtonUsed -> Menu_OpenScreen -> IInventory_
# forHero) resolves.  Every other track is self-contained in its shippable paste.
HERO_PHASES = [
    "hero_inventory_PHASE1_COMBINED.j",
    "hero_inventory_PHASE2_COMBINED.j",
    "hero_inventory_PHASE3_COMBINED.j",
    "hero_inventory_PHASE4_COMBINED.j",
    "hero_inventory_PHASE5_COMBINED.j",
    "hero_inventory_PHASE6_COMBINED.j",
    "hero_inventory_PHASE7_COMBINED.j",
]


def _read_many(names):
    text = ""
    for n in names:
        p = os.path.join(FIXSPECS, n)
        if not os.path.isfile(p):
            print(f"ERROR: missing deliverable file: {n}", file=sys.stderr)
            sys.exit(3)
        with open(p, encoding="utf-8", errors="replace") as fh:
            text += fh.read() + "\n"
    return text


def _discover_other_tracks():
    """Every shippable .j that is NOT a hero-inventory phase and NOT a *_stub.j.

    Stubs are harness scaffolding (native/global decls for the pjass gate), never
    pasted into the map, so they are out of scope for a deliverable audit.
    """
    out = []
    for p in sorted(glob.glob(os.path.join(FIXSPECS, "*.j"))):
        base = os.path.basename(p)
        if base.startswith("hero_inventory_PHASE"):
            continue
        if base.endswith("_stub.j"):
            continue
        out.append(base)
    return out


def _audit_one(label, text):
    """Return (ok, has_getter, findings)."""
    funcs = parse_funcs(text)
    has_getter = any(is_lazy_getter(b) for b in funcs.values())
    ok, findings = audit(funcs)
    return ok, has_getter, findings


def run_live():
    print("=== class-wide GetLocalPlayer / lazy synced-alloc completeness audit ===")
    any_red = False

    # 1) hero-inventory, fully linked
    ok, has_getter, findings = _audit_one("hero_inventory(7 phases)", _read_many(HERO_PHASES))
    tag = "GREEN" if ok else "RED"
    if not ok:
        any_red = True
    print(f"\n[{tag}] hero_inventory (7 phases linked) — getter_present={has_getter}")
    for f in findings:
        print("        - " + f)

    # 2) every other shippable track, each self-contained
    others = _discover_other_tracks()
    print(f"\n--- {len(others)} other shippable tracks (each scanned for the class) ---")
    red_others = []
    getter_others = []
    for base in others:
        ok, has_getter, findings = _audit_one(base, _read_many([base]))
        if not ok:
            red_others.append(base)
            any_red = True
        if has_getter:
            getter_others.append(base)
        flag = "" if ok else "  <-- RED"
        g = "  [has lazy getter]" if has_getter else ""
        print(f"   {'GREEN' if ok else 'RED  '}  {base}{g}{flag}")

    print("\n=== verdict ===")
    print(f"  other tracks containing a lazy synced-MODEL getter: "
          f"{getter_others if getter_others else 'NONE'}")
    print(f"  other tracks RED (gated-only lazy alloc):          "
          f"{red_others if red_others else 'NONE'}")
    if not getter_others and not red_others:
        print("  => CONTAINED: hero-inventory Menu_OnButtonUsed is the SOLE instance "
              "of this desync class in the entire shippable set.")
    else:
        print("  => NOT CONTAINED: a sibling instance exists outside hero-inventory "
              "(see RED tracks above) — needs the same unconditional-prealloc fix.")

    if any_red:
        # RED live == hero-inventory's staged-but-unapplied fix is still pending.
        print("\nRESULT: RED (EXIT 2) — the staged hero-inventory prealloc fix is not yet "
              "applied; all OTHER tracks are clean. Goes GREEN once Evan applies it.")
        return 2
    print("\nRESULT: GREEN (EXIT 0) — no gated-only lazy synced allocation anywhere.")
    return 0


# --- selftest: prove the class-wide sweep flags a FOREIGN-track instance ------
_LAZY_GETTER = """
function Foo_create takes nothing returns integer
    set Foo_alloc = Foo_alloc + 1
    return Foo_alloc
endfunction
function Foo_forHero takes unit hero returns integer
    local integer id = GetHandleId(hero)
    local integer x = LoadInteger(FOO_HT, id, 0)
    if x == 0 then
        set x = Foo_create()
        set Foo_owner[x] = hero
        call SaveInteger(FOO_HT, id, 0, x)
    endif
    return x
endfunction
function Foo_Open takes player p, unit hero returns nothing
    local integer x = Foo_forHero(hero)
    if GetLocalPlayer() != p then
        return
    endif
    call BlzFrameSetVisible(FooFrame, true)
endfunction
function Foo_Screen takes player p, unit hero returns nothing
    call Foo_Open(p, hero)
endfunction
"""

# A foreign (non-hero) track handler with the gated-only lazy-alloc bug.
_BUGGY_FOREIGN = """
function SomeOtherTrack_OnUsed takes nothing returns boolean
    local unit u = GetTriggerUnit()
    local player p = GetTriggerPlayer()
    call UnitRemoveItem(u, GetManipulatedItem())
    if GetLocalPlayer() == p then
        call Foo_Screen(p, u)
    endif
    return false
endfunction
"""

# The real benign cases that must STAY green:
#  (a) effect handle written/read only inside GLP gates (PHASE1 SHOW_WEAPON_FX).
#  (b) local file-read + BlzSendSyncData (desync2_localization).
_BENIGN_EFFECT = """
function Spike_OpenArmory takes player p returns nothing
    local integer pid = GetPlayerId(p)
    if GetLocalPlayer() == p and SHOW_WEAPON_FX[pid] == null then
        set SHOW_WEAPON_FX[pid] = AddSpecialEffectTarget("x.mdl", SHOW_UNIT[pid], "hand")
    endif
endfunction
"""

_BENIGN_SYNCREAD = """
function LoadSaveSlot takes player p, integer slot returns nothing
    local string s = ""
    if GetLocalPlayer() == p then
        set s = SaveFile_getLines(slot, 1, false, 0)
        call BlzSendSyncData("PFX", s)
    endif
    set s = null
endfunction
"""


def selftest():
    fails = 0

    def check(label, text, expect_ok):
        nonlocal fails
        ok, has_getter, findings = _audit_one(label, text)
        status = "PASS" if ok == expect_ok else "FAIL"
        if ok != expect_ok:
            fails += 1
        print(f"  [{status}] {label}: ok={ok} (expected {expect_ok}) getter={has_getter}")
        for f in findings:
            print("        - " + f)

    print("=== selftest ===")
    # The whole point: a FOREIGN track carrying the bug must be caught RED.
    check("foreign track w/ gated-only lazy alloc -> RED",
          _LAZY_GETTER + _BUGGY_FOREIGN, expect_ok=False)
    # Benign idioms must stay GREEN (no false positive that would mask the real one).
    check("benign: effect handle in GLP gate (SHOW_WEAPON_FX) -> GREEN",
          _BENIGN_EFFECT, expect_ok=True)
    check("benign: local file-read + BlzSendSyncData -> GREEN",
          _BENIGN_SYNCREAD, expect_ok=True)
    # A foreign track with the getter but an UNCONDITIONAL prealloc stays GREEN.
    fixed = _LAZY_GETTER + _BUGGY_FOREIGN.replace(
        "if GetLocalPlayer() == p then",
        "call Foo_forHero(u)\n    if GetLocalPlayer() == p then")
    check("foreign track w/ unconditional prealloc -> GREEN", fixed, expect_ok=True)
    if fails:
        print(f"SELFTEST FAILED ({fails})")
        return 1
    print("SELFTEST PASS (4/4)")
    return 0


def main():
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    sys.exit(run_live())


if __name__ == "__main__":
    main()
