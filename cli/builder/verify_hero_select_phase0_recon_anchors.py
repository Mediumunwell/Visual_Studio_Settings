#!/usr/bin/env python3
"""
verify_hero_select_phase0_recon_anchors.py
================================================================================
KOTR Hero-Select REDESIGN (Track 4) · PHASE 0 RECON  PROSE <-> LIVE-EXTRACT binder.

WHY THIS GATE EXISTS (a real, uncovered seam — the Track-4 twin of the hero-inv
and companion-AI Phase-0 recon binders)
--------------------------------------------------------------------------------
`hero_select_redesign_PHASE0_RECON_2026-06-17_claude-p.md` is the read-only
grounding deliverable that Evan's "16-slot circular castle + themed rooms"
hero-SELECT redesign plans every later phase against. To stay dependency-correct
it pins ~50 BYTE-EXACT `war3map.j` line cites — the wisp `'ewsp'` start-unit
cluster, the 10 per-hero enter-rect pick triggers and their `*_Appear` spawns,
the `HeroPickAssignTalentTree` stamp (incl. the `'Harf'` special-case), the
re-select-after-control ability `'A00W'`, the `udg_SaveUnitType[0..20]` roster
whitelist (with its reserved `[11..20]` headroom), and the desync-sensitive
save/load spawn point `gg_rct_Arthur_Kay_Lancelot_Appear`.

Those are LIVE-MAP facts but they live in **prose no gate parses**:

  * `verify_castleslot_global_contract.py` binds the P2 generated `.j` <-> the P2
    APPLY-RUNBOOK STEP-0 var table — NOT this recon.
  * `verify_track4_shipset_parity.py` checks the Track-4 ship-set is coherent —
    it never reads the recon prose.
  * pjass / the 178-sweep compile the pastes; none read recon prose.

So the moment the live extract drifts (a WE re-save renumbers JASS — the staleness
class that already bit B4b and that the sibling recon binds repeatedly caught) or
the recon is silently edited, it would keep telling a later phase "the talent
stamp keys on `'Harf'` at L44043" or "roster headroom is L44968-44976" while the
live map disagrees — a SILENT stale-recon brick on the redesign's dependency map.
This binder closes that seam.

TWO CITES WERE OFF-BY-ONE AT FIRST BIND (corrected in the recon, dated 2026-06-18;
both authoring slips, not map drift — the extract md5 is unchanged since authoring):
  * §1.3 talent stamp: the `GetUnitTypeId(GetTriggerUnit()) == 'Harf'` check is at
    **L44042**, not L44043 (L44043 is the `return false` inside ...Func006C).
  * §1.5 roster headroom: indices `[11..20]` set to `0` span **L44968-L44977**
    ([20]=0 is L44977); the prior cite stopped at L44976.
The other ~48 cites verified byte-exact unchanged.

WHAT IT CHECKS (read-only; touches no .w3x and no shippable .j)
--------------------------------------------------------------------------------
  1. The live canonical extract still hashes to the md5 the recon pins, and is
     still 75,535 lines (a re-bake is caught before any per-cite check false-passes).
  2. For each line anchor: every claimed token is present on the cited live line
     BYTE-EXACT (forward).
  3. The recon prose still carries every bound cite string (reverse) — binding
     prose <-> live-extract BOTH ways, incl. both corrected cites.

Exit 0 only if md5+linecount match AND all anchors hold in both directions.

Run:        python3 verify_hero_select_phase0_recon_anchors.py
Self-test:  python3 verify_hero_select_phase0_recon_anchors.py --selftest

EXIT 0 = GREEN, 1 = an anchor drifted, 2 = source/recon not found, 3 = selftest failed.
STANDALONE by design — NOT wired into verify_all.py, so the canonical 178/178 sweep
is unchanged. Sibling of the hero-inv + companion-AI Phase-0 recon binders; same
EXTRACT / md5 / both-ways-binding contract.
"""
import hashlib
import sys
from pathlib import Path

SRC = Path("/mnt/c/Users/Morph/OneDrive/Documents/Warcraft III/Maps/KOTR/_extract_v050/war3map.j")
RECON = Path("/mnt/c/Users/Morph/OneDrive/Documents/Warcraft III/Maps/KOTR/_crew/"
             "hero_select_redesign_PHASE0_RECON_2026-06-17_claude-p.md")

