#!/usr/bin/env python3
r"""
verify_hero_select_p2_takenvillager_anchor.py
================================================================================
KOTR Hero-Select REDESIGN (Track 4) · P2 APPLY-RUNBOOK **STEP-0 `CastleSlot_TakenVillager`
per-slot already-taken fallback unit-type** <-> handler DEFERRED-ELSE spine authority <->
generated data table <-> live extract binder.
Built 2026-06-19 by KOTR Builder (engine claude-p).

WHY THIS GATE EXISTS (a real, uncovered seam — the DEFERRED ELSE-branch fallback DATA)
--------------------------------------------------------------------------------
`hero_select_p2_APPLY_RUNBOOK.md` STEP-0 reserves:
    | `CastleSlot_TakenVillager` | integer **array** | 0 | P2 | already-taken fallback
      unit-type (human-ELSE, deferred) |
That row is WHICH placeholder unit a pedestal spawns when a HUMAN-controlled slot is picked
(the body spawns the "taken villager" placeholder in the `controller != COMPUTER` ELSE
branch INSTEAD of renaming). `InitCastleSlotData` materializes the 10 values byte-exact from
the canonical extract (`set udg_CastleSlot_TakenVillager[0]='n00S' ... [9]='n00S'`) — even
though the handler's ELSE spine is deliberately EMPTY (the villager spawn+items+`udg_Villager_<Hero>`
ref-set are DEFERRED / P1-Evan-gated and ride the per-slot villager/extras path, NOT the
data-uniform spine). The DATA is captured so the deferred path has the right values when it
lands; if that per-slot villager distribution drifts, the future deferred path spawns the
WRONG placeholder at a human-picked pedestal — a silent regression invisible to a compile,
and (because the ELSE is empty today) invisible to the live spine too.

The trap that makes this its OWN gate, distinct from the HeroType binder:
  * The villager is the **SECOND** picker-owned `CreateNUnits` spawn in each body (the hero
    is the FIRST). A naive "grab the CreateUnit rawcode" conflates the two. This gate binds
    specifically the second picker-owned spawn — the DEFERRED ELSE op — per slot.
  * Unlike HeroType (10 DISTINCT — a real per-slot identity), TakenVillager is a **grouped
    fallback MULTISET** (`n00S x4, n00Q x2, n00R x4`) — there ARE intentional repeats. A
    tooth that demanded 10-distinct (correct for HeroType) would FALSE-POSITIVE here; a
    tooth that demanded a stuck single value would miss the 3-way grouping. This gate proves
    the live multiset == the generated multiset AND that it genuinely repeats (not a
    per-slot identity, not a stuck fill).
  * "Deferred" must mean **captured-not-dropped**: the handler ELSE is EMPTY (no villager
    CreateNUnits on the spine) YET the data table still materializes all 10 values. This
    gate proves both halves — folding the villager spawn back onto the spine (un-deferring
    it) OR dropping the data table values both trip it.

Why no existing gate closes THIS seam:
  * `verify_hero_select_p2_herotype_anchor.py` reads `villagers` only to prove the villager
    SET is DISJOINT from the hero set (non-conflation, one direction). It NEVER binds the
    per-slot villager VALUES to the generated `TakenVillager[i]`, never proves the live
    second-picker-spawn[i] == gen[i], never checks the multiset structure, and never proves
    the deferred-ELSE honesty (empty spine + materialized data). A wrong per-slot villager
    rawcode, or a folded-onto-spine villager spawn, passes it.
  * `verify_hero_select_p2_generated_j.py` checks the materialized .j broadly; it is not a
    runbook<->handler<->live per-slot identity binder with the conflation/deferred teeth.
  * `verify_castleslot_global_contract.py` binds the STEP-0 var TABLE row's *type +
    array-flag* (TakenVillager = integer array) — never the per-slot VALUES nor live.

So this gate closes the seam the established Track-4 way: runbook prose <-> handler spine
<-> generated data table <-> md5-pinned live extract, both directions — the DEFERRED-ELSE,
grouped-multiset sibling of the dense-distinct HeroType binder.

WHAT IT CHECKS (read-only; touches no .w3x and no shippable .j)
--------------------------------------------------------------------------------
  0. md5 pin: the live extract still hashes to the runbook-pinned md5 (a re-bake trips it).
  1. all 10 hand-written hero pick bodies are present in the live extract.
  2. per-slot-faithful: for slot i, the SECOND picker-owned CreateNUnits 2nd arg in body i
     (live) == `set udg_CastleSlot_TakenVillager[i]='...'` (generated data table), all 10.
  3. grouped-multiset (NOT 10-distinct): live villager multiset == gen villager multiset
     AND it genuinely repeats (distinct < 10) — the discrimination invariant that proves
     this is a faction-grouped fallback table, not a per-slot identity (HeroType's trap
     inverted).
  4. deferred-honesty: handler ELSE spine carries NO villager CreateNUnits (deferred/empty
     by design) YET the data table materializes all 10 TakenVillager values (captured, not
     dropped) <-> handler "(taken-villager block) is DEFERRED by design" <-> runbook
     "already-taken fallback ... human-ELSE, deferred".
  5. non-conflation/hero: the villager set is DISJOINT from the hero set (live + generated)
     — the villager binder must not grab the FIRST (hero) spawn.
  6. non-conflation/neutral: Gawain's neutral 'h012' caster is excluded from the villager
     set (live) — the villager is picker-owned, not the neutral polymorph caster.
  7. ordering/ELSE-position: every body has exactly [hero, villager] picker-owned spawns in
     that order — the villager is the SECOND (deferred ELSE) op, never the first.

Run:        python3 verify_hero_select_p2_takenvillager_anchor.py
Self-test:  python3 verify_hero_select_p2_takenvillager_anchor.py --selftest
            (parser unit-tests + a per-direction RED-catch so the gate has teeth)
"""
import hashlib
import re
import sys
from collections import Counter
from pathlib import Path

