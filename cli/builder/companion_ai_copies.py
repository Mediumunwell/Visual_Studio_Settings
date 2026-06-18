#!/usr/bin/env python3
"""companion_ai_copies.py — which `kotr_companion_ai_v0.52.j` is canonical, and
which copies have silently diverged?  Answer it in one read-only command.

BACKGROUND (the cross-copy confusion trap)
  The companion-AI hub `kotr_companion_ai_v0.52.j` lives on MANY mounts at once
  (the WSL git repo, Systems_Migration, the OneDrive desktop mount, the obsidian
  vault, AppData agent-session outputs).  Different engine families evolve
  DIFFERENT copies — the desktop routine rev-bumps the OneDrive copy (rev35 →
  rev36 …), the crew keeps a paste-ready draft in Systems_Migration, the WSL
  builder commits its own copy in git.  The result, seen repeatedly in
  #kotr-ai-builders, is engines posting CONTRADICTING md5s / line-counts / rev
  numbers for "the hub" and correcting each other (e.g. Cowork's 01:43Z "complete
  rev35" → 02:43Z "actually rev36, footer truncated again").  There are also TWO
  parallel implementations under the same filename: the desktop hub is `CAI_*`-
  namespaced, the crew staged set is `KotrAI_*`-namespaced.

  This reporter ends the guesswork: it discovers every live copy on the box,
  fingerprints each (md5 / lines / bytes / footer-integrity / namespace flavor /
  git-tracked + HEAD / max `revN` marker / mtime), groups by content, and names
  the freshest.  Sibling of pulse_ghost_detector.py — turn a manual cross-mount
  audit into a repeatable check so the next engine never re-derives it by hand.

FOOTER INTEGRITY (the recurring truncation the channel keeps re-flagging)
  The unambiguous corruption signal is a MISSING EOF newline — a file cut
  mid-write ends without one ("ends mid OPEN-ITEM, no EOF newline", per Cowork).
  That alone is reported TRUNCATED.  The closing-banner line (`//====…`) is a
  CONVENTION the evolved hubs follow but older paste-ready drafts legitimately do
  not, so banner-presence is reported as a SEPARATE informational column (bnr=Y/N)
  and never on its own counted as corruption — avoiding a false TRUNCATED verdict
  on a clean draft that simply ends with a usage-note comment.

VERSION FAMILY (the other half of the confusion)
  The hub is version-suffixed and evolves: `kotr_companion_ai_v0.52.j` →
  `_v0.53.j` → `_v0.54.j` (plus the bare `kotr_companion_ai.j`).  An engine citing
  "v0.52 is the hub" while the canonical work has already advanced to v0.54 — both
  present in the SAME triggers dir — is the exact same "which is canonical" trap,
  one version axis over.  So this reporter discovers the whole `kotr_companion_ai*.j`
  family, tags each copy with its version, and judges divergence PER VERSION: two
  copies of the *same* version that differ is a real silent drift (RED); two
  *different* versions that differ is expected progression (not divergence).  It
  also names the latest version present so the next engine cites the current hub,
  not a stale suffix.

EXIT CODES
  0  every version group is internally byte-identical and footer-intact
     (cross-version differences are expected progression, NOT divergence)
  2  some version group has >1 distinct content (a copy silently diverged) OR
     any copy is TRUNCATED (missing EOF newline)
  3  no copy of the file family found (nothing to reconcile)

POSTURE: strictly read-only — md5/stat/grep only; never writes or edits any copy.
  Excludes *.bak* snapshots and AppData agent-session caches by design.
"""
import hashlib
import os
import re
import subprocess
import sys
import time

TARGET_LABEL = "kotr_companion_ai*.j"
# The whole version family: bare name OR a _vMAJOR.MINOR suffix.
TARGET_RE = re.compile(r"^kotr_companion_ai(?:_v\d+\.\d+)?\.j$")

# Roots to scan for live copies. Kept explicit so the report is deterministic and
# fast; add a root here if a new mount appears.
SEARCH_ROOTS = [
    os.path.expanduser("~/Warcraft III"),
    os.path.expanduser("~/Systems_Migration"),
    os.path.expanduser("~/obsidian-vault"),
    "/mnt/c/Users/Morph/Projects",
    "/mnt/c/Users/Morph/OneDrive/Documents/Warcraft III",
]

# Path fragments that mark a non-canonical / throwaway copy — excluded by design.
EXCLUDE_FRAGMENTS = (
    ".bak",                       # pre-rev snapshots
    "/local-agent-mode-sessions/",  # AppData agent-session scratch outputs
    "/.git/",
    "/node_modules/",
)