CANON_MD5 = "967131658fd8d4fb27ee0d7f74e4bd22"
CANON_LINES = 75535

# forward: (cid, 1-based live line, token | [tokens all-required]) byte-exact on that line
LINE_ANCHORS = [
    # §1.1 wisp 'ewsp' start-unit cluster (the selection cursor) ~(-5300, 5800) + 2nd @(1205.7,10745.4)
    ("wisp.0",   40918, "BlzCreateUnitWithSkin(p, 'ewsp'"),
    ("wisp.1",   40929, "BlzCreateUnitWithSkin(p, 'ewsp'"),
    ("wisp.2",   40940, "BlzCreateUnitWithSkin(p, 'ewsp'"),
    ("wisp.3",   40951, "BlzCreateUnitWithSkin(p, 'ewsp'"),
    ("wisp.4",   40962, "BlzCreateUnitWithSkin(p, 'ewsp'"),
    ("wisp.5",   40973, "BlzCreateUnitWithSkin(p, 'ewsp'"),
    ("wisp.6",   40984, "BlzCreateUnitWithSkin(p, 'ewsp'"),
    ("wisp.7",   40995, "BlzCreateUnitWithSkin(p, 'ewsp'"),
    ("wisp.2nd", 41062, ["BlzCreateUnitWithSkin(p, 'ewsp'", "1205.7, 10745.4"]),
    # §1.2 enter-rect pick condition gates on the wisp
    ("cond.a",   49153, "GetUnitTypeId(GetTriggerUnit()) == 'ewsp'"),
    ("cond.b",   49324, "GetUnitTypeId(GetTriggerUnit()) == 'ewsp'"),
    # §1.2 the 10 named per-hero pick-trigger action fns
    ("trg.arthur",   49272, "function Trig_King_Arthur_Actions"),
    ("trg.gwen",     49443, "function Trig_Lady_Guinevere_Actions"),
    ("trg.nimue",    49608, "function Trig_Lady_of_the_Lake_Actions"),
    ("trg.merlin",   49772, "function Trig_Merlin_Actions"),
    ("trg.kay",      49944, "function Trig_Sir_Kay_Actions"),
    ("trg.percival", 50107, "function Trig_Sir_Percival_Actions"),
    ("trg.galahad",  50274, "function Trig_Sir_Galahad_Actions"),
    ("trg.lancelot", 50436, "function Trig_Sir_Lancelot_Actions"),
    ("trg.yvain",    50600, "function Trig_Sir_Yvain_Actions"),
    ("trg.gawain",   50763, "function Trig_Sir_Gawain_Actions"),
    # §1.2 Arthur init + enter-rect registration (the InitTrig/register precedent)
    ("init.arthur",  49313, "function InitTrig_King_Arthur"),
    ("init.reg",     49315, "TriggerRegisterEnterRectSimple(gg_trg_King_Arthur, gg_rct_Arthur)"),
    # §1.2 each pick re-enables the talent stamp
    ("en.a",  49276, "EnableTrigger(gg_trg_HeroPickAssignTalentTree)"),
    ("en.b",  49447, "EnableTrigger(gg_trg_HeroPickAssignTalentTree)"),
    ("en.c",  49612, "EnableTrigger(gg_trg_HeroPickAssignTalentTree)"),
    # §1.2 *_Appear spawns (heroType + Appear-rect, byte-exact)
    ("ap.gwen",       49450, ["CreateNUnitsAtLocFacingLocBJ(1, 'Hvwd'", "gg_rct_Guinevere_Appear"]),
    ("ap.gwen.pan",   49465, ["PanCameraToTimedLocForPlayer", "gg_rct_Guinevere_Appear"]),
    ("ap.nimue",      49615, ["CreateNUnitsAtLocFacingLocBJ(1, 'Hjai'", "gg_rct_Nimue_Appear"]),
    ("ap.nimue.pan",  49629, ["PanCameraToTimedLocForPlayer", "gg_rct_Nimue_Appear"]),
    ("ap.merlin",     49779, ["CreateNUnitsAtLocFacingLocBJ(1, 'Hant'", "gg_rct_Merlin_Appear"]),
    ("ap.percival",   50114, ["CreateNUnitsAtLocFacingLocBJ(1, 'Huth'", "gg_rct_Percival_Appear"]),
    ("ap.galahad",    50281, ["CreateNUnitsAtLocFacingLocBJ(1, 'Hpb2'", "gg_rct_Galahad_Appear"]),
    ("ap.galahad.pan",50293, ["PanCameraToTimedLocForPlayer", "gg_rct_Galahad_Appear"]),
    # §1.3 HeroPickAssignTalentTree stamp (the on-spawn talent assignment)
    ("tt.cond",      44034, "function Trig_HeroPickAssignTalentTree_Conditions"),
    ("tt.harf",      44042, "GetUnitTypeId(GetTriggerUnit()) == 'Harf'"),   # CORRECTED L44043->L44042
    ("tt.actions",   44048, "function Trig_HeroPickAssignTalentTree_Actions"),
    ("tt.herovar",   44050, "set udg_Hero=GetTriggerUnit()"),
    ("tt.trigstr",   44051, '"TRIGSTR_3995"'),
    ("tt.stk1",      44054, "STK_AssignTalentTree(1"),
    ("tt.stk2",      44056, "STK_AssignTalentTree(2"),
    ("tt.stk3",      44058, "STK_AssignTalentTree(3"),
    ("tt.disinit",   44066, "DisableTrigger(gg_trg_HeroPickAssignTalentTree)"),
    ("tt.reg",       44067, "TriggerRegisterEnterRectSimple(gg_trg_HeroPickAssignTalentTree, GetPlayableMapRect())"),
    ("tt.redisable", 45266, "DisableTrigger(gg_trg_HeroPickAssignTalentTree)"),
    # §1.4 re-select-after-control ability 'A00W' + its triggers + grant/remove
    ("rs.ability", 3699,  "Dragonflight___ABILITY_ID= 'A00W'"),
    ("rs.arthur",  62739, "function Trig_Select_Arthur_again_Conditions"),
    ("rs.gwen",    63900, "function Trig_Select_Gwen_again_Conditions"),
    ("rs.add1",    38518, "UnitAddAbilityBJ('A00W'"),
    ("rs.rem1",    38523, "UnitRemoveAbility((STKTalentTree_EventUnit), 'A00W')"),
    ("rs.add2",    74489, "UnitAddAbilityBJ('A00W'"),
    ("rs.rem2",    74495, "UnitRemoveAbility((STKTalentTree_EventUnit), 'A00W')"),
    # §1.5 roster whitelist udg_SaveUnitType[0..10] + reserved [11..20]=0 headroom
    ("rost.0",  44957, "set udg_SaveUnitType[0]='Harf'"),
    ("rost.1",  44958, "set udg_SaveUnitType[1]='Hvwd'"),
    ("rost.2",  44959, "set udg_SaveUnitType[2]='Hant'"),
    ("rost.3",  44960, "set udg_SaveUnitType[3]='Hjai'"),
    ("rost.4",  44961, "set udg_SaveUnitType[4]='Hpb2'"),
    ("rost.5",  44962, "set udg_SaveUnitType[5]='Hpb1'"),
    ("rost.6",  44963, "set udg_SaveUnitType[6]='Hart'"),
    ("rost.7",  44964, "set udg_SaveUnitType[7]='Huth'"),
    ("rost.8",  44965, "set udg_SaveUnitType[8]='H007'"),
    ("rost.9",  44966, "set udg_SaveUnitType[9]='H013'"),
    ("rost.10", 44967, "set udg_SaveUnitType[10]='H014'"),
    ("rost.11", 44968, "set udg_SaveUnitType[11]=0"),
    ("rost.15", 44972, "set udg_SaveUnitType[15]=0"),
    ("rost.20", 44977, "set udg_SaveUnitType[20]=0"),                     # CORRECTED range end
    # §1.2/§2 desync-sensitive save/load spawn point (must not regress on redesign)
    ("sl.spawn", 45264, ["CreateUnitAtLoc", "gg_rct_Arthur_Kay_Lancelot_Appear"]),
    ("sl.r1",    46435, ["CreateNUnitsAtLoc", "gg_rct_Arthur_Kay_Lancelot_Appear"]),
    ("sl.r2",    46487, ["CreateNUnitsAtLoc", "gg_rct_Arthur_Kay_Lancelot_Appear"]),
    ("sl.r3",    46538, ["CreateNUnitsAtLoc", "gg_rct_Arthur_Kay_Lancelot_Appear"]),
]

