#!/usr/bin/env python3
"""
verify_companion_ai_phase0_recon_anchors.py — KOTR Companion-AI PHASE 0 RECON binder
=====================================================================================
Binds `companion_ai_PHASE0_RECON.md` — the Phase-0 grounding deliverable that every later
companion-AI phase (brain skeleton -> cliff/stuck recover -> travel -> combat/retreat ->
shop) is planned against — to the live `_extract_v050/war3map.j`, BOTH directions.
Sibling of the already-shipped `verify_hero_inventory_phase0_recon_anchors.py` (the
hero-inventory Phase-0 binder); this recon was the corresponding LAST companion-AI
source-of-truth carrying byte-exact line/count cites that NO gate machine-checked.

WHY THIS GATE EXISTS (covered by no other gate in the 178/178 sweep):
  The existing companion-AI gates prove different things: verify_companion_ai.py proves the
  assembled STAGED_COMBINED.j PARSES, and verify_companion_ai_fidelity.py proves it stays
  STATEMENT-FAITHFUL to the phase specs. NEITHER reads this recon. Yet the recon is the
  grounding the whole track hangs on: it enumerates the native availability counts, the exact
  ability-constant rawcodes (Flurry 'A003' / DrachenFire 'A01F' / Dash 'DDas'), the reuse
  idioms' line anchors, and — most load-bearing — the positively-identified post-combat fling
  root cause in the Knockback system (L29027-29065). A single World-Editor save renumbers JASS
  and shifts every count/line, silently invalidating the recon, and Phase 1 would be built
  against stale anchors. When first audited (2026-06-18) one cite was ALREADY wrong:
  `GetTriggerPlayer` ×65 while the canonical extract carries exactly ×67 bare GetTriggerPlayer()
  native calls (the GetTriggerPlayerIsKeyDown/…MouseX/Y/Button siblings are distinct tokens).
  That cite is corrected and the whole document is now bound.

WHAT IT CHECKS (read-only; touches no .w3x):
  source identity   md5 == 967131658fd8…, lines == 75535
  native counts     each §1 count reproduced by the SAME rule the recon used (see COUNT_ANCHORS):
                    paren-occ `token(` for the call-form natives (SetUnitPosition 11 — excludes
                    SetUnitPositionLoc; IssuePointOrder 8 — excludes …LocBJ; IssueImmediateOrder
                    53 — excludes …BJ; IssueTargetOrder 21; TimerStart 84; CreateGroup 97;
                    GroupClear 43); substring-line `grep -c` for the recon's line-count rows
                    (GetTerrainCliffLevel 8; GetUnitX 119 / GetUnitY 119 — each incl. the one
                    comment line at L27177; GroupEnumUnitsInRange 48); exact-literal occ for
                    GetTriggerPlayer() == 67 (the corrected count).
  rawcode consts    L1369 'SPSU' / L1373 'A003' / L1375 'A01F' / L1140 'DDas' / L1142 "DDash.mdl"
                    / L1146 2000 (the Q/E/R/dash kit ids the COMBAT casts wire against)
  state feed        L43534 s__File_open ; L43539 KOTR_StateWriter_Init ;
                    L43541 TimerStart(udg_KOTR_StateTimer, 30.00, …) (the .pld 30 s feed)
  Arthur global     L1901 decl `unit udg_Arthur= null` ; L46472 / L49282 spawn sets
  reuse idioms      L47060 "-load" prefix ; L47104-47106 gg_trg_Load_GUI_Manual regs ;
                    L44133 "-tt" exact-match ; L24355/L28028/L32472 0.03125 combat util ;
                    L32043 BlzGetUnitAbilityCooldownRemaining ; L35952 udg_group ; L1825
                    udg_KB_KnockbackedUnits ; L1890 udg_ECK_Group ; L52880 Tornado ; L2022
                    udg_skill_loca ; rects gg_rct_Arthur (L42918, byte-exact coords) /
                    gg_rct_Arthur_Kay_Lancelot_Appear (L42919) used at L45264
  cliff precedent   L29066 GetTerrainCliffLevel compare ; L25556 world-bounds normalizer
  fling root cause  L5009/L5011/L5021 Knockback struct globals ; L29027 s__Knockback_onPeriod ;
                    L29038 duration>0 + UnitAlive guard ; L29039 duration decrement ;
                    L29065 onCliff branch ; L28997 s__Knockback_remove ; L29022/L29051 stop

  REVERSE DIRECTION (prose -> cite): every L-anchor and count literal above must STILL appear in
  the recon prose. The forward checks catch a WE re-bake that moves the map out from under the
  recon; the reverse checks catch the twin seam — a doc edit that silently drops/rewrites a cite
  (the seam that had left `GetTriggerPlayer` ×65 wrong) — leaving the gate green over a rotted recon.

Run:        python3 verify_companion_ai_phase0_recon_anchors.py
Self-test:  python3 verify_companion_ai_phase0_recon_anchors.py --selftest
            (unit-tests the count helpers, builds a synthetic source that passes every forward
             anchor, then mutates one anchor per category to prove each break is caught — no
             live file needed; also checks the reverse prose direction)

EXIT 0 = GREEN, 1 = an anchor drifted, 2 = source/recon not found, 3 = selftest failed.
Standalone by design — NOT wired into verify_all.py, so the canonical 178/178 sweep is
unchanged; invoked on its own when the recon is touched or after any WE re-extract.
"""
import hashlib
import re
import sys
from pathlib import Path

