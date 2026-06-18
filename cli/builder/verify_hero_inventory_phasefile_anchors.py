#!/usr/bin/env python3
"""
verify_hero_inventory_phasefile_anchors.py — Hero-Inventory PHASE 1-7 file anchor binder
=========================================================================================
Binds the SEVEN hero-inventory implementation phase files —

    hero_inventory_PHASE1_SPIKE.md                  (showroom / item-event spike)
    hero_inventory_PHASE2_DATAMODEL.md              (per-hero Table store + UI frame idiom)
    hero_inventory_PHASE3_PLUMBING.md               (pickup/give/use/drop/pawn shadow hooks)
    hero_inventory_PHASE4_EQUIPMENT.md              (NewBonus equip/unequip + camera FX)
    hero_inventory_PHASE5_SAVELOAD.md               (savecode write/read item slots)
    hero_inventory_PHASE6_MENUBUTTONS.md            (6-slot menu buttons + talent open)
    hero_inventory_PHASE7_ERRANTRY_QUESTLOG_HEARTH.md (errantry / questlog / hearth)

— to the live `_extract_v050/war3map.j`, BOTH directions. These seven docs are the
per-phase build specs: each justifies its paste's integration points by pinning
byte-exact `war3map.j` line cites (the central pickup hub `s__Items___Items_OnPickUp`
at L43910 / its reg L43939, the `NewBonus.add` equip/revert idiom at L33562, the
savecode item-slot writer/reader at L45466/L47008, the `STK_OpenTalentScreen` entry at
L31735, the saved-hero spawn rect at L2939, …).

WHY THIS GATE EXISTS (covered by no other gate)
--------------------------------------------------------------------------------
The hero-inventory track already has several binders, but each binds a DIFFERENT
artifact, and NONE reads the PHASE1-7 files' own live war3map.j cites:
  * verify_command_hub_spec_grounding.py            -> SPEC.md grounding <-> live
  * verify_hero_inventory_phase0_recon_anchors.py   -> PHASE0_RECON.md  <-> live
  * verify_hero_inventory_runbook_*_anchors.py       -> APPLY_RUNBOOK.md <-> live / phase files
  * verify_hero_inventory_runbook_phasefile_anchors.py -> RUNBOOK prose <-> phase-file LINES
      (binds the runbook's #2/#3 menu-item & DESYNC2 cites INTO the phase files — NOT the
       phase files' own cites OUT to the live extract)
The PHASE1-7 files are the LIVING per-phase specs the runbook's pastes derive from
(the runbook footer: "Source of truth for each paste block is the named phase file"),
yet their byte-exact line cites OUT to war3map.j were machine-checked by nothing. A
World-Editor save renumbers JASS and shifts every cited line (the staleness class that
already bit B4b and the runbook's own phase-file cites — see the GROUNDED FINDING in
verify_hero_inventory_runbook_phasefile_anchors.py, where PHASE1_SPIKE L143 had already
drifted to L152), silently turning a phase file into a liar — "the pickup hub is at
L43910" while L43910 has drifted — and the next operator pastes against a moved anchor.
This binder makes that drift fail LOUD. It is the exact Track-symmetric twin of
verify_companion_ai_phasefile_anchors.py (the companion-AI PHASE1-5 file binder).

WHAT IT CHECKS (read-only; touches no .w3x and no shippable .j)
--------------------------------------------------------------------------------
source identity   md5 == 967131658fd8…, lines == 75535 (the canonical v0.50 extract)
For every anchor in ANCHORS, BOTH directions must hold:
  1. FORWARD (live):  the extract's cited 1-based line carries ALL claimed tokens
     byte-exact (a WE re-bake that moves the line is caught); AND
  2. REVERSE (prose): the OWNING phase file still carries that exact `L<n>` cite
     (a doc edit that drops/rewrites the cite is caught).

No phase-file md5 pin: phase files are LIVING paste sources, so line-level cite drift
(not a whole-file hash) is the signal that matters — the live extract IS md5-pinned,
and the phase prose is what is kept honest. Sibling of
verify_companion_ai_phasefile_anchors.py and verify_hero_inventory_runbook_phasefile_anchors.py.

Run:        python3 verify_hero_inventory_phasefile_anchors.py
Self-test:  python3 verify_hero_inventory_phasefile_anchors.py --selftest
            (synthetic extract + phase texts that pass every anchor, then drift one
             live line and drop one prose cite; both must be caught)

EXIT 0 = GREEN, 1 = an anchor drifted, 2 = source/phase file not found, 3 = selftest.
Standalone by design — NOT wired into verify_all.py, so the canonical 178/178 sweep is
unchanged; invoked on its own when a phase file is touched or after any WE re-extract.
"""
import hashlib
import sys
from pathlib import Path