# reverse: recon prose must still carry each cite string (en-dash U+2013 matches the doc)
PROSE_CITES = [
    ("src.lines",      "75,535"),
    ("src.md5",        "967131658fd8d4fb27ee0d7f74e4bd22"),
    ("wisp",           "L40918"),
    ("wisp.2nd",       "L41062"),
    ("cond.a",         "L49153"),
    ("cond.b",         "L49324"),
    ("trg.arthur",     "L49272"),
    ("trg.gawain",     "L50763"),
    ("init",           "L49313/49315"),
    ("en.a",           "L49276"),
    ("ap.gwen",        "L49450"),
    ("ap.merlin",      "L49779"),
    ("ap.galahad",     "L50281"),
    ("tt.range.fn",    "L44034–44070"),
    ("tt.harf",        "L44042"),               # binds the L44043 -> L44042 correction
    ("tt.stk.range",   "L44052–44062"),
    ("tt.reg",         "L44067"),
    ("rs.ability",     "L3699"),
    ("rs.add1",        "L38518"),
    ("rs.rem2",        "L74495"),
    ("rost.range",     "L44957–44967"),
    ("rost.1115",      "L44968–44972"),
    ("rost.headroom",  "L44968–44977"),    # binds the L44968-44976 -> L44968-44977 correction
    ("sl.spawn",       "L45264"),
    ("sl.r3",          "L46538"),
    ("pp.castle",      "gg_rct_Castle_Slot"),   # the redesign's proposed new rect family
]


