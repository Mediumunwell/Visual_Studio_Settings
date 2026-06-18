#!/usr/bin/env python3
"""
verify_castleslot_global_contract.py — KOTR Hero-Select REDESIGN (Track 4), PASTE-CONTRACT gate
================================================================================================
Closes an uncovered seam between PRODUCER and CONSUMER of the hero-select P2 data table:

  PRODUCER : _crew/hero_select_p2_InitCastleSlotData.generated.j
             (auto-generated; writes the `udg_CastleSlot_*` parallel arrays at map init)
  CONSUMER : _crew/hero_select_p2_APPLY_RUNBOOK.md  STEP-0 var table
             (the GUI Variable-Editor vars the operator must create BEFORE paste)

Why this gate exists (invisible to every other gate):
  pjass/WE compile the generated `.j` fine even if a STEP-0 var is the WRONG TYPE or MISSING —
  WarCraft's GUI `udg_` vars are declared in the Variable Editor, not in the pasted text, so a
  `unit`-vs-`integer` mismatch or an undeclared array is a SILENT PASTE-BRICK at run/save time,
  not a compile error. The generator already proves its OWN round-trip; nothing proved that what
  it WRITES lines up, name-for-name and TYPE-for-TYPE, with what the operator is told to declare.

What it checks (read-only; touches no .w3x):
  1. Every `udg_CastleSlot_<X>` array the generated `.j` ASSIGNS is DECLARED in the runbook table.
  2. The literal KIND the `.j` assigns to each array is TYPE-COMPATIBLE with the declared type:
       'XXXX' rawcode / int literal  -> integer        "..." / "TRIGSTR_n"  -> string
       gg_unit_* (or null)           -> unit           gg_trg_* (or null)   -> trigger
  Exit 0 only if all written arrays are declared AND every assignment is type-compatible.

Run:        python3 verify_castleslot_global_contract.py
Self-test:  python3 verify_castleslot_global_contract.py --selftest   (injects a synthetic
            type mismatch + an undeclared array into in-memory copies and proves both are caught)
"""
import re
import sys
from pathlib import Path

CREW = Path.home() / "Warcraft III" / "KOTR" / "_crew"
GEN_J = CREW / "hero_select_p2_InitCastleSlotData.generated.j"
RUNBOOK = CREW / "hero_select_p2_APPLY_RUNBOOK.md"

# declared type -> the set of assignment KINDS that are legal for it
COMPAT = {
    "integer": {"integer"},
    "string": {"string"},
    "unit": {"unit", "handle-null"},
    "trigger": {"trigger", "handle-null"},
    "location": {"location", "handle-null"},
}


def declared_types(runbook_text):
    """name -> declared base type, from rows like `| `CastleSlot_Item` | integer **array** | ...`"""
    decl = {}
    for m in re.finditer(r"\|\s*`CastleSlot_(\w+)`\s*\|\s*([a-z]+)\b", runbook_text):
        decl[m.group(1)] = m.group(2)
    return decl


def assignment_kind(rhs):
    """Classify the RHS literal of a `set udg_CastleSlot_X[i]=<rhs>` line."""
    rhs = rhs.strip()
    if re.fullmatch(r"'[^']{4}'", rhs):
        return "integer"            # 4-char rawcode -> integer in GUI vars
    if re.fullmatch(r'"[^"]*"', rhs):
        return "string"
    if re.fullmatch(r"-?\d+", rhs):
        return "integer"
    if rhs == "null":
        return "handle-null"
    if rhs.startswith("gg_unit_"):
        return "unit"
    if rhs.startswith("gg_trg_"):
        return "trigger"
    if rhs.startswith("gg_rct_") or rhs.startswith("GetRectCenter") or rhs.startswith("GetUnitLoc"):
        return "location"
    return "UNKNOWN:" + rhs


def written_kinds(j_text):
    """name -> set of assignment kinds the .j actually uses for that CastleSlot array."""
    seen = {}
    for m in re.finditer(r"set udg_CastleSlot_(\w+?)\[\d+\]=(.+)$", j_text, re.M):
        seen.setdefault(m.group(1), set()).add(assignment_kind(m.group(2)))
    return seen


def audit(j_text, rb_text):
    """Return (rows, failures). rows = [(name, declared, kinds, ok)]."""
    decl = declared_types(rb_text)
    seen = written_kinds(j_text)
    rows, failures = [], []
    for name in sorted(seen):
        d = decl.get(name, "MISSING")
        kinds = seen[name]
        ok = (d in COMPAT) and kinds.issubset(COMPAT[d])
        rows.append((name, d, kinds, ok))
        if d == "MISSING":
            failures.append(f"{name}: written by .j but NOT declared in STEP-0 table")
        elif not ok:
            failures.append(f"{name}: declared '{d}' but .j assigns {sorted(kinds)} (type-incompatible)")
    return rows, failures, decl, seen


def report(rows):
    print(f"{'ARRAY':<16}{'DECLARED':<10}{'ASSIGNED-KINDS':<28}OK?")
    for name, d, kinds, ok in rows:
        print(f"{name:<16}{d:<10}{','.join(sorted(kinds)):<28}{'OK' if ok else 'XXXX MISMATCH'}")


def selftest():
    print("=== SELFTEST: inject a type mismatch + an undeclared array, prove both caught ===")
    j_text = (
        "function InitCastleSlotData takes nothing returns nothing\n"
        "    set udg_CastleSlot_HeroType[0]='Harf'\n"          # integer-ok
        "    set udg_CastleSlot_Ally[0]=gg_unit_h00E_0459\n"   # unit-ok
        "    set udg_CastleSlot_Ally[1]=gg_trg_Boom\n"         # INJECTED: trigger into unit -> MISMATCH
        "    set udg_CastleSlot_Ghost[0]='Xxxx'\n"             # INJECTED: undeclared array
        "endfunction\n"
    )
    rb_text = (
        "| `CastleSlot_HeroType` | integer **array** | 0 | P2 | x |\n"
        "| `CastleSlot_Ally` | unit **array** | (none) | P2 | x |\n"
    )
    rows, failures, _, _ = audit(j_text, rb_text)
    report(rows)
    caught_mismatch = any("Ally:" in f and "type-incompatible" in f for f in failures)
    caught_undecl = any("Ghost:" in f and "NOT declared" in f for f in failures)
    print("\nfailures:")
    for f in failures:
        print("  -", f)
    ok = caught_mismatch and caught_undecl and len(failures) == 2
    print(f"\nSELFTEST {'PASS' if ok else 'FAIL'}  (mismatch={caught_mismatch} undeclared={caught_undecl})")
    return 0 if ok else 3


def main():
    if "--selftest" in sys.argv:
        return selftest()
    if not GEN_J.exists():
        print(f"FATAL: generated .j not found: {GEN_J}")
        return 2
    if not RUNBOOK.exists():
        print(f"FATAL: apply runbook not found: {RUNBOOK}")
        return 2
    rows, failures, decl, seen = audit(GEN_J.read_text(), RUNBOOK.read_text())
    report(rows)
    print(f"\nwritten arrays={len(seen)}  declared CastleSlot vars={len(decl)}  "
          f"contract-failures={len(failures)}")
    if failures:
        print("RESULT: FAIL — paste-contract broken:")
        for f in failures:
            print("  -", f)
        return 1
    print("RESULT: GREEN — every written udg_CastleSlot_* array is declared + type-compatible.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