ROOT = Path("/mnt/c/Users/Morph/OneDrive/Documents/Warcraft III/Maps/KOTR")
SRC = ROOT / "_extract_v050" / "war3map.j"
CREW = ROOT / "_crew"

CANON_MD5 = "967131658fd8d4fb27ee0d7f74e4bd22"
CANON_LINES = 75535

PHASE_FILES = {
    "P1": CREW / "hero_inventory_PHASE1_SPIKE.md",
    "P2": CREW / "hero_inventory_PHASE2_DATAMODEL.md",
    "P3": CREW / "hero_inventory_PHASE3_PLUMBING.md",
    "P4": CREW / "hero_inventory_PHASE4_EQUIPMENT.md",
    "P5": CREW / "hero_inventory_PHASE5_SAVELOAD.md",
    "P6": CREW / "hero_inventory_PHASE6_MENUBUTTONS.md",
    "P7": CREW / "hero_inventory_PHASE7_ERRANTRY_QUESTLOG_HEARTH.md",
}

# Each anchor: (cid, phase-key, 1-based live line, [tokens ALL byte-exact on that
# live line], the `L<n>` cite literal the OWNING phase file's prose must carry).
ANCHORS = [
    # ---- PHASE 1: showroom camera setups + the map's item-event idiom ----------
    ("p1.cam1",       "P1", 43077, ["set gg_cam_Beginning_01=CreateCameraSetup()"],                       "L43077"),
    ("p1.cam2",       "P1", 43091, ["set gg_cam_Beginning_02=CreateCameraSetup()"],                       "L43091"),
    ("p1.itemusedef", "P1", 15215, ["function GT_RegisterItemUsedEvent takes trigger t,integer abil"],    "L15215"),
    ("p1.itemuseidiom","P1",15887, ["call TriggerAddCondition(GT_RegisterItemUsedEvent(CreateTrigger()"], "L15887"),
    ("p1.itemusecond","P1", 15237, ["function GT__TriggerItemUsedEvent takes nothing returns boolean"],   "L15237"),
    ("p1.acqdef",     "P1", 15349, ["function GT_RegisterItemAcquiredEvent takes trigger t,integer abil"],"L15349"),
    ("p1.camtarget",  "P1", 44205, ["SetCameraTargetControllerNoZForPlayer(GetTriggerPlayer()"],          "L44205"),
    ("p1.camreset",   "P1", 44212, ["ResetToGameCameraForPlayer(GetTriggerPlayer(), 0)"],                 "L44212"),
    ("p1.camapply",   "P1", 51226, ["CameraSetupApplyForPlayer(true, gg_cam_Call_To_Arms"],               "L51226"),
    # ---- PHASE 2: Table store + the Talent UI frame idiom to mirror ------------
    ("p2.tablecreate","P2", 18248, ["function s__Table_create takes nothing returns integer"],            "L18248"),
    ("p2.italentslot","P2",  4147, ["constant integer si__ITalentSlot=15"],                               "L4147"),
    ("p2.mainframe",  "P2", 16848, ['set TalentMainFrame=BlzCreateFrame("EscMenuBackdrop"'],              "L16848"),
    ("p2.treebg",     "P2", 16901, ['set TreeBackgroundLeft=BlzCreateFrameByType("BACKDROP"'],            "L16901"),
    ("p2.pickuphandler","P2",43910,["function s__Items___Items_OnPickUp takes nothing returns nothing"],  "L43910"),
    ("p2.pickupreg",  "P2", 43939, ["RegisterPlayerUnitEvent(EVENT_PLAYER_UNIT_PICKUP_ITEM"],             "L43939"),
    ("p2.uimakerinit","P2", 16845, ["function REFORGEDUIMAKER___init takes nothing returns nothing"],     "L16845"),
    ("p2.additem",    "P2", 41089, ["call UnitAddItemToSlotById(u, 'whwd', 0)"],                          "L41089"),
    # ---- PHASE 3: the pickup hub + give/use/drop/pawn shadow-hook surfaces ------
    ("p3.pickupreg",  "P3", 43939, ["RegisterPlayerUnitEvent(EVENT_PLAYER_UNIT_PICKUP_ITEM"],             "L43939"),
    ("p3.pickuphandler","P3",43910,["function s__Items___Items_OnPickUp takes nothing returns nothing"],  "L43910"),
    ("p3.pawn",       "P3", 70181, ["TriggerRegisterAnyUnitEventBJ(gg_trg_AncientCity, EVENT_PLAYER_UNIT_PAWN_ITEM)"], "L70181"),
    ("p3.drop1",      "P3", 28042, ["RegisterPlayerUnitEvent(EVENT_PLAYER_UNIT_DROP_ITEM", "s__EffectLink_onDrop"], "L28042"),
    ("p3.drop2",      "P3", 34378, ["RegisterPlayerUnitEvent(EVENT_PLAYER_UNIT_DROP_ITEM", "s__NewBonusUtils_onDrop"], "L34378"),
    ("p3.restore",    "P3", 47008, ["UnitAddItemByIdSwapped(udg_LoadItemTypes[( 5 - GetForLoopIndexA() )]"], "L47008"),
    ("p3.itemusedef", "P3", 15215, ["function GT_RegisterItemUsedEvent takes trigger t,integer abil"],    "L15215"),
    ("p3.itemuseidiom","P3",15887, ["call TriggerAddCondition(GT_RegisterItemUsedEvent(CreateTrigger()"], "L15887"),
    # ---- PHASE 4: NewBonus equip/revert idiom, bonus channels, origin FX -------
    ("p4.addimpl",    "P4", 33562, ["function s__NewBonus_add takes unit source,integer bonus,real value"],"L33562"),
    ("p4.addwrap",    "P4",  7050, ["function sc__NewBonus_add takes unit source,integer bonus,real value"],"L7050"),
    ("p4.bonus1",     "P4",  1490, ["constant integer BONUS_DAMAGE= 1"],                                  "L1490"),
    ("p4.bonus27",    "P4",  1516, ["constant integer BONUS_TENACITY_OFFSET= 27"],                        "L1516"),
    ("p4.linkitem",   "P4", 11172, ["function sc__NewBonusUtils_linkItem takes unit source,integer bonus,real amount,item i"], "L11172"),
    ("p4.origin",     "P4", 25503, ["AddSpecialEffectTarget(s__LifeSteal_effect", '"origin"'],            "L25503"),
    ("p4.camreset",   "P4", 44212, ["ResetToGameCameraForPlayer(GetTriggerPlayer(), 0)"],                 "L44212"),
    ("p4.camapply",   "P4", 51226, ["CameraSetupApplyForPlayer(true, gg_cam_Call_To_Arms"],               "L51226"),
    ("p4.camtarget",  "P4", 44205, ["SetCameraTargetControllerNoZForPlayer(GetTriggerPlayer()"],          "L44205"),
    # ---- PHASE 5: savecode item-slot writer/reader, whitelist, hash ------------
    ("p5.loaditems",  "P5", 45466, ["LoadInteger(s__SaveHelper_Hashtable, s__SaveHelper_KEY_ITEMS", "UnitItemInSlot(udg_SaveTempUnit"], "L45466"),
    ("p5.restore",    "P5", 47008, ["UnitAddItemByIdSwapped(udg_LoadItemTypes[( 5 - GetForLoopIndexA() )]"], "L47008"),
    ("p5.save",       "P5", 45524, ["set udg_SaveTempString=s__Savecode_Save((udg_SaveTempInt),GetTriggerPlayer() , 1)"], "L45524"),
    ("p5.saveinteger","P5", 26805, ["SaveInteger(s__SaveHelper_Hashtable, s__SaveHelper_KEY_ITEMS, udg_SaveItemType[i], i)"], "L26805"),
    ("p5.itemtypemax","P5", 45051, ["set udg_SaveItemTypeMax=999"],                                       "L45051"),
    ("p5.hash",       "P5", 22746, ["call s__Savecode_Encode(this,hash , (5000))"],                       "L22746"),
    # ---- PHASE 6: 6-slot bound, item-use/drop hooks, talent open + close -------
    ("p6.invbound",   "P6", 27379, ["exitwhen i > bj_MAX_INVENTORY"],                                     "L27379"),
    ("p6.itemslot",   "P6", 27380, ["set k=UnitItemInSlot(source, i)"],                                   "L27380"),
    ("p6.itemusedef", "P6", 15215, ["function GT_RegisterItemUsedEvent takes trigger t,integer abil"],    "L15215"),
    ("p6.itemusecond","P6", 15237, ["function GT__TriggerItemUsedEvent takes nothing returns boolean"],   "L15237"),
    ("p6.dropdef",    "P6", 15483, ["function GT_RegisterItemDroppedEvent takes trigger t,integer abil"], "L15483"),
    ("p6.talentopen", "P6", 31735, ["function STK_OpenTalentScreen takes player p returns nothing"],      "L31735"),
    ("p6.talentcaller","P6",44125, ["function Trig_OpenTalentTreeUI_Actions takes nothing returns nothing"], "L44125"),
    ("p6.talentcall", "P6", 44127, ["call STK_OpenTalentScreen(GetTriggerPlayer())"],                     "L44127"),
    ("p6.ttchat",     "P6", 44133, ['TriggerRegisterPlayerChatEvent(gg_trg_OpenTalentTreeUI, Player(0), "-tt", true)'], "L44133"),
    ("p6.framehide",  "P6", 16851, ["call BlzFrameSetVisible(TalentMainFrame, false)"],                   "L16851"),
    ("p6.additem",    "P6", 41089, ["call UnitAddItemToSlotById(u, 'whwd', 0)"],                          "L41089"),
    # ---- PHASE 7: questboard, saved-hero spawn rect, blink FX, townsfolk -------
    ("p7.questboard", "P7",  2761, ["multiboard udg_Questboard= null"],                                   "L2761"),
    ("p7.spawnrect",  "P7",  2939, ["rect gg_rct_Arthur_Kay_Lancelot_Appear= null"],                      "L2939"),
    ("p7.blink1",     "P7",  3732, ["constant string Dragonflight___TELEPORT", "BlinkTarget.mdl"],        "L3732"),
    ("p7.blink2",     "P7",  3904, ["constant string AerialStrike__TELEPORT", "BlinkTarget.mdl"],         "L3904"),
    ("p7.villager",   "P7",  2892, ["unit udg_Villager_Arthur= null"],                                    "L2892"),
]