# The dated line-correction note (+ machine-checked footer) this binder appends to
# the recon redundantly mentions the corrected cites (e.g. "L44042", "L44968-L44977").
# If the reverse search read the whole file it could go vacuous against a BODY edit —
# it would still "find" the cite in our own note. So the reverse direction strips the
# note before searching prose, exactly like the companion-AI runbook binder.
NOTE_MARKER = "**Line-correction note (2026-06-18"


def recon_body(recon_text):
    """The grounding body, excluding this binder's own appended audit note/footer."""
    return recon_text.split(NOTE_MARKER, 1)[0]


def _tokens(sub):
    return sub if isinstance(sub, list) else [sub]


def audit(text, src_md5=None):
    """Return (rows, failures) for the forward (live-line) direction."""
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

    for cid, ln, sub in LINE_ANCHORS:
        observed = L(ln).strip()
        ok = all(tok in observed for tok in _tokens(sub))
        check(cid, f"L{ln} carries {sub!r}", observed[:80], ok)

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
    print(f"{'ANCHOR':<16}{'OK?':<6}OBSERVED")
    for cid, _claim, observed, ok in rows:
        print(f"{cid:<16}{'OK' if ok else 'XXXX':<6}{observed}")


def _build_synth():
    """Synthetic source that PASSES every forward anchor (md5 skipped)."""
    base = ["x"] * CANON_LINES

    def put(ln, s):
        base[ln - 1] = s

    for cid, ln, sub in LINE_ANCHORS:
        put(ln, " ".join(_tokens(sub)))     # all required tokens present on the line
    return base