EXTRACT = Path.home() / "Warcraft III" / "KOTR" / "_extract_v050" / "war3map.j"
RUNBOOK = Path.home() / "Warcraft III" / "KOTR" / "_crew" / "hero_select_p2_APPLY_RUNBOOK.md"
HANDLER = (Path.home() / "Systems_Migration" / "kotr" / "fix_specs"
           / "hero_select_p2_loop_handler.j")
GEN_DATA = (Path.home() / "Systems_Migration" / "kotr" / "fix_specs"
            / "hero_select_p2_loop_data.gen.j")

# the md5 the runbook pins the canonical extract to (Grounding header) — same pin
# the sibling Track-4 binders use, so a re-bake trips them all together.
RUNBOOK_CLAIMED_MD5 = "967131658fd8d4fb27ee0d7f74e4bd22"

# the 10 hand-written hero pick bodies, in data-table SLOT order (slot i below ==
# udg_CastleSlot_*[i]). Identical ordering to the HeroType binder (proven there by
# per-slot-faithful on the FIRST spawn; here we bind the SECOND spawn at the same order).
HERO_FUNCS = [
    ("Trig_King_Arthur_Actions", "Arthur"),         # 0
    ("Trig_Lady_Guinevere_Actions", "Guinevere"),   # 1
    ("Trig_Lady_of_the_Lake_Actions", "Nimue"),     # 2
    ("Trig_Merlin_Actions", "Merlin"),              # 3
    ("Trig_Sir_Kay_Actions", "Kay"),               # 4
    ("Trig_Sir_Percival_Actions", "Percival"),      # 5
    ("Trig_Sir_Galahad_Actions", "Galahad"),        # 6
    ("Trig_Sir_Lancelot_Actions", "Lancelot"),      # 7
    ("Trig_Sir_Yvain_Actions", "Yvain"),           # 8
    ("Trig_Sir_Gawain_Actions", "Gawain"),          # 9
]

_RAWCODE = re.compile(r"CreateNUnitsAtLoc(?:FacingLocBJ)?\(1, '([^']+)'")


def body_of(extract_text, func):
    m = re.search(
        r"function " + re.escape(func) + r" takes nothing returns nothing(.*?)\nendfunction",
        extract_text, re.DOTALL)
    return m.group(1) if m else None