REV_RE = re.compile(r"\brev(\d+)\b")
FUNC_CAI_RE = re.compile(r"^\s*function\s+CAI_", re.MULTILINE)
FUNC_KOTRAI_RE = re.compile(r"^\s*function\s+KotrAI_", re.MULTILINE)
VER_RE = re.compile(r"_v(\d+)\.(\d+)\.j$")

# The companion-AI SHIPS through the crew pipeline, NOT these standalone drafts. The
# `kotr_companion_ai_v0.5x.j` family is the CAI_*-namespaced hand-paste DRAFT lineage
# (ungated, not in any runbook); the shippable artifact is the KotrAI_*-namespaced crew
# set — the operator runbook below, backed by the sweep-gated COMBINED. So "latest draft
# suffix" (e.g. v0.54) is NOT "the thing that ships": surfacing this stops the next engine
# pasting a standalone draft when the pipeline artifact is the actual deliverable. (Verified
# 2026-06-18 claude-p: STAGED_COMBINED carries 16 KotrAI_* fns, 0 CAI_*; v0.5x.j drafts carry
# CAI_* only — two distinct lineages, the exact "which is canonical" trap one axis over.)
DRAFT_NS = "CAI_*"
PIPELINE_NS = "KotrAI_*"
PIPELINE_RUNBOOK = "~/Warcraft III/KOTR/_crew/companion_ai_APPLY_RUNBOOK.md"
PIPELINE_ARTIFACT = "Systems_Migration/kotr/fix_specs/companion_ai_STAGED_COMBINED.j"
PIPELINE_GATE = "verify_companion_ai_fidelity.py"


def ver_of(path):
    """Version tag parsed from the filename: 'v0.54', or 'base' for the bare name."""
    m = VER_RE.search(os.path.basename(path))
    return f"v{int(m.group(1))}.{m.group(2)}" if m else "base"


def ver_key(ver):
    """Sortable key for a version tag; 'base' sorts below all numbered versions."""
    if ver == "base":
        return (-1, -1)
    m = re.match(r"v(\d+)\.(\d+)$", ver)
    return (int(m.group(1)), int(m.group(2))) if m else (0, 0)


def discover():
    """Return absolute paths of every live copy of the TARGET family under roots."""
    seen = set()
    found = []
    for root in SEARCH_ROOTS:
        if not os.path.isdir(root):
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            # prune obviously-excluded subtrees for speed
            dirnames[:] = [d for d in dirnames if d not in (".git", "node_modules")]
            for fn in filenames:
                if not TARGET_RE.match(fn):
                    continue
                p = os.path.realpath(os.path.join(dirpath, fn))
                if any(frag in p for frag in EXCLUDE_FRAGMENTS):
                    continue
                if p in seen:
                    continue
                seen.add(p)
                found.append(p)
    return sorted(found)


def git_info(path):
    """(tracked: bool, head: str|None) if path is inside a git work-tree."""
    d = os.path.dirname(path)
    try:
        tracked = subprocess.run(
            ["git", "-C", d, "ls-files", "--error-unmatch", os.path.basename(path)],
            capture_output=True, text=True, timeout=15,
        ).returncode == 0
    except Exception:  # noqa: BLE001
        return (False, None)
    head = None
    try:
        r = subprocess.run(["git", "-C", d, "rev-parse", "--short", "HEAD"],
                           capture_output=True, text=True, timeout=15)
        if r.returncode == 0:
            head = r.stdout.strip()
    except Exception:  # noqa: BLE001
        pass
    return (tracked, head)


def fingerprint(path):
    with open(path, "rb") as fh:
        raw = fh.read()
    md5 = hashlib.md5(raw).hexdigest()
    text = raw.decode("utf-8", errors="replace")
    lines = text.splitlines()
    nlines = len(lines)
    nbytes = len(raw)

    eof_newline = raw.endswith(b"\n")
    last_content = next((ln for ln in reversed(lines) if ln.strip()), "")
    has_banner = last_content.lstrip().startswith("//==")
    # Corruption = a file cut mid-write (no EOF newline). Banner is convention-only.
    footer = "OK" if eof_newline else "TRUNCATED"

    cai = len(FUNC_CAI_RE.findall(text))
    kotrai = len(FUNC_KOTRAI_RE.findall(text))
    if cai and not kotrai:
        ns = "CAI_*"
    elif kotrai and not cai:
        ns = "KotrAI_*"
    elif cai and kotrai:
        ns = "MIXED"
    else:
        ns = "?"

    revs = [int(x) for x in REV_RE.findall(text)]
    rev = max(revs) if revs else None

    tracked, head = git_info(path)
    mtime = os.path.getmtime(path)

    return {
        "path": path, "ver": ver_of(path), "md5": md5, "lines": nlines,
        "bytes": nbytes, "footer": footer, "banner": has_banner, "ns": ns,
        "rev": rev, "tracked": tracked, "head": head, "mtime": mtime,
    }


