#!/usr/bin/env python3
r"""
builder_greenlight.py — the ONE full-surface green-light for the KOTR builder.
Built 2026-06-18 by KOTR Builder (engine claude-p).

WHY (the gap this closes — flagged as the unclaimed NEXT by the 21:34Z aggregate-sweep handoff):
  The builder's verification surface is split across TWO independent sweeps that live in TWO
  different directories and answer TWO different questions:

    1. cli/builder/verify_builder_gates.py   — the 20 standalone ANCHOR BINDERS (+ a discovery
       cross-check). They bind every documentation source-of-truth (recon binders, apply-runbooks,
       per-phase build specs, the hero-select divergence catalog, the command-hub spec, the
       castleslot global contract, the localplayer/desync2 link gates) BOTH WAYS against the live
       `_extract_v050/war3map.j`. "Are all the DOCS still byte-exact vs the live extract?"

    2. fix_specs/verify_all.py                — the 178 PASTE-SET regression gates. pjass-compile
       the A->E combined paste set, prove the anchors byte-exact, the set fully wired, the union
       conflict-free. "Does the SHIPPABLE paste set still compile + link as one program?"

  Neither sweep knows the other exists. Confirming "the whole builder is green" today means
  remembering to `cd` into two trees and run two commands — and if you forget one, half the
  surface is unverified while the table you DID run says GREEN. That is exactly the silent-rot
  class the binders themselves were built to kill, one level up.

  This runner closes it: ONE command, run from anywhere, that executes BOTH sweeps as
  subprocesses and returns a single GREEN verdict iff BOTH exit 0 — the builder's full
  green-light before a commit / handoff.

WHAT it does (teeth):
  * Runs each sweep as a subprocess, captures exit code + the most informative SWEEP line.
  * GREEN (exit 0) ONLY if EVERY sweep exits 0 AND every sweep script was actually found+runnable
    (a missing sweep is RED, never a silent skip).
  * On RED, names the first failing sweep and replays its full output so the failure is actionable.
  * --selftest proves the AGGREGATOR bites: it composes the same logic over synthetic exit-0 /
    exit-1 sub-sweeps and asserts mixed -> RED naming the offender, all-zero -> GREEN. It does
    NOT touch the real gates, so the selftest is honest whatever the live sweeps say today.

READ-ONLY: runs other scripts as subprocesses; touches no .w3x / .j / live extract itself.

Run:        python3 builder_greenlight.py
Self-test:  python3 builder_greenlight.py --selftest
"""

import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent

# fix_specs lives outside this repo; resolve robustly (env override -> conventional home path).
FIX_SPECS = Path(
    os.environ.get("KOTR_FIX_SPECS", str(Path.home() / "Systems_Migration" / "kotr" / "fix_specs"))
)

# (label, cwd, argv, one-line description) — the full builder verification surface.
SWEEPS = [
    (
        "builder-gates",
        HERE,
        [sys.executable, str(HERE / "verify_builder_gates.py")],
        "20 standalone anchor binders + discovery cross-check (docs <-> live extract)",
    ),
    (
        "fix_specs",
        FIX_SPECS,
        [sys.executable, str(FIX_SPECS / "verify_all.py")],
        "178 paste-set regression gates (pjass-compile + wiring + union)",
    ),
]


def _headline(output: str) -> str:
    """Pull the most informative line out of a sweep's stdout.

    Both sweeps end with a `SWEEP:` verdict line; fall back to the last non-separator,
    non-blank line so a sweep that rewords still reports SOMETHING."""
    lines = [ln.rstrip() for ln in output.splitlines()]
    for ln in reversed(lines):
        s = ln.strip()
        if s.startswith("SWEEP:"):
            return s[len("SWEEP:"):].strip()
    for ln in reversed(lines):
        s = ln.strip()
        if s and set(s) - set("=-_ "):  # not a pure separator rule
            return s
    return "(no output)"


def _run_sweep(label, cwd, argv):
    """Run one sweep; return (status, rc, secs, headline, combined_output)."""
    script = Path(argv[-1])
    if not script.is_file():
        return ("MISSING", None, 0.0, f"sweep script not found: {script}", "")
    if not Path(cwd).is_dir():
        return ("MISSING", None, 0.0, f"sweep cwd not found: {cwd}", "")
    t0 = time.time()
    try:
        proc = subprocess.run(argv, cwd=str(cwd), capture_output=True, text=True)
        rc, out, err = proc.returncode, proc.stdout, proc.stderr
    except Exception as exc:  # pragma: no cover - defensive
        rc, out, err = 99, "", f"{type(exc).__name__}: {exc}"
    secs = time.time() - t0
    combined = out + (("\n" + err) if err.strip() else "")
    status = "PASS" if rc == 0 else "FAIL"
    return (status, rc, secs, _headline(out), combined)