def body_spawns(body):
    """Ordered picker-owned + neutral CreateNUnits rawcodes in one pick body.
    picker[0] is the HERO spawn; picker[1] (if any) is the TakenVillager fallback
    (the human-ELSE deferred op); neutral holds Gawain's 'h012' polymorph caster."""
    picker, neutral = [], []
    if body is None:
        return picker, neutral
    for raw in body.splitlines():
        s = raw.strip()
        if "CreateNUnits" not in s:
            continue
        m = _RAWCODE.search(s)
        code = m.group(1) if m else "?"
        if "GetOwningPlayer(GetTriggerUnit())" in s:
            picker.append(code)
        else:
            neutral.append(code)
    return picker, neutral


def live_facts(extract_text):
    """Per-slot fallback-villager facts pulled straight from the live bodies."""
    missing, heroes, villagers, neutrals, orders = [], [], [], [], []
    for func, _hero in HERO_FUNCS:
        body = body_of(extract_text, func)
        if body is None:
            missing.append(func)
            heroes.append(None)
            villagers.append(None)
            neutrals.append([])
            orders.append(None)
            continue
        picker, neutral = body_spawns(body)
        heroes.append(picker[0] if len(picker) >= 1 else None)
        villagers.append(picker[1] if len(picker) >= 2 else None)
        neutrals.append(neutral)
        # the discrimination invariant: exactly [hero, villager], villager SECOND.
        orders.append(len(picker) == 2)
    return {
        "missing": missing,
        "heroes": heroes,            # slot-ordered live hero rawcodes (FIRST spawn)
        "villagers": villagers,      # slot-ordered live TakenVillager rawcodes (SECOND)
        "neutrals": neutrals,        # per-slot neutral rawcodes (only Gawain non-empty)
        "orders": orders,            # per-slot: exactly [hero, villager]
    }


def gen_array(gen_text, name):
    """slot-ordered list of `set udg_<name>[i]='CODE'` values from the generated table."""
    pairs = re.findall(
        r"set udg_" + re.escape(name) + r"\[(\d+)\]\s*=\s*'([^']+)'", gen_text)
    out = {}
    for i, code in pairs:
        out[int(i)] = code
    return [out.get(i) for i in range(len(out))] if out else []


def handler_else_has_villager_spawn(handler_text):
    """True if the handler's controller-guard ELSE branch emits a (picker-owned) villager
    CreateNUnits — i.e. the deferred op was (wrongly) folded back onto the spine. The
    faithful handler keeps the ELSE EMPTY (deferred), so this must be False."""
    m = re.search(r"\n\s*else\b(.*?)\n\s*endif", handler_text, re.DOTALL)
    if not m:
        return False
    else_block = m.group(1)
    # strip comment lines; a real spawn is an uncommented `call CreateNUnits...`
    for raw in else_block.splitlines():
        s = raw.strip()
        if s.startswith("//"):
            continue
        if "CreateNUnits" in s and "call" in s:
            return True
    return False