def line_at(lines, lineno):
    return lines[lineno - 1] if 0 < lineno <= len(lines) else "<<EOF>>"


def audit(extract_lines, phase_texts, src_md5=None):
    """Return (rows, failures). rows=[(cid, phase, live_ok, prose_ok, detail)]."""
    rows, failures = [], []

    if src_md5 is not None:
        ok = src_md5 == CANON_MD5
        rows.append(("src.md5", "-", ok, True, "" if ok else f"md5 {src_md5} != {CANON_MD5}"))
        if not ok:
            failures.append(f"src.md5: extract md5 {src_md5} != pinned {CANON_MD5}")
    nlines = len(extract_lines) - 1 if extract_lines and extract_lines[-1] == "" else len(extract_lines)
    if src_md5 is not None:
        ok = nlines == CANON_LINES
        rows.append(("src.lines", "-", ok, True, "" if ok else f"{nlines} != {CANON_LINES}"))
        if not ok:
            failures.append(f"src.lines: extract has {nlines} lines, pinned {CANON_LINES}")

    for cid, pkey, lineno, tokens, cite in ANCHORS:
        live = line_at(extract_lines, lineno)
        missing = [t for t in tokens if t not in live]
        live_ok = not missing
        prose_ok = cite in phase_texts[pkey]
        detail = ""
        if not live_ok:
            detail = f"{pkey} live L{lineno} missing {missing!r} -> {live.strip()[:70]!r}"
        elif not prose_ok:
            detail = f"{pkey} prose no longer cites {cite!r}"
        rows.append((cid, pkey, live_ok, prose_ok, detail))
        if not (live_ok and prose_ok):
            failures.append(f"{cid}: {detail}")
    return rows, failures


