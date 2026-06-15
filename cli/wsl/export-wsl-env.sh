#!/usr/bin/env bash
# Capture this WSL machine's CLI environment into the repo. Run on the LAPTOP.
# Captures package LISTS + SCRUBBED config only. NEVER credentials.
set -uo pipefail
OUT="$(cd "$(dirname "$0")" && pwd)"

apt-mark showmanual > "$OUT/apt-manual.txt" 2>/dev/null || true
command -v npm >/dev/null && npm ls -g --depth=0 2>/dev/null | sed '1d' | awk '{print $2}' | sed '/^$/d' > "$OUT/npm-global.txt" || true
command -v pip3 >/dev/null && pip3 freeze > "$OUT/pip-freeze.txt" 2>/dev/null || true

{ echo "# captured (UTC) via export-wsl-env.sh"
  echo "node:    $(node --version 2>/dev/null || echo none)"
  echo "npm:     $(npm --version 2>/dev/null || echo none)"
  echo "python3: $(python3 --version 2>/dev/null || echo none)"
  echo "claude:  $(claude --version 2>/dev/null || echo none)"
  echo "codex:   $(codex --version 2>/dev/null || echo none)"; } > "$OUT/versions.txt"

# Claude Code: plugin/marketplace/skill inventory (no tokens)
claude plugin list > "$OUT/claude/plugins.txt" 2>/dev/null || echo "(claude plugin list unavailable)" > "$OUT/claude/plugins.txt"
ls ~/.claude/skills 2>/dev/null > "$OUT/claude/skills.txt" || true
if [ -f ~/.claude/settings.json ]; then
  sed -E 's/("(apiKey|token|accessToken|refreshToken|clientSecret)"[[:space:]]*:[[:space:]]*)"[^"]*"/\1"REDACTED"/g' \
    ~/.claude/settings.json > "$OUT/claude/settings.json"
fi

# Codex: config only, NEVER auth.json
[ -f ~/.codex/config.toml ] && cp ~/.codex/config.toml "$OUT/codex/config.toml" || true
ls ~/.codex/skills 2>/dev/null > "$OUT/codex/skills.txt" || true

echo "Captured to $OUT"
echo "REVIEW for secrets, then: cd ~/Visual_Studio_Settings && git add -A && git commit -m 'Update WSL CLI env' && git push"
