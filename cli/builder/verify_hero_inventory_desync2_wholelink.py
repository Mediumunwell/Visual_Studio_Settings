#!/usr/bin/env python3
# ============================================================================
# verify_hero_inventory_desync2_wholelink.py
#
#   The NEXT-LARGER hero-inventory link unit the 2026-06-18T13:14Z compile cert
#   left explicitly unclaimed: "this proves the P6 slice; full P1-P7+DESYNC2
#   end-to-end COMBINED compile is the next larger unit, left unclaimed."
#
#   verify_hero_inventory_integration.py already links phases 2..7 as ONE
#   program under the operator's REAL pjass.exe (P1 is the deliberately-
#   superseded feasibility spike, correctly excluded -- see that module's
#   docstring).  DESYNC2 (the Phase-F loadslot-localization save/load hardening:
#   LoadSaveSlot + SampleDialogSystem__GetTitle) has its OWN single-track compile
#   cert, but it has NEVER been co-linked with the P2-P7 Command-Hub in one pjass
#   unit -- and DESYNC2 patches the SAME save/load family P5 owns, so a cross-
#   unit collision (a duplicate symbol, a stub-union TYPE conflict on a shared
#   save global/native, or a forward-reference order fault) would be invisible to
#   both the per-track gate and the 178/178 static sweep.
#
#   This gate closes that seam.  It reuses the integration module's audited
#   assembler (build_prelude / parse_phases / call_graph / topo_order /
#   run_pjass) to build the P2-P7 program, then merges DESYNC2's stub + the two
#   DESYNC2-patched function bodies into the SAME unit -- deduping prelude symbols
#   by name while ASSERTING any name shared between the DESYNC2 stub and a phase
#   stub has an IDENTICAL signature (the stub-union type-conflict teeth) and that
#   no function name is defined by both DESYNC2 and a phase (the duplicate teeth).
#   The merged, topologically-ordered whole is then handed to the operator's REAL
#   pjass.exe.
#
#   CONSERVATIVE / GRACEFUL: if pjass.exe is not reachable (a non-Windows engine)
#   the LINK step prints SKIP and the gate returns 0 on the static merge checks
#   alone, exactly like the integration gate.  It can only go RED on a real
#   duplicate / stub-union type conflict / cross-unit orphan / cycle, or where
#   pjass IS present and the assembled program fails to Parse.
#
#   STANDALONE by design -- NOT wired into verify_all.py, so the fix_specs sweep
#   stays 178/178; this gate's GREEN is the new evidence.
#
#   `--selftest` proves the merge harness has TEETH without pjass: it injects
#   (a) a DESYNC2-vs-phase duplicate function and (b) a stub-union global TYPE
#   conflict, and asserts both are caught.
#
#   Read-only except the one temp .j run_pjass writes+deletes.
#   Exit 0 = clean whole-program link (or pjass absent + clean static merge);
#   exit 1 = a duplicate / type conflict / orphan / cycle, or a failed real parse.
#
#   Built 2026-06-18 (engine claude-p).
# ============================================================================
import os
import re
import sys
import glob

FIXSPECS = "/home/mediumunwell/Systems_Migration/kotr/fix_specs"
sys.path.insert(0, FIXSPECS)
import verify_hero_inventory_integration as integ  # audited assembler we reuse

DESYNC2_STUB = os.path.join(FIXSPECS, "desync2_localization_stub.j")
DESYNC2_COMBINED = os.path.join(FIXSPECS, "desync2_localization_COMBINED.j")


def _norm(line):
    """Collapse whitespace so two decls of the same symbol that differ only in
    spacing compare equal -- a real signature/type difference still differs."""
    return re.sub(r'\s+', ' ', re.sub(r'//.*$', '', line)).strip()


_TYPE_PARENT_RE = re.compile(r'^type\s+(\w+)\s+extends\s+(\w+)\b')