def report(rows):
    print(f"{'ANCHOR':<18}{'PH':<4}{'LIVE':<7}{'PROSE':<7}DETAIL")
    for cid, pkey, live_ok, prose_ok, detail in rows:
        print(f"{cid:<18}{pkey:<4}{('OK' if live_ok else 'DRIFT'):<7}"
              f"{('OK' if prose_ok else 'DRIFT'):<7}{detail}")


def _build_synth():
    """Synthetic extract lines + phase texts that PASS every anchor (md5 skipped)."""
    base = ["x"] * CANON_LINES
    for _cid, _pk, lineno, tokens, _cite in ANCHORS:
        base[lineno - 1] = "    " + " ".join(tokens)
    phase_texts = {k: "" for k in PHASE_FILES}
    for _cid, pkey, _ln, _tok, cite in ANCHORS:
        if cite not in phase_texts[pkey]:
            phase_texts[pkey] += cite + " "
    return base, phase_texts


def selftest():
    print("=== SELFTEST: synthetic baseline GREEN, then drift one live line + drop one cite ===")
    ok_all = True

    base, phase_texts = _build_synth()
    _rows, failures = audit(base + [""], phase_texts, src_md5=None)
    clean_ok = (len(failures) == 0)
    print(f"  clean synthetic: ALL anchors GREEN both ways? {clean_ok}")
    if not clean_ok:
        for f in failures[:6]:
            print("   - unexpected:", f)
    ok_all &= clean_ok

    # (A) DRIFT a live line — the pickup hub moved off L43910
    bad = list(base)
    bad[43910 - 1] = "    function s__Something_else takes nothing returns nothing"
    _r1, f1 = audit(bad + [""], phase_texts, src_md5=None)
    caught_live = any(x.startswith("p3.pickuphandler:") and "live" in x for x in f1)
    print(f"  live-drift @L43910 caught? {caught_live}")

    # (B) DROP a prose cite — PHASE5 prose lost its L47008 restore cite
    bad_texts = dict(phase_texts)
    bad_texts["P5"] = phase_texts["P5"].replace("L47008 ", "")
    _r2, f2 = audit(base + [""], bad_texts, src_md5=None)
    caught_prose = any(x.startswith("p5.restore:") and "prose" in x for x in f2)
    print(f"  prose-drop L47008 (P5) caught? {caught_prose}")

    # (C) multi-token anchor: dropping ONE of two tokens must fail (not all-or-nothing slip)
    bad2 = list(base)
    bad2[28042 - 1] = "    call RegisterPlayerUnitEvent(EVENT_PLAYER_UNIT_DROP_ITEM , function s__Other_onDrop)"
    _r3, f3 = audit(bad2 + [""], phase_texts, src_md5=None)
    caught_multi = any(x.startswith("p3.drop1:") for x in f3)
    print(f"  multi-token partial-match @L28042 caught? {caught_multi}")

    # (D) md5 pin engages
    _r4, f4 = audit(base + [""], phase_texts, src_md5="deadbeef")
    caught_md5 = any(x.startswith("src.md5:") for x in f4)
    print(f"  md5 mismatch caught? {caught_md5}")

    ok_all &= caught_live and caught_prose and caught_multi and caught_md5
    print(f"\nSELFTEST {'PASS' if ok_all else 'FAIL'}")
    return 0 if ok_all else 3