def short(path):
    home = os.path.expanduser("~")
    return path.replace(home, "~")


def classify(fps):
    """Version-aware verdict over a list of fingerprint dicts.

    Returns (exit_code, lines) where lines are human-readable verdict strings.
    Divergence is judged PER VERSION: >1 distinct content within a single version
    tag is a real silent drift (RED); differences ACROSS versions are expected
    progression and are not divergence. Any TRUNCATED copy is RED.
    """
    lines = []
    if not fps:
        return 3, [f"SKIP — no '{TARGET_LABEL}' copy found under the search roots."]

    # group by version tag
    groups = {}
    for f in fps:
        groups.setdefault(f["ver"], []).append(f)

    drifted = {v: g for v, g in groups.items()
               if len({f["md5"] for f in g}) > 1}
    truncated = [f for f in fps if f["footer"] == "TRUNCATED"]

    latest = max(groups, key=ver_key)
    latest_fp = max(groups[latest], key=lambda f: f["mtime"])
    latest_ns = latest_fp["ns"]
    scope = ("latest DRAFT in this family" if latest_ns == DRAFT_NS
             else "the current copy to cite")
    lines.append(
        f"LATEST version present: {latest} "
        f"([{latest_fp['md5'][:8]}] {latest_fp['lines']}L {latest_ns}, "
        f"{short(latest_fp['path'])}) — {scope}, not a stale suffix.")
    # A CAI_* latest is a STANDALONE DRAFT, not the shippable artifact — say so plainly so
    # "cite v0.54" is never misread as "v0.54 ships". (Lineage-axis trap: see module header.)
    if latest_ns == DRAFT_NS:
        lines.append(
            f"NOTE — the {DRAFT_NS} `kotr_companion_ai_v*.j` family is the standalone "
            f"hand-paste DRAFT lineage, NOT the deliverable. The companion AI that SHIPS is "
            f"the {PIPELINE_NS} crew pipeline: runbook {PIPELINE_RUNBOOK}, backed by the "
            f"sweep-gated {PIPELINE_ARTIFACT} ({PIPELINE_GATE}). So '{latest}' = latest draft "
            f"suffix, not the shippable artifact — don't paste a v*.j draft over the pipeline.")

    code = 0
    if drifted:
        code = 2
        for v, g in sorted(drifted.items(), key=lambda kv: ver_key(kv[0])):
            distinct = {f["md5"][:8] for f in g}
            lines.append(
                f"RED — version {v} has {len(distinct)} distinct contents across "
                f"{len(g)} copies (SILENT DRIFT, same version should be identical): "
                + ", ".join(short(f["path"]) for f in g))
    if truncated:
        code = 2
        lines.append("RED — TRUNCATED (no EOF newline): "
                     + ", ".join(short(f["path"]) for f in truncated))
    if code == 0:
        nver = len(groups)
        if nver > 1:
            lines.append(
                f"GREEN — {nver} versions present, each internally byte-identical "
                "and footer-intact. Cross-version differences are expected "
                "progression, not divergence.")
        else:
            lines.append("GREEN — every copy is byte-identical and footer-intact. "
                         "No divergence to reconcile.")
    return code, lines


