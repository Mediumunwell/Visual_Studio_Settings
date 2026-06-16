#!/usr/bin/env bash
# kotr_ai_pulse.sh — the KOTR brain's safe, scheduled pulse.
# Scans the routine queues/scoreboards/staged files for items marked BLOCKED, asks the local
# kotr-ai model how to unblock them (or how to change the routine so it stops getting blocked),
# logs the analysis, and posts a two-part summary to #kotr-ai-builders.
#
# READ-ONLY by design: it analyzes + proposes + logs + posts. It does NOT edit routines or the
# game — that's the command-triggered/supervised layer. Run once (`bash kotr_ai_pulse.sh`) or on
# a timer via the kotr-ai-pulse systemd service.
set -uo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
LOG="$DIR/BLOCKED_ROUTINES_LOG.md"
EXE='/mnt/c/Users/ureth/AppData/Local/Programs/Ollama/ollama.exe'; [ -f "$EXE" ] || EXE='/mnt/e/Ollama/ollama.exe'
POST="$DIR/../discord/post_via_webhook.py"
SCAN=( "/mnt/e/Claude Projects/Systems_Migration" "$DIR" )

# --- 1. gather BLOCKED routine items (queues, scoreboards, staged-for-human files) ----------
blocked="$(
  for d in "${SCAN[@]}"; do
    [ -d "$d" ] || continue
    grep -rinE "blocked|STAGED_FOR|\[ \].*block" \
      --include="QUEUE.md" --include="SCOREBOARD.md" --include="STAGED_FOR_*.md" \
      --include="*.md" "$d" 2>/dev/null
  done | sed -E 's#/mnt/e/Claude Projects/##' | grep -ivE "BLOCKED_ROUTINES_LOG" | sort -u | head -40
)"
[ -z "$blocked" ] && blocked="(no items currently tagged blocked — report that the queues are clear.)"

# --- 2. ask kotr-ai how to unblock / prevent ------------------------------------------------
PF="$(mktemp)"; trap 'rm -f "$PF" "$RF" 2>/dev/null' EXIT
cat > "$PF" <<EOF
You are kotr-ai, the local KOTR brain. Below are routine items currently flagged BLOCKED across
the KOTR repos. For EACH distinct blocker: (1) the concrete step(s) to unblock it now, and
(2) how to change the routine/prompt so it stops getting blocked for that reason in future.
Be concise and specific. Then give a one-line headline verdict. Items:

$blocked
EOF
RF="$(mktemp)"
WPF="$(wslpath -w "$PF")"
powershell.exe -NoProfile -Command "
  \$p = Get-Content -Raw -LiteralPath '$WPF';
  \$b = @{ model='kotr-ai'; prompt=\$p; stream=\$false } | ConvertTo-Json -Compress;
  try { (Invoke-RestMethod -Uri 'http://127.0.0.1:11434/api/generate' -Method Post -Body \$b -ContentType 'application/json' -TimeoutSec 600).response }
  catch { 'INFER_ERROR: ' + \$_.Exception.Message }
" 2>/dev/null | tr -d '\r' > "$RF"
# strip deepseek <think> traces
analysis="$(sed -E ':a;N;$!ba; s#<think>.*</think>##g' "$RF" | sed -E 's/^[[:space:]]*//' )"
[ -z "${analysis//[[:space:]]/}" ] && analysis="(kotr-ai returned no analysis — check the server / VRAM.)"

# --- 3. log + post --------------------------------------------------------------------------
ts="$(date -u +%FT%TZ)"
nblock="$(printf '%s\n' "$blocked" | grep -c . || true)"
{ echo; echo "## $ts — kotr-ai pulse ($nblock scanned lines)"; echo '```'; echo "$analysis"; echo '```'; } >> "$LOG"

summary="🧠 **kotr-ai pulse** $ts
I. Scanned $nblock blocked/staged lines across KOTR repos
II. Proposed unblock + prevention steps (detail ↓)
III. Logged to cli/builder/BLOCKED_ROUTINES_LOG.md"
python3 "$POST" --username "KOTR (kotr-ai brain)" --message "$summary" --detail "$analysis" >/dev/null 2>&1 \
  && echo "posted pulse to #kotr-ai-builders ($ts)" || echo "post failed ($ts)"