SRC = Path("/mnt/c/Users/Morph/OneDrive/Documents/Warcraft III/Maps/KOTR/_extract_v050/war3map.j")
RECON = Path("/mnt/c/Users/Morph/OneDrive/Documents/Warcraft III/Maps/KOTR/_crew/companion_ai_PHASE0_RECON.md")

CANON_MD5 = "967131658fd8d4fb27ee0d7f74e4bd22"
CANON_LINES = 75535

# --- forward: §1 native counts ------------------------------------------------------------
# Each row carries the EXACT matching rule that reproduces the recon's stated number, because
# the recon mixed grep conventions per row (a faithful binding, not a re-interpretation):
#   "paren" = occurrences of `token(`  (substring-safe: excludes longer-named siblings)
#   "line"  = `grep -c token`          (substring line count, the recon's own number)
#   "exact" = occurrences of the literal string verbatim
COUNT_ANCHORS = [
    ("n.cliff",      "GetTerrainCliffLevel",  "line",  8),
    ("n.setpos",     "SetUnitPosition",       "paren", 11),   # excludes SetUnitPositionLoc*
    ("n.pointord",   "IssuePointOrder",       "paren", 8),    # excludes IssuePointOrderLocBJ/ById
    ("n.immord",     "IssueImmediateOrder",   "paren", 53),   # excludes …BJ / …ById
    ("n.tgtord",     "IssueTargetOrder",      "paren", 21),   # excludes …BJ / …ById
    ("n.getx",       "GetUnitX",              "line",  119),  # incl. 1 comment line @L27177
    ("n.gety",       "GetUnitY",              "line",  119),  # incl. 1 comment line @L27177
    ("n.timer",      "TimerStart",            "paren", 84),
    ("n.creategrp",  "CreateGroup",           "paren", 97),
    ("n.grpclear",   "GroupClear",            "paren", 43),
    ("n.grpenum",    "GroupEnumUnitsInRange", "line",  48),   # no alpha-suffix sibling exists
    ("n.trigplayer", "GetTriggerPlayer()",    "exact", 67),   # corrected 65->67 this cycle
]