def selftest():
    """Exercise fingerprint() truncation/banner detection on synthetic fixtures."""
    import tempfile
    checks = []

    def write(name, data):
        d = tempfile.mkdtemp()
        p = os.path.join(d, name)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(data)
        return p

    # 1. banner + EOF newline -> OK, banner Y
    fp = fingerprint(write("kotr_companion_ai_v0.52.j",
        "//==\nfunction CAI_Brain takes nothing returns nothing\nendfunction\n//====\n"))
    checks.append(("banner+nl => OK/bnrY",
                   fp["footer"] == "OK" and fp["banner"] and fp["ns"] == "CAI_*"))

    # 2. clean comment ending, EOF newline, NO banner -> OK, banner N (no false TRUNC)
    fp = fingerprint(write("kotr_companion_ai_v0.52.j",
        "function CAI_Brain takes nothing returns nothing\nendfunction\n// usage note\n"))
    checks.append(("noBanner+nl => OK/bnrN",
                   fp["footer"] == "OK" and not fp["banner"]))

    # 3. missing EOF newline -> TRUNCATED
    fp = fingerprint(write("kotr_companion_ai_v0.52.j", "function CAI_X\nendfunction\n//== cut here"))
    checks.append(("noEOFnl => TRUNCATED", fp["footer"] == "TRUNCATED"))

    # 4. KotrAI_* namespace detection
    fp = fingerprint(write("kotr_companion_ai_v0.52.j", "function KotrAI_Tick takes nothing returns nothing\nendfunction\n"))
    checks.append(("KotrAI ns", fp["ns"] == "KotrAI_*"))

    # 5. rev marker extraction (max)
    fp = fingerprint(write("kotr_companion_ai_v0.52.j",
        "// rev4 then rev25 later\nfunction CAI_A\nendfunction\n"))
    checks.append(("rev max=25", fp["rev"] == 25))

    # 6. version tag parsed from filename (family member vs bare base)
    checks.append(("ver_of v0.54",
                   ver_of("/x/kotr_companion_ai_v0.54.j") == "v0.54"))
    checks.append(("ver_of base",
                   ver_of("/x/kotr_companion_ai.j") == "base"))
    checks.append(("ver_key orders v0.54>v0.52>base",
                   ver_key("v0.54") > ver_key("v0.52") > ver_key("base")))

    def fp_of(ver, md5, footer="OK"):
        return {"ver": ver, "md5": md5, "footer": footer, "mtime": 0.0,
                "lines": 1, "ns": "CAI_*", "path": f"/x/{ver}/{md5}.j"}

    # 7. cross-version differences are EXPECTED progression -> GREEN (exit 0)
    code, _ = classify([fp_of("v0.52", "aaa"), fp_of("v0.54", "bbb")])
    checks.append(("cross-version diff => GREEN", code == 0))

    # 8. SAME-version distinct contents = real silent drift -> RED (exit 2)
    code, _ = classify([fp_of("v0.52", "aaa"), fp_of("v0.52", "ccc")])
    checks.append(("same-version drift => RED", code == 2))

    # 9. a truncated copy -> RED (exit 2) even if versions otherwise agree
    code, _ = classify([fp_of("v0.54", "ddd", footer="TRUNCATED")])
    checks.append(("truncated => RED", code == 2))

    # 10. empty set -> nothing to reconcile (exit 3)
    code, _ = classify([])
    checks.append(("no copies => EXIT3", code == 3))

    # 11. a CAI_* latest emits the standalone-draft-vs-pipeline lineage NOTE (the trap this
    #     fix closes); a KotrAI_* latest does NOT (it's already pipeline-namespaced).
    _, ls_cai = classify([fp_of("v0.54", "eee")])  # fp_of defaults ns="CAI_*"
    checks.append(("CAI_* latest => pipeline NOTE",
                   any(PIPELINE_NS in ln and PIPELINE_RUNBOOK in ln for ln in ls_cai)))
    _, ls_kot = classify([{"ver": "v0.54", "md5": "fff", "footer": "OK", "mtime": 0.0,
                           "lines": 1, "ns": PIPELINE_NS, "path": "/x/v0.54/fff.j"}])
    checks.append(("KotrAI_* latest => no draft NOTE",
                   not any("standalone" in ln for ln in ls_kot)))

    ok = sum(1 for _, c in checks if c)
    for name, c in checks:
        print(f"  [{'PASS' if c else 'FAIL'}] {name}")
    print(f"selftest: {ok}/{len(checks)} " + ("PASS" if ok == len(checks) else "FAIL"))
    return 0 if ok == len(checks) else 1


def main():
    if "--selftest" in sys.argv[1:]:
        return selftest()
    copies = discover()
    if not copies:
        print(f"SKIP — no '{TARGET_LABEL}' copy found under the search roots.")
        return 3

    fps = [fingerprint(p) for p in copies]
    # sort by version (newest first), then mtime within a version (newest first)
    fps.sort(key=lambda f: (ver_key(f["ver"]), f["mtime"]), reverse=True)

    md5s = {f["md5"] for f in fps}
    vers = sorted({f["ver"] for f in fps}, key=ver_key, reverse=True)

    print(f"=== companion-AI hub copy reconciliation — {len(fps)} live copy(ies), "
          f"{len(vers)} version(s), {len(md5s)} distinct content(s) ===")
    for f in fps:
        age_h = (time.time() - f["mtime"]) / 3600.0
        git = f"git:{f['head']}" if f["tracked"] and f["head"] else (
            "git:untracked" if f["head"] else "no-git")
        revs = f"rev{f['rev']}" if f["rev"] is not None else "rev?"
        bnr = "Y" if f["banner"] else "N"
        print(f"  {f['ver']:<6} [{f['md5'][:8]}] {f['lines']:>5}L {f['bytes']:>7}B  "
              f"{f['footer']:<9} bnr={bnr} ns={f['ns']:<9} {revs:<6} {git:<14} "
              f"{age_h:5.1f}h  {short(f['path'])}")

    print("-" * 78)
    code, lines = classify(fps)
    for ln in lines:
        print(ln)
    if code == 2:
        print("  → reconcile before any paste: same-version copies must match; "
              "desktop CAI_* hub vs crew KotrAI_* staged set are PARALLEL "
              "implementations (not stale copies of each other).")
    return code


if __name__ == "__main__":
    sys.exit(main())
