# HANDOFF → Claude Desktop — build the STAGED executors

**Created:** 2026-06-16 · **For:** the Claude **Desktop app** (computer-use) on `DESKTOP-IARTP5U`.
**Why desktop:** the WE-GUI driver + desktop routines need computer-use, which the desktop app has.
Evan will resume the WSL/CLI session and we finish these together — this doc lets you make progress meanwhile.

> The control-center **structure** is built (`~/backend_panel.py`, shortcut "KOTR Backend Control").
> Each switch is tagged **[LIVE]** or **[STAGED]**. Your job: turn the **[STAGED]** switches into real
> executors, one at a time, each verified, then flip its tag to [LIVE] in `backend_panel.py`.

## ⛔ Blocked on Evan (don't burn cycles fighting these — note + proceed where you can)
1. `wsl --shutdown` (from Windows) → enables WSL↔Ollama on `localhost:11434` (mirrored net). Until then,
   call the model from the **Windows side** (pattern below).
2. OBS/YouTube + **locatekko** Drive creds dropped in Drive → unblocks ⑤ Streaming.
3. Laptop `git -C ~/Visual_Studio_Settings pull`; `sudo loginctl enable-linger mediumunwell`.

## ✅ Already working (build ON these, don't rebuild)
- **kotr-ai** = `qwen2.5:14b`, pinned on the RTX 3080 Ti (`ollama ps` shows it). Models on `E:\Ollama`.
- **Inference from a script** (until the WSL bridge is up): POST to the Windows-side API —
  `powershell.exe Invoke-RestMethod -Uri http://127.0.0.1:11434/api/generate -Method Post -ContentType 'application/json' -Body <json>`
  with the prompt **`[string]`-cast** (Get-Content attaches note-props → 400 otherwise). Working
  reference: `cli/builder/kotr_ai_pulse.sh`.
- **Discord I/O**: post two-part (family-tree summary + `||spoiler code block||`) via
  `cli/discord/post_via_webhook.py --message … --detail …`; read with `cli/discord/read_channel.py`.
  Token = restored GIR bot token in `~/.clawhip/config.toml`. Format spec: `cli/discord/KOTR_BACKEND.md`.
- **Operator template to mirror**: `~/Gir/tools/discord_operator_listener.py` (+ `cli/discord/kotr_gir_gateway.py`).
- **Control config**: `~/.kotr_control.json` (active `campaign_goal`, toggles). Panel `run_now()` already
  routes campaign/dream/review/health — wire real work there.
- **Services** (`systemctl --user`): `gir-listener`, `kotr-listener`, `kotr-ai-pulse` (45-min pulse =
  scan blocked routines → propose fixes → post; the working autonomous pattern).
- **Review deck**: `python3 cli/builder/kotr_review.py` → `Desktop/KOTR_Review.html`.

## Build order (cheapest/highest-signal first)
### 1. kotr-ai command **operator** (`review`, `health`, `campaign`, `dream`)
A listener on `#kotr-ai-builders` (use the GIR token; mirror `discord_operator_listener.py`) that runs
allowlisted commands from Evan's user id, gated like Gir's. Wire each to the panel Run Now buttons.
- `health` — gather git/ollama/service/disk/VRAM state → kotr-ai summary → post.
- `review` — `git diff`/recent changes → kotr-ai code review → post (use the two-part format).
- `campaign` — read `campaign_goal` from `~/.kotr_control.json`; **plan + propose** steps toward that
  goal first (no destructive action until executors 2–3 exist).
- `dream` — free analysis pass like Gir's.
Run it as a `kotr-ai-operator.service` and add it to `backend_panel.py` SERVICES. Flip Run Now tags → [LIVE].

### 2. **WE-GUI driver** (Arthur / playtest) — computer-use
Per the **updated** WE policy (`BUILDER_PROMPT.md` hard rules): you MAY make changes in the World
Editor and **save** — but ONLY by driving the WE GUI + WE's own Save. **Never** edit `.w3x` binaries.
**Back up the map first; v0.49 is untouchable; verify every change by visually reading frames** (screenshot).
Wire to panel ②b. This is what makes "Arthur moves in a playtest" real.

### 3. Desktop routines / Cowork (②a/②b) → real scheduled tasks + desktop-app routines.
### 4. Codex lane (④) → give Codex its autonomous space.
### 5. Streaming (⑤) — OBS scene → YouTube (Mediumunwell) + livestream analysis. **Needs creds (blocker #2).**

## Rules (keep — these are Evan's boundaries)
- **Command-gated** automation (Discord-triggered), NOT a wild self-approving loop.
- Verify with **evidence** (Discord post + screenshot). Don't claim done without proof.
- Outward publishing (streaming, Drive uploads) only with creds present — don't set unattended.
- After each executor works, **edit `backend_panel.py`** to flip its tag/label [STAGED]→[LIVE].

## Context
Full session state: `Obsidian-KOTR/Systems/SESSION_2026-06-16_backend-control.md`.
Report progress to `#kotr-ai-builders` (two-part format) so Evan sees it in the morning + the review deck picks it up.
