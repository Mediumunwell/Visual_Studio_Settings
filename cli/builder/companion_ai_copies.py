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

EXIT CODES
  0  exactly one distinct content across all discovered copies (no divergence)
  2  >1 distinct content (copies have diverged) OR any copy is TRUNCATED
     (missing EOF newline)
  3  no copy of the file found (nothing to reconcile)

POSTURE: strictly read-only — md5/stat/grep only; never writes or edits any copy.
  Excludes *.bak* snapshots and AppData agent-session caches by design.
"""
import hashlib
import os
import re
import subprocess
import sys
import time

TARGET = "kotr_companion_ai_v0.52.j"

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


def discover():
    """Return absolute paths of every live TARGET copy under SEARCH_ROOTS."""
    seen = set()
    found = []
    for root in SEARCH_ROOTS:
        if not os.path.isdir(root):
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            # prune obviously-excluded subtrees for speed
            dirnames[:] = [d for d in dirnames if d not in (".git", "node_modules")]
            if TARGET in filenames:
                p = os.path.realpath(os.path.join(dirpath, TARGET))
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
        "path": path, "md5": md5, "lines": nlines, "bytes": nbytes,
        "footer": footer, "banner": has_banner, "ns": ns, "rev": rev,
        "tracked": tracked, "head": head, "mtime": mtime,
    }


def short(path):
    home = os.path.expanduser("~")
    return path.replace(home, "~")


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
    fp = fingerprint(write(TARGET,
        "//==\nfunction CAI_Brain takes nothing returns nothing\nendfunction\n//====\n"))
    checks.append(("banner+nl => OK/bnrY",
                   fp["footer"] == "OK" and fp["banner"] and fp["ns"] == "CAI_*"))

    # 2. clean comment ending, EOF newline, NO banner -> OK, banner N (no false TRUNC)
    fp = fingerprint(write(TARGET,
        "function CAI_Brain takes nothing returns nothing\nendfunction\n// usage note\n"))
    checks.append(("noBanner+nl => OK/bnrN",
                   fp["footer"] == "OK" and not fp["banner"]))

    # 3. missing EOF newline -> TRUNCATED
    fp = fingerprint(write(TARGET, "function CAI_X\nendfunction\n//== cut here"))
    checks.append(("noEOFnl => TRUNCATED", fp["footer"] == "TRUNCATED"))

    # 4. KotrAI_* namespace detection
    fp = fingerprint(write(TARGET, "function KotrAI_Tick takes nothing returns nothing\nendfunction\n"))
    checks.append(("KotrAI ns", fp["ns"] == "KotrAI_*"))

    # 5. rev marker extraction (max)
    fp = fingerprint(write(TARGET, "// rev4 then rev25 later\nfunction CAI_A\nendfunction\n"))
    checks.append(("rev max=25", fp["rev"] == 25))

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
        print(f"SKIP — no '{TARGET}' copy found under the search roots.")
        return 3

    fps = [fingerprint(p) for p in copies]
    fps.sort(key=lambda f: f["mtime"], reverse=True)

    md5s = {f["md5"] for f in fps}
    truncated = [f for f in fps if f["footer"] == "TRUNCATED"]

    print(f"=== companion-AI hub copy reconciliation — {len(fps)} live copy(ies), "
          f"{len(md5s)} distinct content(s) ===")
    for i, f in enumerate(fps):
        age_h = (time.time() - f["mtime"]) / 3600.0
        git = f"git:{f['head']}" if f["tracked"] and f["head"] else (
            "git:untracked" if f["head"] else "no-git")
        revs = f"rev{f['rev']}" if f["rev"] is not None else "rev?"
        fresh = "  <-- FRESHEST (by mtime)" if i == 0 else ""
        bnr = "Y" if f["banner"] else "N"
        print(f"  [{f['md5'][:8]}] {f['lines']:>5}L {f['bytes']:>7}B  "
              f"{f['footer']:<9} bnr={bnr} ns={f['ns']:<9} {revs:<6} {git:<14} "
              f"{age_h:5.1f}h  {short(f['path'])}{fresh}")

    print("-" * 78)
    if len(md5s) > 1:
        print(f"RED — {len(md5s)} distinct contents: the copies have DIVERGED. "
              f"Freshest by mtime is {fps[0]['md5'][:8]} "
              f"({short(fps[0]['path'])}).")
        print("  → reconcile before any paste: confirm which copy is canonical "
              "for the target use (desktop CAI_* hub vs crew KotrAI_* staged set "
              "are PARALLEL implementations, not stale copies of each other).")
    if truncated:
        print(f"RED — {len(truncated)} copy(ies) TRUNCATED (no closing banner / "
              f"no EOF newline): " + ", ".join(short(f["path"]) for f in truncated))
    if len(md5s) == 1 and not truncated:
        print("GREEN — every copy is byte-identical and footer-intact. "
              "No divergence to reconcile.")
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