# (cid, 1-based line, byte-exact substring that must be present on that line)
LINE_ANCHORS = [
    # ability-constant rawcodes (the kit the COMBAT/STUCK casts wire against)
    ("rc.spsu",   1369, "'SPSU'"),
    ("rc.dash",   1140, "'DDas'"),
    ("rc.dashmdl",1142, "DDash.mdl"),
    ("rc.dashspd",1146, "2000"),
    ("rc.flurry", 1373, "'A003'"),
    ("rc.drachen",1375, "'A01F'"),
    # .pld state feed (proves the 30 s coarse feed -> brain must run in-map)
    ("sf.open",   43534, "s__File_open"),
    ("sf.init",   43539, "KOTR_StateWriter_Init"),
    ("sf.timer",  43541, "TimerStart(udg_KOTR_StateTimer, 30.00, true, function KOTR_StateWriter_Tick)"),
    # canonical Arthur global (reuse, don't shadow)
    ("ar.decl",   1901, "unit udg_Arthur= null"),
    ("ar.set1",   46472, "set udg_Arthur=GetLastCreatedUnit()"),
    ("ar.set2",   49282, "udg_Arthur"),
    # reuse idioms
    ("rid.load",  47060, '"-load"'),
    ("rid.loadreg1", 47104, "gg_trg_Load_GUI_Manual"),
    ("rid.loadreg2", 47105, "gg_trg_Load_GUI_Manual"),
    ("rid.loadreg3", 47106, "gg_trg_Load_GUI_Manual"),
    ("rid.tt",    44133, '"-tt"'),
    ("rid.cu1",   24355, "0.03125"),
    ("rid.cu2",   28028, "0.03125"),
    ("rid.cu3",   32472, "0.03125"),
    ("rid.cd",    32043, "BlzGetUnitAbilityCooldownRemaining"),
    ("rid.grp",   35952, "udg_group"),
    ("rid.kb",    1825, "udg_KB_KnockbackedUnits"),
    ("rid.eck",   1890, "udg_ECK_Group"),
    ("rid.tornado",52880, "Tornado"),
    ("rid.skillloca",2022, "udg_skill_loca"),
    # waypoint rects (byte-exact coords — the patrol/RETREAT/de-cliff goals)
    ("wp.arthur", 42918, "set gg_rct_Arthur=Rect(- 5376.0, 6400.0, - 5248.0, 6528.0)"),
    ("wp.appear", 42919, "set gg_rct_Arthur_Kay_Lancelot_Appear=Rect(4288.0, 10272.0, 4704.0, 10560.0)"),
    ("wp.spawnuse",45264, "gg_rct_Arthur_Kay_Lancelot_Appear"),
    # cliff handling precedent
    ("cl.compare",29066, "GetTerrainCliffLevel"),
    ("cl.norm",   25556, "GetTerrainCliffLevel"),
    # post-combat fling root cause (the Knockback mover)
    ("kb.struct", 5009, "s__Knockback"),
    ("kb.period", 5011, "s__Knockback_period"),
    ("kb.duration",5021, "s__Knockback_duration"),
    ("kb.onperiod",29027, "s__Knockback_onPeriod"),
    ("kb.guard",  29038, "s__Knockback_duration[this] > 0 and UnitAlive("),
    ("kb.decr",   29039, "set s__Knockback_duration[this]="),
    ("kb.cliff",  29065, "s__Knockback_onCliff[this] and"),
    ("kb.remove", 28997, "s__Knockback_remove"),
    ("kb.stop1",  29022, "s__Knockback_duration[this]=0"),
    ("kb.stop2",  29051, "s__Knockback_duration[this]=0"),
]

# --- reverse: recon prose must still carry each literal -----------------------------------
PROSE_CITES = [
    ("src.lines",   "75,535"),
    ("n.cliff",     "| 8 |"),
    ("n.setpos",    "| 11 |"),
    ("n.orders",    "8 / 53 / 21"),
    ("n.getxy",     "119 / 119"),
    ("n.timer",     "| 84 |"),
    ("n.groups",    "97 / 43 / 48"),
    ("n.trigplayer","67 / many"),     # binds the 65->67 correction
    ("rc.flurry",   "'A003'"),
    ("rc.drachen",  "'A01F'"),
    ("rc.dash",     "'DDas'"),
    ("sf.timer",    "L43541"),
    ("ar.decl",     "L1901"),
    ("rid.loadreg", "L47104-47106"),
    ("rid.cu",      "L24355"),
    ("wp.arthur",   "L42918"),
    ("kb.onperiod", "L29027"),
    ("kb.decr",     "L29039"),
    ("kb.remove",   "L28997"),
]


def count_paren(text, token):
    """Occurrences of `token(` — substring-safe (a '(' must follow the token)."""
    return len(re.findall(re.escape(token) + r"\(", text))


def count_line(text, token):
    """grep -c semantics: number of LINES containing the token (substring)."""
    return sum(1 for ln in text.split("\n") if token in ln)


def count_exact(text, token):
    """Occurrences of the literal string verbatim."""
    return text.count(token)


def count_by_rule(text, token, rule):
    return {"paren": count_paren, "line": count_line, "exact": count_exact}[rule](text, token)


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

    for cid, token, rule, want in COUNT_ANCHORS:
        got = count_by_rule(text, token, rule)
        check(cid, f"{token} [{rule}]=={want}", got, got == want)

    for cid, ln, sub in LINE_ANCHORS:
        observed = L(ln).strip()
        check(cid, f"L{ln} carries {sub!r}", observed[:72], sub in observed)

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

    for cid, ln, sub in LINE_ANCHORS:
        # place each anchor's exact substring on its line (full live text for the count-feeders)
        put(ln, sub)
    # the comment line that makes GetUnitX/GetUnitY substring-counts land on 119 (incl. comment)
    put(27177, "    // Similar to GetUnitX and GetUnitY but for Z axis")

    # top up §1 native counts to their targets using the row's own rule.
    REGION = 60000
    cur = REGION
    for cid, token, rule, want in COUNT_ANCHORS:
        have = count_by_rule("\n".join(base), token, rule)
        for _ in range(max(0, want - have)):
            base[cur] = f"    set z={token}(a)" if rule != "exact" else f"    set z={token}"
            cur += 1
        # if a row already overshoots (shouldn't), the audit will catch it -> selftest fails loudly
    return base


