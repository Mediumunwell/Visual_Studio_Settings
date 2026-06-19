#!/usr/bin/env python3
r"""
verify_builder_gates.py — the single AGGREGATE SWEEP for the cli/builder standalone gates.
Built 2026-06-18 by KOTR Builder (engine claude-p).

WHY (the gap this closes):
  The fix_specs/ regression sweep (verify_all.py, 178/178) guards the v0.50 PASTE SET —
  it knows nothing about the standalone gates that live HERE in cli/builder (count == the
  GATES registry below). Each binds a different documentation SOURCE-OF-TRUTH (recon binders, apply-runbooks,
  per-phase build specs, the hero-select divergence catalog, the command-hub spec, the
  castleslot global contract, the localplayer-sync / desync2 link gates) BOTH WAYS against
  the live `_extract_v050/war3map.j`. Each was wired + cert'd one at a time and then run
  individually, by hand. There was NO single command that answers the one question that
  matters across a build session:

      "Are ALL of the builder's anchor binders STILL GREEN against the live extract?"

  Without it, a doc edit or an extract re-ground can rot one binder and no sweep catches it
  until someone happens to re-run that exact gate. This runner closes that — one command,
  one unified table, one GREEN/RED verdict over the whole standalone set.

WHAT it does (two layers of teeth):
  1. REGISTRY SWEEP — runs every gate in GATES as a subprocess, EXIT 0 == PASS, builds the
     verify_all.py-style table, returns 1 on the first non-zero exit.
  2. DISCOVERY CROSS-CHECK — globs `verify_*.py` on disk (excluding this runner) and compares
     to the GATES registry. Any on-disk gate NOT registered is itself a RED condition. This is
     the twin of the rot the binders fight: a NEW gate shipped but never added here would
     otherwise be silently skipped forever. The registry can never go quietly stale.

  --selftest proves layer 1 has teeth: it injects a synthetic always-failing gate into a temp
  dir and confirms the runner reports RED and names it as the first offender.

READ-ONLY: runs other gates as subprocesses; touches no .w3x / .j / live extract itself.
"""

import glob
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
SELF = os.path.basename(__file__)

# The standalone cli/builder gates, grouped by the source-of-truth each binds.
GATES = [
    # --- hero-inventory track ---
    "verify_hero_inventory_phase0_recon_anchors.py",
    "verify_hero_inventory_runbook_desync2_anchors.py",
    "verify_hero_inventory_runbook_hearthclock_anchors.py",
    "verify_hero_inventory_runbook_menuitem_collision.py",
    "verify_hero_inventory_runbook_phasefile_anchors.py",
    "verify_hero_inventory_phasefile_anchors.py",
    "verify_hero_inventory_desync2_wholelink.py",
    "verify_hero_inventory_localplayer_sync.py",
    # --- companion-AI track ---
    "verify_companion_ai_phase0_recon_anchors.py",
    "verify_companion_ai_runbook_anchors.py",
    "verify_companion_ai_phasefile_anchors.py",
    # --- hero-select / Track-4 ---
    "verify_hero_select_phase0_recon_anchors.py",
    "verify_hero_select_p2_runbook_anchors.py",
    "verify_hero_select_divergence_catalog_anchors.py",
    "verify_hero_select_p2_generated_j.py",
    "verify_hero_select_p2_crew_vs_authority.py",
    "verify_hero_select_p2_initcall_anchor.py",
    "verify_hero_select_p2_step2_heroref_anchor.py",
    "verify_hero_select_p2_merlin_extrashook_anchor.py",
    "verify_hero_select_p2_gawain_extrashook_anchor.py",
    "verify_hero_select_p2_spawnloc_faceloc_anchor.py",
    "verify_hero_select_p2_allyrescueinvuln_anchor.py",
    "verify_hero_select_p2_item_loadout_anchor.py",
    "verify_hero_select_p2_avail_anchor.py",
    "verify_hero_select_p2_spawnability_anchor.py",
    "verify_castleslot_global_contract.py",
    # --- command-hub spec + classwide localplayer alloc ---
    "verify_command_hub_spec_grounding.py",
    "verify_localplayer_synced_alloc_classwide.py",
    # --- we_diffs bug-fix apply runbook ---
    "verify_we_diffs_runbook_anchors.py",
]


def _headline(output: str) -> str:
    """Pull the most informative summary line out of a gate's stdout.

    Builder gates end with a `RESULT:` line; fall back to the last non-separator, non-blank
    line so a gate that rewords still reports SOMETHING rather than an empty cell."""
    lines = [ln.rstrip() for ln in output.splitlines()]
    for ln in reversed(lines):
        s = ln.strip()
        if s.startswith("RESULT:"):
            return s[len("RESULT:"):].strip()
    for ln in reversed(lines):
        s = ln.strip()
        if s and set(s) - set("=-_ "):  # not a pure separator rule
            return s
    return "(no output)"