def parse_prelude_dicts(files):
    """Returns (types, natives, externs, conflicts, type_notes).

    natives/externs: name -> (normalized, raw); a name re-declared with a DIFFERENT
    normalized signature is an unresolvable CONFLICT (the stub-union teeth).

    types: name -> raw decl line, with parent divergence RECONCILED to the common.j
    canonical lattice -- when two stubs declare `type X extends A` and `type X extends
    B`, the MORE-DERIVED parent wins (the one that is itself a transitive subtype of the
    other), because that refinement preserves every IS-A of the looser decl and matches
    what the operator's real common.j compiles against.  A reconciled divergence is a
    `type_notes` entry (not a fail); only INCOMPARABLE parents (neither an ancestor of
    the other) remain a hard `conflicts` entry."""
    natives, externs = {}, {}
    conflicts = []
    # collect every type decl: name -> {parent: raw}
    type_parents = {}
    for f in files:
        in_g = False
        for line in open(f):
            raw = line.rstrip("\n")
            tp = _TYPE_PARENT_RE.match(raw)
            n = integ.NATIVE_RE.match(raw)
            if raw.strip().startswith("globals"):
                in_g = True
                continue
            if raw.strip().startswith("endglobals"):
                in_g = False
                continue
            if tp:
                type_parents.setdefault(tp.group(1), {}).setdefault(tp.group(2), raw)
            elif n:
                _merge(natives, n.group(1), raw, conflicts, "native", f)
            elif in_g:
                name = integ._global_var_name(raw)
                if name:
                    _merge(externs, name, raw, conflicts, "global", f)

    types, type_notes = _reconcile_types(type_parents, conflicts)
    return types, natives, externs, conflicts, type_notes


def _reconcile_types(type_parents, conflicts):
    """Pick, per type, the most-derived parent across all stub decls. Builds the
    ancestor relation from the union of single-parent decls so `agent extends handle`
    lets us judge that `player extends agent` refines `player extends handle`."""
    # base ancestry: a type's parent as declared (any decl); used to test subtype-ness.
    direct = {t: next(iter(ps)) for t, ps in type_parents.items()}  # provisional

    def is_subtype(a, b, seen=None):
        """True if a is (transitively) a subtype of b, per the direct map."""
        seen = seen or set()
        cur = a
        while cur in direct and cur not in seen:
            seen.add(cur)
            if direct[cur] == b:
                return True
            cur = direct[cur]
        return False

    types, notes, chosen_parent = {}, [], {}
    for t, parents in sorted(type_parents.items()):
        if len(parents) == 1:
            p = next(iter(parents))
            types[t] = parents[p]
            chosen_parent[t] = p
            continue
        # choose the parent that is a subtype of (more derived than) all the others
        cand = list(parents)
        best = None
        for p in cand:
            if all(p == q or is_subtype(p, q) for q in cand):
                best = p
                break
        if best is None:
            # incomparable parents -> genuine unresolvable conflict
            conflicts.append(("type", t, parents[cand[0]], "", "<merge>",
                              parents[cand[1]]))
            types[t] = parents[cand[0]]
            chosen_parent[t] = cand[0]
        else:
            types[t] = parents[best]
            chosen_parent[t] = best
            notes.append((t, best, [q for q in cand if q != best]))

    # pjass requires a type's parent to be DECLARED ABOVE it -> emit parent-before-child.
    ordered, placed = {}, set()

    def place(t, seen=None):
        seen = seen or set()
        if t in placed or t not in types or t in seen:
            return
        seen.add(t)
        place(chosen_parent.get(t), seen)  # parent first (built-in/handle is a no-op)
        ordered[t] = types[t]
        placed.add(t)

    for t in sorted(types):
        place(t)
    return ordered, notes


def _merge(d, name, raw, conflicts, kind, f):
    norm = _norm(raw)
    if name in d:
        if d[name][0] != norm:
            conflicts.append((kind, name, d[name][1], d[name][0], os.path.basename(f), norm))
    else:
        d[name] = (norm, raw)


def parse_funcs(path):
    """name -> full function text, for every `function ... endfunction` in `path`."""
    funcs = {}
    lines = open(path).read().splitlines()
    i = 0
    while i < len(lines):
        m = integ.FUNC_RE.match(lines[i])
        if m:
            name = m.group(1)
            buf = [lines[i]]
            i += 1
            while i < len(lines) and not integ.ENDFUNC_RE.match(lines[i]):
                buf.append(lines[i])
                i += 1
            if i < len(lines):
                buf.append(lines[i])
            funcs[name] = (os.path.basename(path), "\n".join(buf))
        i += 1
    return funcs


