#!/usr/bin/env python3
"""
verify_hero_select_p2_generated_j.py
================================================================================
KOTR hero-select P2 · GENERATED PASTE ARTIFACT <-> DATATABLE-JSON binder.

WHY THIS GATE EXISTS (a real, uncovered seam — the only Track-4 source-of-truth
that is a *machine-generated paste blob*, not prose)
--------------------------------------------------------------------------------
`hero_select_p2_InitCastleSlotData.generated.j` is the literal `function
InitCastleSlotData` body an operator pastes into the World Editor to drive P2 of
the hero-select redesign: ten parallel `udg_CastleSlot_*` arrays plus five flat
sub-tables (item / ally / rescue / invuln / avail) that the generic enter-handler
walks by `[Start .. Start+Count)` per slot index. Its sibling
`hero_select_p2_datatable.generated.json` is the structured source of truth both
files were emitted from by `verify_hero_select_p2_datatable.py`.

But that generator script is **not present in this WSL tree** (it ran once and
left only its two artifacts), so NOTHING re-checks them each sweep:

  * `fix_specs/verify_all.py` (178/178) compiles the PASTE SET — it never reads
    these `.generated.*` files and is unchanged by them.
  * `verify_hero_select_p2_runbook_anchors.py` binds the P2 *APPLY-RUNBOOK* prose
    cites to the live `.j`; it does not touch the generated InitCastleSlotData blob
    or its datatable.
  * `verify_castleslot_global_contract.py` proves every written `udg_CastleSlot_*`
    global is declared; it says nothing about the VALUES this blob packs.

So if the `.j` is hand-edited despite its "DO NOT hand-edit" banner, or the JSON
drifts from it, or a flat-table span stops matching its per-slot list length, the
operator would paste a blob whose `[Start..Start+Count)` windows silently index
the wrong units/items — a corrupt-but-compiling P2 with no gate to catch it. This
binder closes that seam: the paste blob is pinned, byte-for-value, to its datatable
in BOTH directions, and the datatable's pinned md5 is checked against reality.

WHAT IT BINDS (read-only; touches no .w3x and no shippable .j)
--------------------------------------------------------------------------------
  0. md5 reality: the JSON's pinned md5/line-count == the `.j` header's pinned
     md5/line-count == the LIVE `_extract_v050/war3map.j` actually hashed now.
     A re-bake is caught before any value below can false-pass.
  1. Per-slot scalars (forward JSON->.j, equality is inherently both-way): HeroType,
     NameStr (=TRIGSTR_<PlayerNameStr>), AnnounceStr (=TRIGSTR_<AnnounceStr>),
     TakenVillager, SpawnAbility (null->0 else '<raw>'), EnableTrig (None->null),
     CamLoc (=GetRectCenter(<CamRect>) — the per-slot camera-pan target; see note),
     and the slot-header Name, the owner/claim/pedestal comment, the
     spawnApi/extrasHook comment.

  NOTE (CamLoc — added 2026-06-18 claude-p): the datatable generator originally DROPPED the
  per-slot camera pan entirely, so the `_crew` paste blob and its JSON both lacked CamLoc while
  the authoritative pjass-compiled loop-gen output (`fix_specs/hero_select_p2_loop_data.gen.j`)
  carried all 10. This binder checked blob<->JSON only, so the gap was invisible (GREEN on a
  CamLoc-less pair). Pasting that blob would spawn heroes with no camera pan. The generator now
  emits CamLoc and the JSON carries CamRect; this gate binds them so the drop can never recur.
  2. Spans: each table's Start/Count in the `.j` == the JSON `<tbl>_span[i]`, AND
     Count == len(per-slot list) (HeroItems/AllyUnits/RescueUnits/...).
  3. Flat sub-tables: each `.j` `udg_CastleSlot_<Tbl>[k]` == JSON `<tbl>_flat[k]`,
     element-for-element, with EQUAL lengths (reverse: a stray/dropped `.j` entry
     beyond the JSON flat list is a RED).
  4. Internal span integrity (guards the JSON itself even if the `.j` agrees):
     span[0] starts at 0, each span starts where the previous ended, and the last
     span's end == len(flat). A corrupt cumulative offset is caught here.
  5. Cardinality (reverse): the `.j` defines exactly len(JSON["slots"]) slot blocks
     and no `udg_CastleSlot_*[i]` scalar for an out-of-range slot index.

Exit 0 only if md5 matches AND every binding holds in both directions.

Run:        python3 verify_hero_select_p2_generated_j.py
Self-test:  python3 verify_hero_select_p2_generated_j.py --selftest

STANDALONE by design (sibling of the other Track-4 binders): prints RESULT and
exits 1 on any drift, NOT wired into fix_specs/verify_all.py, so the 178/178 static
sweep is unchanged. It IS registered in verify_builder_gates.py (the cli/builder
aggregate sweep), whose discovery cross-check would otherwise flag it as
unregistered rot.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

EXTRACT = Path.home() / "Warcraft III" / "KOTR" / "_extract_v050" / "war3map.j"
CREW = Path.home() / "Warcraft III" / "KOTR" / "_crew"
GEN_J = CREW / "hero_select_p2_InitCastleSlotData.generated.j"
DATATABLE = CREW / "hero_select_p2_datatable.generated.json"

# the md5 the JSON pins the canonical extract to (cross-checked against reality)
CLAIMED_MD5 = "967131658fd8d4fb27ee0d7f74e4bd22"

# flat sub-tables: (.j array field, JSON flat key, JSON span key, JSON per-slot
# list key, whether the .j element is a quoted fourcc vs a bare global ref)
TABLES = [
    ("Item",   "item_flat",   "item_span",   "HeroItems",   True),
    ("Ally",   "ally_flat",   "ally_span",   "AllyUnits",   False),
    ("Rescue", "rescue_flat", "rescue_span", "RescueUnits", False),
    ("Invuln", "invuln_flat", "invuln_span", "InvulnUnits", False),
    ("Avail",  "avail_flat",  "avail_span",  "AvailUnits",  True),
]
FLAT_FIELDS = {t[0] for t in TABLES}

_SET = re.compile(r"^\s*set udg_CastleSlot_(\w+)\[(\d+)\]=(.+?)\s*$")
_SLOTHDR = re.compile(r"^\s*// --- slot (\d+): (.+?) ---\s*$")
_OWNER = re.compile(r"^\s*// owner=(\S+) claim=(\S+) pedestal=(\[.*\])\s*$")
_SPAWN = re.compile(r"^\s*// spawnApi=(\S+) extrasHook=(\S+)\s*$")
_HEADER = re.compile(r"md5 ([0-9a-f]{32}) \((\d+) lines\)")


def parse_generated_j(text):
    """Parse the generated blob into a structured dict (no validation here)."""
    out = {"header": None, "scalars": {}, "slot_names": {},
           "owner": {}, "spawn": {}, "flat": {t[0]: {} for t in TABLES}}
    cur_slot = None
    for line in text.splitlines():
        m = _HEADER.search(line)
        if m and out["header"] is None:
            out["header"] = (m.group(1), int(m.group(2)))
            continue
        m = _SLOTHDR.match(line)
        if m:
            cur_slot = int(m.group(1))
            out["slot_names"][cur_slot] = m.group(2)
            continue
        m = _OWNER.match(line)
        if m and cur_slot is not None:
            out["owner"][cur_slot] = (m.group(1), m.group(2), m.group(3))
            continue
        m = _SPAWN.match(line)
        if m and cur_slot is not None:
            out["spawn"][cur_slot] = (m.group(1), m.group(2))
            continue
        m = _SET.match(line)
        if m:
            field, idx, val = m.group(1), int(m.group(2)), m.group(3)
            if field in FLAT_FIELDS:
                out["flat"][field][idx] = val
            else:
                out["scalars"].setdefault(idx, {})[field] = val
    return out


def _flat_elem(raw, quoted):
    """Normalize a `.j` flat RHS to the bare string the JSON stores."""
    raw = raw.strip()
    if quoted:
        return raw[1:-1] if len(raw) >= 2 and raw[0] == raw[-1] == "'" else raw
    return raw


def audit(j, data, live_md5, live_lines):
    """Return list of (category, label, ok, detail) checks."""
    checks = []

    def add(cat, label, ok, detail=""):
        checks.append((cat, label, ok, detail))

    slots = data["slots"]
    n = len(slots)

    # --- 0. md5 / line reality ----------------------------------------------
    jh = j["header"]
    add("md5", "json md5 == claimed", data["md5"] == CLAIMED_MD5,
        f'json={data["md5"]} claimed={CLAIMED_MD5}')
    add("md5", ".j header md5 == json md5", bool(jh) and jh[0] == data["md5"],
        f'.j={jh[0] if jh else None} json={data["md5"]}')
    add("md5", "live extract md5 == json md5", live_md5 == data["md5"],
        f"live={live_md5} json={data['md5']}")
    add("md5", "json lines == .j header lines",
        bool(jh) and jh[1] == data["lines"],
        f'.j={jh[1] if jh else None} json={data["lines"]}')
    add("md5", "live extract lines == json lines", live_lines == data["lines"],
        f"live={live_lines} json={data['lines']}")

    # --- 5. cardinality (reverse) -------------------------------------------
    add("card", "slot-block count == json slots",
        len(j["slot_names"]) == n, f'.j={len(j["slot_names"])} json={n}')
    stray = sorted(i for i in j["scalars"] if i < 0 or i >= n)
    add("card", "no out-of-range slot scalars", not stray, f"stray slot idx {stray}")

    # --- 4. internal span integrity (guards JSON itself) --------------------
    for _field, flatkey, spankey, _listkey, _q in TABLES:
        span = data[spankey]
        flat = data[flatkey]
        running = 0
        ok = True
        bad = ""
        for i, (start, count) in enumerate(span):
            if start != running:
                ok, bad = False, f"slot {i} start={start} expected {running}"
                break
            running += count
        if ok and running != len(flat):
            ok, bad = False, f"last span end={running} != flat len {len(flat)}"
        add("span-int", f"{flatkey} cumulative", ok, bad)

    # --- 1. per-slot scalars + comments -------------------------------------
    def want(idx, field, expected):
        got = j["scalars"].get(idx, {}).get(field)
        add("scalar", f"slot{idx}.{field}", got == expected,
            f"got={got!r} want={expected!r}")

    for i, s in enumerate(slots):
        want(i, "HeroType", f"'{s['HeroTypeId']}'")
        want(i, "NameStr", f'"TRIGSTR_{s["PlayerNameStr"]}"')
        want(i, "AnnounceStr", f'"TRIGSTR_{s["AnnounceStr"]}"')
        want(i, "TakenVillager", f"'{s['TakenVillagerType']}'")
        sa = s["SpawnAbility"]
        want(i, "SpawnAbility", "0" if sa is None else f"'{sa}'")
        et = s["EnableTrig"]
        want(i, "EnableTrig", "null" if et is None else et)
        # CamLoc: the per-slot camera-pan target = GetRectCenter(<appear rect>). Binds the blob's
        # CamLoc RHS to the JSON's CamRect both ways; a missing/dropped CamLoc (the original defect)
        # reads got=None != want -> RED.
        want(i, "CamLoc", f"GetRectCenter({s['CamRect']})")
        # slot-header name
        add("scalar", f"slot{i}.Name", j["slot_names"].get(i) == s["Name"],
            f'got={j["slot_names"].get(i)!r} want={s["Name"]!r}')
        # owner / claim / pedestal comment
        ow = j["owner"].get(i)
        exp_ow = (s["OwnerGlobal"], s["ClaimFlag"], repr(s["PedestalUnitsRemoved"]))
        add("scalar", f"slot{i}.owner", ow == exp_ow, f"got={ow!r} want={exp_ow!r}")
        # spawnApi / extrasHook comment
        sp = j["spawn"].get(i)
        exp_sp = (s["SpawnApi"], "YES" if s["HasExtrasHook"] else "no")
        add("scalar", f"slot{i}.spawn", sp == exp_sp, f"got={sp!r} want={exp_sp!r}")

    # --- 2. spans in .j == json span + count == per-slot list len -----------
    for field, _flatkey, spankey, listkey, _q in TABLES:
        span = data[spankey]
        for i, s in enumerate(slots):
            start, count = span[i]
            gs = j["scalars"].get(i, {}).get(f"{field}Start")
            gc = j["scalars"].get(i, {}).get(f"{field}Count")
            add("span", f"slot{i}.{field}Start", gs == str(start),
                f"got={gs} want={start}")
            add("span", f"slot{i}.{field}Count", gc == str(count),
                f"got={gc} want={count}")
            add("span", f"slot{i}.{field}Count==len({listkey})",
                count == len(s[listkey]), f"count={count} list={len(s[listkey])}")

    # --- 3. flat sub-tables element-for-element, equal length ----------------
    for field, flatkey, _spankey, _listkey, quoted in TABLES:
        flat = data[flatkey]
        jflat = j["flat"][field]
        add("flat", f"{field} length", len(jflat) == len(flat),
            f".j={len(jflat)} json={len(flat)}")
        mism = []
        for k, expected in enumerate(flat):
            got = _flat_elem(jflat[k], quoted) if k in jflat else None
            if got != expected:
                mism.append(f"[{k}] got={got!r} want={expected!r}")
        add("flat", f"{field} elements", not mism,
            "; ".join(mism[:4]) + (" ..." if len(mism) > 4 else ""))

    return checks


def report(checks):
    cats = ["md5", "card", "span-int", "scalar", "span", "flat"]
    for cat in cats:
        rows = [c for c in checks if c[0] == cat]
        if not rows:
            continue
        npass = sum(1 for _, _, ok, _ in rows if ok)
        print(f"[{cat:<8}] {npass}/{len(rows)} ok")
        for _cat, label, ok, detail in rows:
            if not ok:
                print(f"    DRIFT {label}: {detail}")


def _run(j_text, data, live_md5, live_lines):
    return audit(parse_generated_j(j_text), data, live_md5, live_lines)


def selftest():
    print("=== SELFTEST: .j<->JSON binding has teeth (scalar / flat-elem / "
          "flat-len / span-int / md5 / live-md5) ===")
    # Minimal but structurally complete 2-slot fixture that passes everything.
    data = {
        "md5": CLAIMED_MD5, "lines": 75535,
        "slots": [
            {"HeroTypeId": "Harf", "PlayerNameStr": "839", "AnnounceStr": "2987",
             "TakenVillagerType": "n00S", "SpawnAbility": None,
             "EnableTrig": "gg_trg_Flurry_AI", "Name": "Arthur",
             "OwnerGlobal": "udg_A", "ClaimFlag": "udg_oneA",
             "PedestalUnitsRemoved": ["gg_unit_Harf_0001"],
             "SpawnApi": "CreateNUnitsAtLoc", "HasExtrasHook": False,
             "CamRect": "gg_rct_Arthur_Kay_Lancelot_Appear",
             "HeroItems": ["I005", "ankh"], "AllyUnits": ["gg_unit_x"],
             "RescueUnits": [], "InvulnUnits": [], "AvailUnits": []},
            {"HeroTypeId": "Hvwd", "PlayerNameStr": "840", "AnnounceStr": "2988",
             "TakenVillagerType": "n00Q", "SpawnAbility": "LInf",
             "EnableTrig": None, "Name": "Guin",
             "OwnerGlobal": "udg_G", "ClaimFlag": "udg_oneG",
             "PedestalUnitsRemoved": ["gg_unit_Hvwd_0000"],
             "SpawnApi": "CreateNUnitsAtLocFacingLocBJ", "HasExtrasHook": True,
             "CamRect": "gg_rct_Guinevere_Appear",
             "HeroItems": ["bzbe"], "AllyUnits": ["gg_unit_y", "gg_unit_z"],
             "RescueUnits": ["gg_unit_r"], "InvulnUnits": [], "AvailUnits": ["Hgam"]},
        ],
        "item_flat": ["I005", "ankh", "bzbe"], "item_span": [[0, 2], [2, 1]],
        "ally_flat": ["gg_unit_x", "gg_unit_y", "gg_unit_z"],
        "ally_span": [[0, 1], [1, 2]],
        "rescue_flat": ["gg_unit_r"], "rescue_span": [[0, 0], [0, 1]],
        "invuln_flat": [], "invuln_span": [[0, 0], [0, 0]],
        "avail_flat": ["Hgam"], "avail_span": [[0, 0], [0, 1]],
    }

    def emit(d):
        L = [f"// AUTO-GENERATED. Source: war3map.j md5 {d['md5']} ({d['lines']} lines).",
             "function InitCastleSlotData takes nothing returns nothing"]
        for i, s in enumerate(d["slots"]):
            L.append(f"    // --- slot {i}: {s['Name']} ---")
            L.append(f"    set udg_CastleSlot_HeroType[{i}]='{s['HeroTypeId']}'")
            L.append(f'    set udg_CastleSlot_NameStr[{i}]="TRIGSTR_{s["PlayerNameStr"]}"')
            L.append(f'    set udg_CastleSlot_AnnounceStr[{i}]="TRIGSTR_{s["AnnounceStr"]}"')
            L.append(f"    set udg_CastleSlot_TakenVillager[{i}]='{s['TakenVillagerType']}'")
            for field, _fk, spankey, _lk, _q in TABLES:
                st, ct = d[spankey][i]
                L.append(f"    set udg_CastleSlot_{field}Start[{i}]={st}")
                L.append(f"    set udg_CastleSlot_{field}Count[{i}]={ct}")
            sa = s["SpawnAbility"]
            L.append(f"    set udg_CastleSlot_SpawnAbility[{i}]=" + ("0" if sa is None else f"'{sa}'"))
            et = s["EnableTrig"]
            L.append(f"    set udg_CastleSlot_EnableTrig[{i}]=" + ("null" if et is None else et))
            L.append(f"    set udg_CastleSlot_CamLoc[{i}]=GetRectCenter({s['CamRect']})")
            L.append(f"    // owner={s['OwnerGlobal']} claim={s['ClaimFlag']} "
                     f"pedestal={s['PedestalUnitsRemoved']!r}")
            L.append(f"    // spawnApi={s['SpawnApi']} extrasHook="
                     + ("YES" if s["HasExtrasHook"] else "no"))
        for field, flatkey, _sk, _lk, quoted in TABLES:
            for k, v in enumerate(d[flatkey]):
                rhs = f"'{v}'" if quoted else v
                L.append(f"    set udg_CastleSlot_{field}[{k}]={rhs}")
        L.append("endfunction")
        return "\n".join(L)

    good = emit(data)
    base = _run(good, data, CLAIMED_MD5, 75535)
    assert all(ok for _, _, ok, _ in base), \
        "baseline should pass: " + str([(l, d) for c, l, ok, d in base if not ok])

    def caught(j_text=None, d=None, live_md5=CLAIMED_MD5, live_lines=75535, cat=None):
        rows = _run(j_text if j_text is not None else good,
                    d if d is not None else data, live_md5, live_lines)
        return any((cat is None or c == cat) and not ok for c, l, ok, dt in rows)

    # 1) hand-edit a scalar in the .j
    c_scalar = caught(j_text=good.replace("HeroType[0]='Harf'", "HeroType[0]='ZZZZ'"),
                      cat="scalar")
    # 2) corrupt a flat element in the .j
    c_elem = caught(j_text=good.replace("Item[0]='I005'", "Item[0]='XXXX'"), cat="flat")
    # 3) drop a flat element (length mismatch) — remove last item line
    dropped = "\n".join(l for l in good.splitlines()
                        if "Item[2]=" not in l)
    c_len = caught(j_text=dropped, cat="flat")
    # 4) corrupt the JSON span cumulative (start no longer continues)
    import copy
    bad = copy.deepcopy(data)
    bad["item_span"][1][0] = 99
    c_spanint = caught(d=bad, cat="span-int")
    # 5) .j header md5 disagrees with JSON
    c_md5 = caught(j_text=good.replace(CLAIMED_MD5, "0" * 32), cat="md5")
    # 6) live extract md5 drifted from JSON
    c_live = caught(live_md5="f" * 32, cat="md5")
    # 7) the ORIGINAL DEFECT: drop a slot's CamLoc line from the .j entirely (the camera pan the
    #    datatable generator used to omit). Must read got=None != want -> RED in the scalar cat.
    no_cam = "\n".join(l for l in good.splitlines()
                       if "udg_CastleSlot_CamLoc[0]=" not in l)
    c_camdrop = caught(j_text=no_cam, cat="scalar")
    # 8) point a CamLoc at the WRONG appear rect (silent miss-pan) -> RED.
    c_camwrong = caught(
        j_text=good.replace("CamLoc[1]=GetRectCenter(gg_rct_Guinevere_Appear)",
                            "CamLoc[1]=GetRectCenter(gg_rct_Nimue_Appear)"),
        cat="scalar")

    print(f"  scalar hand-edit caught   : {c_scalar}")
    print(f"  flat-element drift caught  : {c_elem}")
    print(f"  flat-length drift caught   : {c_len}")
    print(f"  span-integrity drift caught: {c_spanint}")
    print(f"  .j/json md5 split caught    : {c_md5}")
    print(f"  live-extract md5 drift caught: {c_live}")
    print(f"  CamLoc drop caught          : {c_camdrop}")
    print(f"  CamLoc wrong-rect caught    : {c_camwrong}")
    ok = all([c_scalar, c_elem, c_len, c_spanint, c_md5, c_live, c_camdrop, c_camwrong])
    print(f"\nSELFTEST {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 3


def main():
    if "--selftest" in sys.argv:
        return selftest()
    for p, what in ((EXTRACT, "live extract"), (GEN_J, "generated .j"),
                    (DATATABLE, "datatable json")):
        if not p.exists():
            print(f"FATAL: {what} not found: {p}")
            return 2

    raw = EXTRACT.read_bytes()
    live_md5 = hashlib.md5(raw).hexdigest()
    live_lines = raw.decode("latin-1").count("\n") + (0 if raw.endswith(b"\n") else 1)
    data = json.loads(DATATABLE.read_text())
    j = parse_generated_j(GEN_J.read_text())

    print(f"live extract : {EXTRACT}")
    print(f"  md5={live_md5}  lines={live_lines}  (json pins {data['md5']}/{data['lines']})")
    print(f"generated .j : {GEN_J.name}  ({len(j['slot_names'])} slot blocks)")
    print(f"datatable    : {DATATABLE.name}  ({len(data['slots'])} slots)\n")

    checks = audit(j, data, live_md5, live_lines)
    report(checks)

    fail = [(c, l, d) for c, l, ok, d in checks if not ok]
    npass = len(checks) - len(fail)
    print(f"\nchecks={len(checks)}  pass={npass}  fail={len(fail)}")
    if fail:
        print("RESULT: FAIL — hero-select P2 generated paste artifact has drifted "
              "from its datatable / the live extract:")
        for c, l, d in fail:
            print(f"  - [{c}] {l}: {d}")
        return 1
    print(f"RESULT: GREEN — all {len(checks)} checks hold: the generated "
          "InitCastleSlotData paste blob is byte-for-value identical to its "
          "datatable JSON in BOTH directions (10 slots: scalars, name/owner/"
          "spawn comments, all five Start/Count spans == json span == per-slot "
          "list length, and the item/ally/rescue/invuln/avail flat sub-tables "
          "element-for-element with equal lengths), the JSON spans are internally "
          "cumulative-consistent, and the md5/line-count the JSON pins matches both "
          "the .j header AND the live _extract_v050/war3map.j hashed right now. "
          "The P2 paste artifact is bound both ways.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