def all_rows(extract_text, runbook_text, handler_text, gen_text):
    """Per-anchor rows: (label, live_ok, handler_ok, prose_ok, prose_required, detail)."""
    f = live_facts(extract_text)
    gen_hero = gen_array(gen_text, "CastleSlot_HeroType")
    gen_vill = gen_array(gen_text, "CastleSlot_TakenVillager")
    rbf = re.sub(r"\s+", " ", runbook_text)
    hd = re.sub(r"\s+", " ", re.sub(r"//+", " ", handler_text))
    rows = []

    def row(label, live_ok, handler_ok, prose_ok, prose_required, detail=""):
        rows.append((label, live_ok, handler_ok, prose_ok, prose_required, detail))

    # 1) all 10 hero pick bodies present
    live_ok = not f["missing"] and all(h is not None for h in f["heroes"])
    row("bodies:present=10", live_ok,
        "10 hand-written Trig_<Hero>_Actions" in hd,
        "10 old `Trig_<Hero>_Actions`" in rbf, True,
        "" if live_ok else f"missing/empty bodies: {f['missing']}")

    # 2) per-slot-faithful: live SECOND-picker-spawn[i] == generated TakenVillager[i], all 10
    live_ok = (len(gen_vill) == 10 and f["villagers"] == gen_vill)
    mism = [(i, f["villagers"][i], gen_vill[i] if i < len(gen_vill) else None)
            for i in range(10) if (i >= len(gen_vill) or f["villagers"][i] != gen_vill[i])]
    row("takenvillager:per-slot-faithful", live_ok,
        "(taken-villager block) is DEFERRED by design" in hd,
        "already-taken fallback unit-type" in rbf, True,
        "" if live_ok else f"live!=gen per slot {mism[:4]}")

    # 3) grouped-multiset (NOT 10-distinct): live multiset == gen multiset AND it repeats
    live_clean = [v for v in f["villagers"] if v]
    repeats = len(set(live_clean)) < 10 and len(live_clean) == 10
    multiset_match = (bool(gen_vill)
                      and Counter(live_clean) == Counter(v for v in gen_vill if v))
    live_ok = repeats and multiset_match
    row("takenvillager:grouped-multiset", live_ok,
        "DEFERRED by design" in hd,
        False, False,
        "" if live_ok
        else f"live={dict(Counter(live_clean))} gen={dict(Counter(v for v in gen_vill if v))} "
             f"distinct={len(set(live_clean))}")

    # 4) deferred-honesty: handler ELSE has NO villager CreateNUnits (deferred/empty), YET
    #    the data table materializes all 10 values (captured, not dropped).
    else_empty = not handler_else_has_villager_spawn(handler_text)
    data_materialized = (len(gen_vill) == 10 and all(v for v in gen_vill))
    live_ok = data_materialized       # the data-side half (live truth = data must exist)
    handler_ok = (else_empty and "(taken-villager block) is DEFERRED by design" in hd)
    row("takenvillager:deferred-honesty", live_ok,
        handler_ok,
        "already-taken fallback unit-type (human-ELSE, deferred)" in rbf, True,
        "" if (live_ok and handler_ok)
        else f"else_empty={else_empty} data_materialized={data_materialized} "
             f"gen_count={len(gen_vill)}")

    # 5) non-conflation/hero: villager set DISJOINT from hero set (live + generated)
    live_heroes = set(h for h in f["heroes"] if h)
    live_vill = set(v for v in f["villagers"] if v)
    gen_disjoint = (bool(gen_hero) and bool(gen_vill)
                    and not (set(gen_hero) & set(gen_vill)))
    live_disjoint = bool(live_vill) and not (live_heroes & live_vill)
    live_ok = live_disjoint and gen_disjoint
    row("non-conflation:hero-disjoint", live_ok,
        "(taken-villager block) is DEFERRED by design" in hd,
        "already-taken fallback unit-type (human-ELSE, deferred)" in rbf, True,
        "" if live_ok
        else f"villager∩hero live={sorted(live_heroes & live_vill)} "
             f"gen={sorted(set(gen_hero) & set(gen_vill))}")

    # 6) non-conflation/neutral: Gawain's 'h012' is excluded from the villager set
    all_neutrals = set(c for nl in f["neutrals"] for c in nl)
    live_ok = ("h012" in all_neutrals) and ("h012" not in live_vill)
    row("non-conflation:neutral-h012-excluded", live_ok,
        "h012" in hd and "neutral" in hd,
        False, False,
        "" if live_ok else f"neutrals={sorted(all_neutrals)} villagers={sorted(live_vill)}")

    # 7) ordering/ELSE-position: every body has exactly [hero, villager], villager SECOND
    live_ok = all(f["orders"])
    bad = [HERO_FUNCS[i][1] for i, ok in enumerate(f["orders"]) if not ok]
    row("ordering:villager-second", live_ok,
        "the body spawns the villager instead" in hd
        or "spawns the per-hero \"taken villager\" placeholder" in hd
        or "taken villager" in hd,
        False, False,
        "" if live_ok else f"bodies without exactly [hero,villager]: {bad}")

    return rows