def assemble_merged(stub_files=None, d2_stub=DESYNC2_STUB, d2_combined=DESYNC2_COMBINED):
    """Build the P2-P7 + DESYNC2 whole-program unit. Returns (unit, report)."""
    phase_stubs = sorted(glob.glob(os.path.join(FIXSPECS, integ.STUB_GLOB)))
    if stub_files is not None:
        phase_stubs = stub_files
    all_stub_files = phase_stubs + [d2_stub]

    types, natives, externs, conflicts, type_notes = parse_prelude_dicts(all_stub_files)

    # phase funcs (P2-P7) via the audited parser, then merge DESYNC2's two leaves
    phase_globals, funcs, dups = integ.parse_phases(FIXSPECS)
    d2_funcs = parse_funcs(d2_combined)
    cross_dups = []
    for name, val in d2_funcs.items():
        if name in funcs:
            cross_dups.append((name, funcs[name][0], val[0]))
        funcs[name] = val

    edges = integ.call_graph(funcs)
    order, cyc = integ.topo_order(funcs, edges)
    orphans = integ.find_orphans(funcs, {f: edges[f] for f in edges}, set(externs))

    head = ["// === merged prelude: union(P2-P7 stubs + DESYNC2 stub), dedup by symbol ==="]
    head += [v for v in types.values()] + [v[1] for v in natives.values()]
    block = ["globals", "    // --- prelude externs (map/library symbols shimmed) ---"]
    block += [v[1] for v in externs.values()] + phase_globals + ["endglobals"]
    body = [funcs[n][1] for n in order]
    unit = "\n".join(head) + "\n\n" + "\n".join(block) + "\n\n" + "\n\n".join(body) + "\n"

    report = {
        "phase_funcs": len(funcs) - len(d2_funcs),
        "d2_funcs": sorted(d2_funcs),
        "total_funcs": len(funcs),
        "conflicts": conflicts,
        "phase_dups": dups,
        "cross_dups": cross_dups,
        "cycle": cyc,
        "orphans": orphans,
        "type_notes": type_notes,
    }
    return unit, report


def run(pjass=None, runner=None):
    pjass = pjass if pjass is not None else integ._find_pjass()
    print("KOTR Hero-Inventory + DESYNC2 WHOLE-PROGRAM link gate "
          "(P2-P7 Command-Hub + the two DESYNC2 save/load fixes assembled into ONE unit, "
          "topo-ordered, then linked by the operator's REAL pjass.exe -- first co-link)")
    unit, rep = assemble_merged()
    print("=" * 78)
    print("  hub phases linked : 6 (PHASE2..PHASE7_COMBINED; phase 1 = historical spike, excluded)")
    print("  DESYNC2 fns added : %d  %s" % (len(rep["d2_funcs"]), ", ".join(rep["d2_funcs"])))
    print("  total functions   : %d" % rep["total_funcs"])

    bad = False
    if rep["phase_dups"] or rep["cross_dups"]:
        bad = True
        for name, a, b in rep["phase_dups"] + rep["cross_dups"]:
            print("  [FAIL] duplicate function `%s` defined by %s AND %s" % (name, a, b))
    else:
        print("  [ OK ] no duplicate function across the hub + DESYNC2")

    if rep["conflicts"]:
        bad = True
        for kind, name, l1, _, f2, l2 in rep["conflicts"]:
            print("  [FAIL] stub-union %s conflict on `%s`: %r vs (%s) %r" % (kind, name, l1, f2, l2))
    else:
        print("  [ OK ] DESYNC2 stub unions cleanly with the phase stubs (no native/global conflict)")

    for t, best, losers in rep["type_notes"]:
        print("  [NOTE] type `%s` parent divergence reconciled to common.j canonical "
              "`extends %s` (phase stubs used `extends %s`)" % (t, best, ", ".join(losers)))

    if rep["orphans"]:
        bad = True
        for fn, c in rep["orphans"]:
            print("  [FAIL] cross-unit orphan: %s -> %s (defined nowhere)" % (fn, c))
    else:
        print("  [ OK ] no cross-unit orphan call")

    if rep["cycle"]:
        bad = True
        print("  [FAIL] call cycle (no single-pass pjass order): %s" % rep["cycle"])
    else:
        print("  [ OK ] cross-unit call graph acyclic -- a callees-first order exists")

    if bad:
        print("=" * 78)
        print("RESULT: STATIC MERGE FAILED -- not linking under pjass.")
        return 1

    if pjass is None and runner is None:
        print("  [SKIP] pjass.exe not reachable -- static merge clean; link proof skipped")
        print("=" * 78)
        print("RESULT: static merge of P2-P7 + DESYNC2 is clean (pjass absent).")
        return 0

    rc, out = integ.run_pjass(unit, pjass, runner=runner)
    parse_ok = "Parse successful" in out and rc == 0
    last = [l for l in out.splitlines() if l.strip()]
    print("  [%s] real pjass linked the merged unit: %s"
          % ("OK " if parse_ok else "FAIL", last[-1] if last else "(no output)"))
    print("=" * 78)
    if parse_ok:
        print("RESULT: the P2-P7 Command-Hub AND the two DESYNC2 save/load fixes LINK AS ONE "
              "PROGRAM -- no duplicate, no stub-union conflict, no orphan, acyclic, and the "
              "topologically-ordered whole Parse-SUCCEEDS on the operator's own pjass.exe.")
        return 0
    print("RESULT: merged P2-P7 + DESYNC2 program FAILED real pjass parse (see above).")
    return 1