def _aggregate(sweeps):
    """Run each (label, cwd, argv[, desc]) sweep; return (results, first_failure)."""
    results = []  # (label, status, rc, secs, headline, combined)
    first_failure = None
    for label, cwd, argv, *_ in sweeps:
        status, rc, secs, headline, combined = _run_sweep(label, cwd, argv)
        results.append((label, status, rc, secs, headline, combined))
        if status != "PASS" and first_failure is None:
            first_failure = (label, combined, f"{label}: {'MISSING' if rc is None else f'exit {rc}'}")
    return results, first_failure


def _print_table(results):
    print()
    print(f"{'SWEEP':<16} {'STATUS':<7} {'EXIT':<5} {'TIME':<9} HEADLINE")
    print("-" * 110)
    for label, status, rc, secs, headline, _out in results:
        rc_s = "-" if rc is None else str(rc)
        head = headline if len(headline) <= 70 else headline[:67] + "..."
        print(f"{label:<16} {status:<7} {rc_s:<5} {secs:>7.2f}s  {head}")
    print("-" * 110)


def selftest() -> int:
    """Prove the AGGREGATOR reports RED when any sub-sweep exits non-zero, GREEN when all pass."""
    import tempfile
    print("SELFTEST: composing the aggregator over synthetic exit-0 / exit-1 sub-sweeps ...")
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        ok_py = td / "sweep_ok.py"
        bad_py = td / "sweep_bad.py"
        ok_py.write_text("print('SWEEP: GREEN — synthetic ok')\nraise SystemExit(0)\n")
        bad_py.write_text("print('SWEEP: RED — synthetic fail')\nraise SystemExit(1)\n")
        ok_cmd = [sys.executable, str(ok_py)]
        bad_cmd = [sys.executable, str(bad_py)]

        # 1) mixed -> RED, first failure named, the passing sweeps still PASS.
        mixed = [("ok-a", td, ok_cmd), ("bad-b", td, bad_cmd), ("ok-c", td, ok_cmd)]
        results, first_failure = _aggregate(mixed)
        mixed_ok = (
            first_failure is not None
            and first_failure[0] == "bad-b"
            and any(l == "ok-a" and s == "PASS" for l, s, *_ in results)
            and any(l == "bad-b" and s == "FAIL" for l, s, *_ in results)
            and any(l == "ok-c" and s == "PASS" for l, s, *_ in results)
        )

        # 2) all-zero -> GREEN (no first failure).
        all_ok = [("ok-a", td, ok_cmd), ("ok-b", td, ok_cmd)]
        _r2, ff2 = _aggregate(all_ok)
        green_ok = ff2 is None

        # 3) a missing sweep script -> RED (never a silent skip).
        missing = [("gone", td, [sys.executable, str(td / "does_not_exist_xyz.py")])]
        r3, ff3 = _aggregate(missing)
        missing_ok = ff3 is not None and any(l == "gone" and s == "MISSING" for l, s, *_ in r3)

    ok = mixed_ok and green_ok and missing_ok
    print(f"SELFTEST: mixed->RED+offender-named={mixed_ok}  all-zero->GREEN={green_ok}  "
          f"missing-script->RED={missing_ok}")
    print(f"SELFTEST: {'PASS' if ok else 'FAIL'} — aggregator "
          f"{'correctly bites' if ok else 'FAILED'} on every synthetic case.")
    return 0 if ok else 1


def main() -> int:
    argv = sys.argv[1:]
    if "--selftest" in argv:
        return selftest()

    print("=" * 110)
    print("KOTR BUILDER FULL GREEN-LIGHT — builder_greenlight.py")
    print(f"  builder gates : {HERE}")
    print(f"  fix_specs     : {FIX_SPECS}")
    print(f"  python        : {sys.executable}  ({sys.version.split()[0]})")
    print("=" * 110)

    results, first_failure = _aggregate(SWEEPS)
    _print_table(results)

    n = len(results)
    n_pass = sum(1 for _, s, *_ in results if s == "PASS")

    if first_failure is not None:
        flabel, foutput, fsummary = first_failure
        print(f"GREEN-LIGHT: RED — {n_pass}/{n} sweeps passed. First failing surface: {fsummary}")
        if foutput.strip():
            print(f"\n----- full output of first failing sweep ({flabel}) -----")
            print(foutput.rstrip())
        return 1

    print(f"GREEN-LIGHT: GREEN — all {n}/{n} sweeps EXIT 0. The full builder verification surface "
          f"is clean: every documentation source-of-truth is byte-exact vs the live extract AND "
          f"the shippable paste set compiles + links as one program. Safe to commit / hand off.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