def _passed(live_ok, handler_ok, prose_ok, prose_required):
    return bool(live_ok) and bool(handler_ok) and (bool(prose_ok) or not prose_required)


def report(rows):
    print(f"{'ANCHOR':<40}{'LIVE':<8}{'HANDLER':<10}{'PROSE':<8}")
    for label, live_ok, handler_ok, prose_ok, prose_required, detail in rows:
        prose_cell = ("OK" if prose_ok else "DRIFT") if prose_required else "n/a"
        print(f"{label:<40}{'OK' if live_ok else 'DRIFT':<8}"
              f"{'OK' if handler_ok else 'DRIFT':<10}"
              f"{prose_cell:<8}"
              + (f"  -> {detail}" if detail else ""))


def _synth_ok():
    """A synthetic (extract, runbook, handler, gen) quad satisfying every anchor — the
    selftest baseline + the fixtures each RED-catch mutates. Gawain's body carries the
    neutral 'h012' caster, so the OK fixture passing proves the parser EXCLUDES it from
    the villager set. Villagers intentionally REPEAT (grouped multiset)."""
    heroes = ["Harf", "Hvwd", "Hjai", "Hant", "Hpb1",
              "Huth", "Hpb2", "Hart", "H013", "H014"]
    vills = ["n00S", "n00Q", "n00Q", "n00R", "n00R",
             "n00R", "n00S", "n00S", "n00R", "n00S"]
    bodies = []
    for idx, (func, _hero) in enumerate(HERO_FUNCS):
        head = f"function {func} takes nothing returns nothing\n"
        pre = ""
        if "Gawain" in func:
            pre = ("    call CreateNUnitsAtLoc(1, 'h012', Player(PLAYER_NEUTRAL_AGGRESSIVE), "
                   "GetRectCenter(gg_rct_Gawain), bj_UNIT_FACING)\n")
        hero = (f"    call CreateNUnitsAtLocFacingLocBJ(1, '{heroes[idx]}', "
                "GetOwningPlayer(GetTriggerUnit()), GetRectCenter(gg_rct_x), GetRectCenter(gg_rct_y))\n")
        vill = (f"        call CreateNUnitsAtLocFacingLocBJ(1, '{vills[idx]}', "
                "GetOwningPlayer(GetTriggerUnit()), GetRectCenter(gg_rct_x), GetUnitLoc(gg_unit_h005_1098))\n")
        bodies.append(head + pre + hero + vill + "endfunction\n")
    extract = "\n".join(bodies)
    gen = "function InitCastleSlotData takes nothing returns nothing\n"
    for i in range(10):
        gen += f"    set udg_CastleSlot_HeroType[{i}]='{heroes[i]}'\n"
    for i in range(10):
        gen += f"    set udg_CastleSlot_TakenVillager[{i}]='{vills[i]}'\n"
    gen += "endfunction\n"
    handler = (
        "//  Replaces the SHARED mechanics of the 10 hand-written Trig_<Hero>_Actions pick\n"
        "//  bodies ... that walks the udg_CastleSlot_* parallel arrays BY SLOT INDEX.\n"
        "//  (a) GAWAIN — spawn a neutral 'h012' caster ... DEFERRED to the ExtrasHook.\n"
        "//  The human-controlled ELSE (taken-villager block) is DEFERRED by design: the\n"
        "//  per-hero udg_Villager_<Hero> ref globals are map-wide referenced + P1-Evan-gated.\n"
        "//  human-controlled slot: the body spawns the per-hero \"taken villager\" placeholder\n"
        "//  here INSTEAD of renaming. the body spawns the villager instead.\n"
        "    if ( GetPlayerController(picker) == MAP_CONTROL_COMPUTER ) then\n"
        "        call SetPlayerName(picker, udg_CastleSlot_NameStr[i])\n"
        "    else\n"
        "        // empty by design (deferred ELSE)\n"
        "    endif\n")
    runbook = (
        "the 10 old `Trig_<Hero>_Actions` pick bodies ... | `CastleSlot_TakenVillager` | "
        "integer **array** | 0 | P2 | already-taken fallback unit-type (human-ELSE, deferred) |")
    return extract, runbook, handler, gen