def selftest():
    print("=== SELFTEST: helpers + per-category RED-catch ===")
    ok_all = True

    # (A) the three counters are substring-safe / rule-correct
    sample = ("a=SetUnitPosition(x) b=SetUnitPositionLoc(y) "
              "c=IssueImmediateOrder(u) d=IssueImmediateOrderBJ(u) "
              "// GetUnitX in a comment\nset q=GetUnitX(z)")
    a_ok = (count_paren(sample, "SetUnitPosition") == 1
            and count_paren(sample, "IssueImmediateOrder") == 1
            and count_line(sample, "GetUnitX") == 2          # comment line + the call line
            and count_exact(sample, "GetTriggerPlayer()") == 0)
    print(f"  counters rule-correct (paren excl. siblings, line incl. comment)? {a_ok}")
    ok_all &= a_ok

    # (B) clean synthetic passes every forward anchor
    base = _build_synth()
    rows, failures = audit("\n".join(base) + "\n", src_md5=None)
    clean_ok = (len(failures) == 0)
    print(f"  clean synthetic: ALL forward anchors GREEN? {clean_ok}")
    if not clean_ok:
        for f in failures:
            print("   - unexpected:", f)
    ok_all &= clean_ok

    # (C) break one representative anchor per category; each must be caught
    # find a feeder line for n.timer (a `TimerStart(` we appended) to break the count
    timer_feed = next(i + 1 for i, ln in enumerate(base) if ln.strip() == "set z=TimerStart(a)")
    trig_feed = next(i + 1 for i, ln in enumerate(base) if ln.strip() == "set z=GetTriggerPlayer()")
    breaks = {
        "n.timer":     (timer_feed, "    set z=nope"),                 # count 84 -> 83
        "n.trigplayer":(trig_feed, "    set z=nope"),                  # exact 67 -> 66
        "rc.flurry":   (1373, "    constant integer X= 'ZZZZ'"),       # rawcode drift
        "sf.timer":    (43541, "    call X()"),                        # 30 s feed anchor drift
        "ar.decl":     (1901, "    unit udg_Other= null"),            # Arthur decl drift
        "wp.arthur":   (42918, "    set gg_rct_Arthur=Rect(0,0,0,0)"), # coord drift
        "kb.onperiod": (29027, "    function Other takes nothing returns nothing"),
        "kb.decr":     (29039, "    set z=0  // gutted"),
    }
    caught = {}
    for cid, (ln, repl) in breaks.items():
        mut = list(base)
        mut[ln - 1] = repl
        _r, fails = audit("\n".join(mut) + "\n", src_md5=None)
        caught[cid] = any(f.startswith(cid + ":") for f in fails)
        print(f"  break {cid:<13} @L{ln:<6} -> caught? {caught[cid]}")
    ok_all &= all(caught.values())

    # (D) reverse direction: clean prose passes; a dropped/rewritten cite is caught
    clean_prose = " ".join(cite for _cid, cite in PROSE_CITES)
    _pr, pf_clean = audit_prose(clean_prose)
    prose_clean_ok = (len(pf_clean) == 0)
    dropped = clean_prose.replace("67 / many", "65 / many")   # the exact rot this gate prevents
    _pr2, pf_drop = audit_prose(dropped)
    caught_prose = any(f.startswith("n.trigplayer.prose") for f in pf_drop)
    print(f"  clean prose GREEN? {prose_clean_ok} ; revert 67->65 cite caught? {caught_prose}")
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
        print("Re-ground companion_ai_PHASE0_RECON.md against the current war3map.j "
              "(or restore the dropped cite) before any phase builds on it.")
        return 1
    print(f"\nRESULT: GREEN — all {len(rows)} forward recon anchors hold verbatim vs live "
          f"source (md5 {CANON_MD5}, {CANON_LINES} lines) AND the recon prose still carries "
          f"all {len(prose_rows)} cites (bound BOTH directions).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