def main():
    if "--selftest" in sys.argv:
        return selftest()
    if not SRC.exists():
        print(f"FATAL: live source not found: {SRC}")
        return 2
    phase_texts = {}
    for key, path in PHASE_FILES.items():
        if not path.exists():
            print(f"FATAL: phase file not found: {path}")
            return 2
        phase_texts[key] = path.read_text(encoding="utf-8")

    raw = SRC.read_bytes()
    src_md5 = hashlib.md5(raw).hexdigest()
    text = raw.decode("utf-8", "surrogatepass").replace("\r\n", "\n")
    extract_lines = text.split("\n")

    rows, failures = audit(extract_lines, phase_texts, src_md5=src_md5)
    report(rows)

    n_anchor = len(ANCHORS)
    print(f"\nsource: {SRC}")
    print(f"phase files: {n_anchor} anchors across {len(PHASE_FILES)} phase docs")
    if failures:
        print(f"\nRESULT: FAIL — {len(failures)} anchor(s) drifted (live-extract and/or phase-prose):")
        for f in failures:
            print("  -", f)
        print("Re-ground the named phase file against the current war3map.j (or restore the "
              "dropped L<n> cite) before any paste builds on it.")
        return 1
    print(f"\nRESULT: GREEN — all {n_anchor} hero-inventory PHASE1-7 file cites hold BYTE-EXACT at "
          f"the cited live line (md5 {CANON_MD5}, {CANON_LINES} lines) AND every owning phase "
          f"file still carries its L<n> cite (bound BOTH directions).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