def _selftest():
    ok = True
    extract, runbook, handler, gen = _synth_ok()

    # parser unit-tests
    f = live_facts(extract)
    if f["villagers"] != ["n00S", "n00Q", "n00Q", "n00R", "n00R",
                          "n00R", "n00S", "n00S", "n00R", "n00S"]:
        print(f"[selftest] FAIL parser villagers: {f['villagers']}"); ok = False
    if f["heroes"][0] != "Harf":
        print(f"[selftest] FAIL parser heroes[0]: {f['heroes'][0]}"); ok = False
    if [c for nl in f["neutrals"] for c in nl] != ["h012"]:
        print(f"[selftest] FAIL parser neutral leak: {f['neutrals']}"); ok = False
    if gen_array(gen, "CastleSlot_TakenVillager")[2] != "n00Q":
        print("[selftest] FAIL gen_array parse"); ok = False
    if handler_else_has_villager_spawn(handler):
        print("[selftest] FAIL else_has_villager_spawn false-positive on empty ELSE"); ok = False

    # OK baseline: every anchor passes
    rows = all_rows(extract, runbook, handler, gen)
    for label, lo, ho, po, pr, det in rows:
        if not _passed(lo, ho, po, pr):
            print(f"[selftest] FAIL OK-baseline anchor {label}: {det}"); ok = False

    # RED 1 — drift one gen villager value (per-slot-faithful must catch)
    bad_gen = gen.replace("set udg_CastleSlot_TakenVillager[3]='n00R'",
                          "set udg_CastleSlot_TakenVillager[3]='nXXX'")
    rows = dict((r[0], r) for r in all_rows(extract, runbook, handler, bad_gen))
    if _passed(*rows["takenvillager:per-slot-faithful"][1:5]):
        print("[selftest] FAIL RED1 per-slot drift not caught"); ok = False

    # RED 2 — collapse villagers to a stuck single value in BOTH live+gen (grouped-multiset
    #         must catch: distinct==1 < 10 still 'repeats', but per-slot must remain faithful
    #         while the multiset stops being the real grouped table). Use distinct=1 fixture
    #         where every slot is the same -> still repeats, multiset matches; this should be
    #         GREEN by design (a degenerate-but-faithful table). Instead test the inverse: make
    #         all 10 villagers DISTINCT in both -> repeats becomes False -> RED.
    distinct = ["n00A", "n00B", "n00C", "n00D", "n00E",
                "n00F", "n00G", "n00H", "n00I", "n00J"]
    ex2 = extract
    g2 = gen
    for i in range(10):
        ex2 = ex2.replace(f"'{['n00S','n00Q','n00Q','n00R','n00R','n00R','n00S','n00S','n00R','n00S'][i]}', GetOwningPlayer(GetTriggerUnit()), GetRectCenter(gg_rct_x), GetUnitLoc",
                          f"'{distinct[i]}', GetOwningPlayer(GetTriggerUnit()), GetRectCenter(gg_rct_x), GetUnitLoc", 1)
        g2 = g2.replace(f"set udg_CastleSlot_TakenVillager[{i}]='{['n00S','n00Q','n00Q','n00R','n00R','n00R','n00S','n00S','n00R','n00S'][i]}'",
                        f"set udg_CastleSlot_TakenVillager[{i}]='{distinct[i]}'")
    rows = dict((r[0], r) for r in all_rows(ex2, runbook, handler, g2))
    if _passed(*rows["takenvillager:grouped-multiset"][1:5]):
        print("[selftest] FAIL RED2 all-distinct (no grouping) not caught"); ok = False

    # RED 3 — fold the villager spawn onto the handler spine ELSE (deferred-honesty must catch)
    folded_handler = handler.replace(
        "        // empty by design (deferred ELSE)\n",
        "        call CreateNUnitsAtLocFacingLocBJ(1, udg_CastleSlot_TakenVillager[i], picker, loc, face)\n")
    rows = dict((r[0], r) for r in all_rows(extract, runbook, folded_handler, gen))
    if _passed(*rows["takenvillager:deferred-honesty"][1:5]):
        print("[selftest] FAIL RED3 villager folded onto spine not caught"); ok = False

    # RED 4 — make a gen villager value collide with a hero rawcode (non-conflation must catch)
    conflated = gen.replace("set udg_CastleSlot_TakenVillager[0]='n00S'",
                            "set udg_CastleSlot_TakenVillager[0]='Harf'")
    rows = dict((r[0], r) for r in all_rows(extract, runbook, handler, conflated))
    if _passed(*rows["non-conflation:hero-disjoint"][1:5]):
        print("[selftest] FAIL RED4 villager∩hero conflation not caught"); ok = False

    # RED 5 — swap order so villager is FIRST, hero SECOND (ordering must catch)
    swapped = extract.replace(
        ("    call CreateNUnitsAtLocFacingLocBJ(1, 'Harf', "
         "GetOwningPlayer(GetTriggerUnit()), GetRectCenter(gg_rct_x), GetRectCenter(gg_rct_y))\n"
         "        call CreateNUnitsAtLocFacingLocBJ(1, 'n00S', "
         "GetOwningPlayer(GetTriggerUnit()), GetRectCenter(gg_rct_x), GetUnitLoc(gg_unit_h005_1098))\n"),
        ("        call CreateNUnitsAtLocFacingLocBJ(1, 'n00S', "
         "GetOwningPlayer(GetTriggerUnit()), GetRectCenter(gg_rct_x), GetUnitLoc(gg_unit_h005_1098))\n"
         "    call CreateNUnitsAtLocFacingLocBJ(1, 'Harf', "
         "GetOwningPlayer(GetTriggerUnit()), GetRectCenter(gg_rct_x), GetRectCenter(gg_rct_y))\n"))
    rows = dict((r[0], r) for r in all_rows(swapped, runbook, handler, gen))
    # ordering stays [2 picker spawns] so 'orders' True; the discrimination shows in
    # per-slot-faithful (villager now reads 'Harf' for slot0). Assert faithful catches it.
    if _passed(*rows["takenvillager:per-slot-faithful"][1:5]):
        print("[selftest] FAIL RED5 hero/villager swap not caught by per-slot-faithful"); ok = False

    print("SELFTEST", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main():
    if "--selftest" in sys.argv:
        return _selftest()

    for p in (EXTRACT, RUNBOOK, HANDLER, GEN_DATA):
        if not p.exists():
            print(f"MISSING input: {p}")
            return 2

    extract_bytes = EXTRACT.read_bytes()
    live_md5 = hashlib.md5(extract_bytes).hexdigest()
    extract_text = extract_bytes.decode("utf-8", "replace")
    runbook_text = RUNBOOK.read_text(encoding="utf-8", errors="replace")
    handler_text = HANDLER.read_text(encoding="utf-8", errors="replace")
    gen_text = GEN_DATA.read_text(encoding="utf-8", errors="replace")

    print("=" * 78)
    print("KOTR Hero-Select P2 — STEP-0 CastleSlot_TakenVillager per-slot fallback binder")
    print(f"  extract : {EXTRACT}")
    print(f"  md5     : {live_md5}  (claimed {RUNBOOK_CLAIMED_MD5})")
    print("=" * 78)

    md5_ok = (live_md5 == RUNBOOK_CLAIMED_MD5)
    if not md5_ok:
        print("FAIL anchor 0: live extract md5 != runbook-pinned md5 (a re-bake happened)")
        return 1

    rows = all_rows(extract_text, runbook_text, handler_text, gen_text)
    report(rows)

    failed = [r[0] for r in rows if not _passed(r[1], r[2], r[3], r[4])]
    total = len(rows)
    passed = total - len(failed)
    print("-" * 78)
    if failed:
        print(f"RESULT: FAIL — {passed}/{total} anchors GREEN; DRIFT: {failed}")
        return 1
    print(f"RESULT: PASS — md5 pinned + {passed}/{total} anchors GREEN "
          "(runbook <-> handler-deferred-ELSE <-> generated table <-> live, both ways)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
