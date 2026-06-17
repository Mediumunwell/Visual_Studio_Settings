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
# Inference runs over the Windows-side Ollama REST API (127.0.0.1:11434); $EXE is only a
# convenience handle for CLI fallbacks. MODEL must be a model that actually exists on this
# host — `ollama list` shows gir/qwen, NOT a `kotr-ai` model (that name 404s -> empty pulse).
EXE='/mnt/c/Users/Morph/AppData/Local/Programs/Ollama/ollama.exe'; [ -f "$EXE" ] || EXE='/mnt/e/Ollama/ollama.exe'
MODEL='gir:latest'
# Resilience: a fresh pulse used to noise-post "(returned no analysis)" the instant $MODEL came
# back empty — almost always transient VRAM/load contention (e.g. the WE-GUI loop has Warcraft
# loaded), NOT a real outage. We now try each MODEL in turn (gir:fast is the lighter fallback that
# fits when VRAM is tight) with a retry each, and only if EVERY attempt fails do we post an
# actionable DIAGNOSTIC instead of a vague apology. Keep the heaviest/best model first.
MODELS=( "$MODEL" 'gir:fast' )
POST="$DIR/../discord/post_via_webhook.py"
# Canonical Systems_Migration lives in the WSL home (mirror at /mnt/c/Users/Morph/Projects).
SCAN=( "/home/mediumunwell/Systems_Migration" "$DIR" )

# --- 1. gather BLOCKED routine items (queues, scoreboards, staged-for-human files) ----------
blocked="$(
  for d in "${SCAN[@]}"; do
    [ -d "$d" ] || continue
    grep -rinE --color=never "blocked|STAGED_FOR|\[ \].*block" \
      --include="QUEUE.md" --include="SCOREBOARD.md" --include="STAGED_FOR_*.md" \
      --include="*.md" "$d" 2>/dev/null
  done | sed -E 's#/home/mediumunwell/##' | grep -ivE "BLOCKED_ROUTINES_LOG" | sort -u | head -40
)"
[ -z "$blocked" ] && blocked="(no items currently tagged blocked — report that the queues are clear.)"
# strip to clean ASCII (tab/newline + printable) so color/control bytes can't corrupt the JSON body
blocked="$(printf '%s' "$blocked" | tr -cd '\11\12\15\40-\176')"

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
# Try each model (one retry each) until one returns a non-empty answer (after <think>-strip).
analysis=""; used_model=""; last_err=""
for m in "${MODELS[@]}"; do
  for attempt in 1 2; do
    powershell.exe -NoProfile -Command "
      \$p = [string](Get-Content -Raw -LiteralPath '$WPF');
      \$b = @{ model='$m'; prompt=\$p; stream=\$false } | ConvertTo-Json -Compress;
      try { (Invoke-RestMethod -Uri 'http://127.0.0.1:11434/api/generate' -Method Post -Body \$b -ContentType 'application/json' -TimeoutSec 600).response }
      catch { 'INFER_ERROR: ' + \$_.Exception.Message }
    " 2>/dev/null | tr -d '\r' > "$RF"
    if grep -q '^INFER_ERROR:' "$RF"; then
      last_err="$m attempt$attempt: $(grep -m1 '^INFER_ERROR:' "$RF" | cut -c1-200)"; continue
    fi
    # strip deepseek <think> traces
    cand="$(sed -E ':a;N;$!ba; s#<think>.*</think>##g' "$RF" | sed -E 's/^[[:space:]]*//' )"
    if [ -n "${cand//[[:space:]]/}" ]; then analysis="$cand"; used_model="$m"; break 2; fi
    last_err="$m attempt$attempt: empty response (post-<think>-strip)"
  done
done
# Every attempt failed -> post an ACTIONABLE diagnostic (models tried, last error, live model
# list), not a vague apology. The next scheduled pulse self-recovers once VRAM frees up.
if [ -z "${analysis//[[:space:]]/}" ]; then
  avail="$(curl -s --max-time 15 http://127.0.0.1:11434/api/tags 2>/dev/null | tr -cd '\11\12\15\40-\176' | python3 -c "import sys,json
try:
    d=json.load(sys.stdin); print(', '.join(m['name'] for m in d.get('models',[])) or '(none listed)')
except Exception as e:
    print('tags-unreachable: %s' % e)" 2>/dev/null)"
  analysis="DIAGNOSTIC — no model produced analysis this pulse (tried: ${MODELS[*]}).
Last error: ${last_err:-none captured}.
Ollama @127.0.0.1:11434 models available: ${avail:-unreachable}.
Likely transient VRAM/load contention (e.g. WE-GUI loop has Warcraft loaded); next pulse self-recovers. If persistent, check the Ollama server / model names."
  used_model="(none — diagnostic)"
fi

# --- 3. log + post --------------------------------------------------------------------------
ts="$(date -u +%FT%TZ)"
nblock="$(printf '%s\n' "$blocked" | grep -c . || true)"
{ echo; echo "## $ts — kotr-ai pulse ($nblock scanned lines, model=$used_model)"; echo '```'; echo "$analysis"; echo '```'; } >> "$LOG"

summary="🧠 **kotr-ai pulse** $ts · model $used_model
I. Scanned $nblock blocked/staged lines across KOTR repos
II. Proposed unblock + prevention steps (detail ↓)
III. Logged to cli/builder/BLOCKED_ROUTINES_LOG.md"
python3 "$POST" --username "KOTR (kotr-ai brain)" --message "$summary" --detail "$analysis" >/dev/null 2>&1 \
  && echo "posted pulse to #kotr-ai-builders ($ts)" || echo "post failed ($ts)"