def selftest():
    print("=== SELFTEST: clean synthetic + per-category RED-catch + reverse ===")
    ok_all = True

    # (A) multi-token helper is all-required
    a_ok = (all(t in "a 'Hvwd' b gg_rct_Guinevere_Appear c"
                for t in _tokens(["'Hvwd'", "gg_rct_Guinevere_Appear"]))
            and not all(t in "a 'Hvwd' b c"
                        for t in _tokens(["'Hvwd'", "gg_rct_Guinevere_Appear"])))
    print(f"  multi-token all-required helper correct? {a_ok}")
    ok_all &= a_ok

    # (B) clean synthetic passes every forward anchor
    base = _build_synth()
    rows, failures = audit("\n".join(base) + "\n", src_md5=None)
    clean_ok = (len(failures) == 0)
    print(f"  clean synthetic: ALL {len(LINE_ANCHORS)} forward anchors GREEN? {clean_ok}")
    if not clean_ok:
        for f in failures:
            print("   - unexpected:", f)
    ok_all &= clean_ok

    # (C) break one representative anchor per category; each must be caught
    breaks = {
        "wisp.0":   (40918, "    set u=CreateUnit(p, 'hfoo')"),       # wisp cluster drift
        "cond.a":   (49153, "    if ( something_else ) then"),         # pick condition drift
        "trg.arthur": (49272, "function Trig_Other_Actions takes nothing returns nothing"),
        "ap.merlin":(49779, "    call CreateNUnitsAtLocFacingLocBJ(1, 'Hxxx', p, loc, loc)"),
        "tt.harf":  (44042, "        return false"),                   # the L44042 'Harf' cite (the fix)
        "tt.stk1":  (44054, "    call SomethingElse(1)"),             # talent assign drift
        "rs.ability":(3699, "    constant integer Dragonflight___ABILITY_ID= 'ZZZZ'"),
        "rost.20":  (44977, "    set udg_SaveUnitType[20]=99"),       # roster headroom-end drift
        "sl.spawn": (45264, "    set udg_x=CreateUnitAtLoc(h, t, GetRectCenter(gg_rct_Other), 270.0)"),
    }
    caught = {}
    for cid, (ln, repl) in breaks.items():
        mut = list(base)
        mut[ln - 1] = repl
        _r, fails = audit("\n".join(mut) + "\n", src_md5=None)
        caught[cid] = any(f.startswith(cid + ":") for f in fails)
        print(f"  break {cid:<12} @L{ln:<6} -> caught? {caught[cid]}")
    ok_all &= all(caught.values())

    # (D) reverse direction: clean prose passes; each corrected cite, if reverted, is caught
    clean_prose = " ".join(cite for _cid, cite in PROSE_CITES)
    _pr, pf_clean = audit_prose(clean_prose)
    prose_clean_ok = (len(pf_clean) == 0)

    rev_harf = clean_prose.replace("L44042", "L44043")          # revert the 'Harf' correction
    _pr2, pf_harf = audit_prose(rev_harf)
    caught_harf = any(f.startswith("tt.harf.prose") for f in pf_harf)

    rev_head = clean_prose.replace("L44968–44977", "L44968–44976")  # revert headroom
    _pr3, pf_head = audit_prose(rev_head)
    caught_head = any(f.startswith("rost.headroom.prose") for f in pf_head)

    print(f"  clean prose GREEN? {prose_clean_ok} ; "
          f"revert 'Harf' L44042->L44043 caught? {caught_harf} ; "
          f"revert headroom ->L44976 caught? {caught_head}")
    ok_all &= prose_clean_ok and caught_harf and caught_head

    # (E) note-exclusion: a BODY edit must be caught even though the appended note
    # still carries the cite (the false-pass trap the companion runbook binder hit).
    fake = ("body cites L44042 and L44968–44977 here.\n\n"
            + NOTE_MARKER + ", claude-p).** corrected to L44042 / L44968–44977.\n")
    body_reverted = recon_body(fake.replace("body cites L44042", "body cites L44043"))
    _pe, pf_excl = audit_prose(body_reverted)
    caught_excl = any(f.startswith("tt.harf.prose") for f in pf_excl)
    # and the clean fake body still passes those two cites
    _pe2, pf_cleanbody = audit_prose(recon_body(fake))
    cleanbody_ok = not any(f.startswith(("tt.harf.prose", "rost.headroom.prose"))
                           for f in pf_cleanbody)
    print(f"  note-exclusion: clean body GREEN? {cleanbody_ok} ; "
          f"body L44042->L44043 caught despite note still carrying it? {caught_excl}")
    ok_all &= caught_excl and cleanbody_ok

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
    prose_rows, prose_failures = audit_prose(recon_body(recon_text))
    print(f"\n{'PROSE CITE':<16}{'OK?':<6}CITE")
    for cid, cite, ok in prose_rows:
        print(f"{cid:<16}{'OK' if ok else 'XXXX':<6}{cite!r}")

    failures = failures + prose_failures
    print(f"\nsource: {SRC}\nrecon:  {RECON}")
    if failures:
        print(f"\nRESULT: FAIL — {len(failures)} recon anchor(s) drifted "
              "(live-source and/or recon-prose direction):")
        for f in failures:
            print("  -", f)
        print("Re-ground hero_select_redesign_PHASE0_RECON against the current war3map.j "
              "(or restore the dropped cite) before any phase builds on it.")
        return 1
    print(f"\nRESULT: GREEN — all {len(LINE_ANCHORS)} forward recon anchors hold verbatim vs "
          f"live source (md5 {CANON_MD5}, {CANON_LINES} lines) AND the recon prose still carries "
          f"all {len(prose_rows)} cites (bound BOTH directions).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
