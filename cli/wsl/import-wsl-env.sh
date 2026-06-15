#!/usr/bin/env bash
# Restore the WSL CLI environment from the captured lists. Run on the DESKTOP after pulling.
set -uo pipefail
IN="$(cd "$(dirname "$0")" && pwd)"

if ! command -v node >/dev/null; then
  echo ">> installing Node (nvm, no sudo)"
  curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
  export NVM_DIR="$HOME/.nvm"; . "$NVM_DIR/nvm.sh"; nvm install --lts
fi
export NVM_DIR="$HOME/.nvm"; [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"

if [ -f "$IN/npm-global.txt" ]; then
  while read -r p; do [ -n "$p" ] && [ "$p" != "npm" ] && npm install -g "$p"; done < "$IN/npm-global.txt"
fi
command -v claude >/dev/null || npm install -g @anthropic-ai/claude-code

[ -f "$IN/pip-freeze.txt" ] && pip3 install -r "$IN/pip-freeze.txt" || true

# apt list is NOT auto-installed (many are system pkgs). Review then run manually:
[ -f "$IN/apt-manual.txt" ] && echo ">> review $IN/apt-manual.txt, then: sudo xargs -a apt-manual.txt apt-get install -y"

mkdir -p ~/.claude ~/.codex
[ -f "$IN/claude/settings.json" ] && cp "$IN/claude/settings.json" ~/.claude/settings.json
[ -f "$IN/codex/config.toml" ]   && cp "$IN/codex/config.toml" ~/.codex/config.toml

echo "Done. Re-auth separately (NOT synced): run 'claude' to log in, 'codex login' for Codex."