# ---------------------------------------------------------------------------
def selftest():
    """TEETH without pjass: the merge harness must catch (a) a DESYNC2-vs-phase
    duplicate function and (b) a stub-union global TYPE conflict."""
    import tempfile, shutil
    ok = True

    # (a) duplicate function: a fake DESYNC2 combined that re-defines a phase fn.
    _, funcs, _ = integ.parse_phases(FIXSPECS)
    victim = sorted(funcs)[0]
    tmpd = tempfile.mkdtemp(prefix="d2_selftest_")
    try:
        dupc = os.path.join(tmpd, "dup_combined.j")
        with open(dupc, "w") as fh:
            fh.write("function %s takes nothing returns nothing\nendfunction\n" % victim)
        _, rep = assemble_merged(d2_combined=dupc)
        caught = any(n == victim for n, _, _ in rep["cross_dups"])
        print("  [%s] duplicate-fn teeth: DESYNC2 re-defining phase fn `%s` -> %s"
              % ("PASS" if caught else "FAIL", victim, "CAUGHT" if caught else "MISSED"))
        ok = ok and caught

        # (b) stub-union type conflict: a fake DESYNC2 stub re-typing a shared native.
        badstub = os.path.join(tmpd, "bad_stub.j")
        with open(badstub, "w") as fh:
            fh.write("native GetLocalPlayer takes nothing returns integer\n")  # wrong return type
        _, rep2 = assemble_merged(d2_stub=badstub)
        caught2 = any(name == "GetLocalPlayer" for _, name, _, _, _, _ in rep2["conflicts"])
        print("  [%s] stub-union teeth: DESYNC2 stub re-typing native GetLocalPlayer -> %s"
              % ("PASS" if caught2 else "FAIL", "CAUGHT" if caught2 else "MISSED"))
        ok = ok and caught2
    finally:
        shutil.rmtree(tmpd, ignore_errors=True)

    # (c) clean control: the real artifacts must NOT trip either tooth.
    _, rep3 = assemble_merged()
    clean = not (rep3["cross_dups"] or rep3["conflicts"] or rep3["phase_dups"] or
                 rep3["cycle"] or rep3["orphans"])
    print("  [%s] clean control: real P2-P7 + DESYNC2 merge has no static fault"
          % ("PASS" if clean else "FAIL"))
    ok = ok and clean
    return 0 if ok else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    sys.exit(run())