def _discover_unregistered():
    """Every verify_*.py on disk (minus this runner) that is NOT in GATES — registry rot."""
    on_disk = {
        os.path.basename(p)
        for p in glob.glob(os.path.join(HERE, "verify_*.py"))
    }
    on_disk.discard(SELF)
    return sorted(on_disk - set(GATES))


def _run_gate(gate, gate_dir=HERE):
    path = os.path.join(gate_dir, gate)
    if not os.path.isfile(path):
        return ("MISSING", None, 0.0, "gate file not found", "")
    t0 = time.time()
    try:
        proc = subprocess.run(
            [sys.executable, path],
            cwd=gate_dir,
            capture_output=True,
            text=True,
        )
        rc, out, err = proc.returncode, proc.stdout, proc.stderr
    except Exception as exc:  # pragma: no cover - defensive
        rc, out, err = 99, "", f"{type(exc).__name__}: {exc}"
    secs = time.time() - t0
    combined = out + (("\n" + err) if err.strip() else "")
    status = "PASS" if rc == 0 else "FAIL"
    return (status, rc, secs, _headline(out), combined)


def _sweep(gates, gate_dir=HERE, verbose=False):
    """Run a list of gates; return (results, first_failure)."""
    results = []  # (gate, status, rc, secs, headline, output)
    first_failure = None
    for gate in gates:
        status, rc, secs, headline, combined = _run_gate(gate, gate_dir)
        if verbose:
            print(f"\n----- {gate} (exit {rc}) -----")
            print(combined.rstrip())
        results.append((gate, status, rc, secs, headline, combined))
        if (status != "PASS") and first_failure is None:
            first_failure = (gate, combined, f"{gate}: exit {rc}")
    return results, first_failure


def _print_table(results):
    print()
    print(f"{'GATE':<52} {'STATUS':<7} {'EXIT':<5} {'TIME':<8} HEADLINE")
    print("-" * 110)
    for gate, status, rc, secs, headline, _out in results:
        rc_s = "-" if rc is None else str(rc)
        head = headline if len(headline) <= 42 else headline[:39] + "..."
        print(f"{gate:<52} {status:<7} {rc_s:<5} {secs:>6.2f}s  {head}")
    print("-" * 110)


def selftest() -> int:
    """Prove the runner reports RED when a registered gate exits non-zero."""
    import tempfile
    print("SELFTEST: injecting a synthetic always-failing gate ...")
    with tempfile.TemporaryDirectory() as td:
        good = "verify_synthetic_ok.py"
        bad = "verify_synthetic_fail.py"
        with open(os.path.join(td, good), "w") as f:
            f.write("import sys\nprint('RESULT: synthetic ok')\nsys.exit(0)\n")
        with open(os.path.join(td, bad), "w") as f:
            f.write("import sys\nprint('RESULT: synthetic FAIL')\nsys.exit(1)\n")
        results, first_failure = _sweep([good, bad], gate_dir=td)
        ok = (
            first_failure is not None
            and first_failure[0] == bad
            and any(g == good and s == "PASS" for g, s, *_ in results)
            and any(g == bad and s == "FAIL" for g, s, *_ in results)
        )
    print(f"SELFTEST: {'PASS' if ok else 'FAIL'} — "
          f"runner {'correctly flags' if ok else 'FAILED to flag'} the failing gate as "
          f"first offender, passing gate stays PASS.")
    return 0 if ok else 1


def main() -> int:
    argv = sys.argv[1:]
    if "--selftest" in argv:
        return selftest()
    verbose = "-v" in argv or "--verbose" in argv

    print("=" * 110)
    print("KOTR cli/builder STANDALONE-GATE AGGREGATE SWEEP — verify_builder_gates.py")
    print(f"  cwd: {HERE}")
    print(f"  python: {sys.executable}  ({sys.version.split()[0]})")
    print("=" * 110)

    # ---- layer 2: discovery cross-check (registry can't go stale) --------
    unregistered = _discover_unregistered()

    # ---- layer 1: registry sweep ----------------------------------------
    results, first_failure = _sweep(GATES, verbose=verbose)
    _print_table(results)

    n = len(results)
    n_pass = sum(1 for _, s, *_ in results if s == "PASS")

    red = False
    if first_failure is not None:
        red = True
        fgate, foutput, fsummary = first_failure
        print(f"SWEEP: RED — {n_pass}/{n} gates passed. First offender: {fsummary}")
        if foutput.strip():
            print(f"\n----- full output of first failing gate ({fgate}) -----")
            print(foutput.rstrip())

    if unregistered:
        red = True
        print(f"\nDISCOVERY: RED — {len(unregistered)} verify_*.py gate(s) on disk are NOT "
              f"registered in GATES (would be silently skipped):")
        for g in unregistered:
            print(f"    - {g}")
        print("  Fix: add each to the GATES list in verify_builder_gates.py.")

    if red:
        return 1

    print(f"SWEEP: GREEN — all {n}/{n} standalone builder gates EXIT 0, and every "
          f"verify_*.py on disk is registered. All documentation source-of-truth binders "
          f"are byte-exact vs the live _extract_v050/war3map.j.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
