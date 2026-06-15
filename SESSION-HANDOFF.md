# SESSION HANDOFF — KOTR / two-machine setup
_Source machine for this work: DESKTOP (`DESKTOP-IARTP5U`). Paste this into a fresh Claude session on either machine to continue._

## Machines
- **DESKTOP** (this work): host `DESKTOP-IARTP5U`, Win user `ureth`, WSL Ubuntu-22.04 user `mediumunwell`. RTX GPU, ultrawide. Has: WC3 + World Editor, VS Code, Obsidian, Ollama (NO models), git, Windows Git Credential Manager.
- **LAPTOP**: host `DESKTOP-500FSE5`. Holds the source-of-truth content (Obsidian vault, Gir Ollama model, known-good WSL env). Its **Claude app is broken** (won't open after updates; two error-terminals every start; currently needs a reboot to clear).

## Goal
Mirror laptop → desktop (Obsidian vault, WSL CLI env, Gir model, repos) and stand up the KOTR autonomous routines on the desktop.

## DONE on the desktop this session
- Fixed WSL git identity (was placeholder `@example.com` → `mediumunwell` + noreply email).
- Created `~/Kerr-Inner-Horizon.code-workspace` (multi-root: Galaxy Sim + VS Settings).
- Wired GitHub auth via Windows GCM (no `gh`, no sudo) — **first push pending a browser login**.
- Added `cli/wsl/export-wsl-env.sh` + `import-wsl-env.sh` to the Visual_Studio_Settings repo, hardened `.gitignore` against credentials — committed locally, **push pending login**.
- Confirmed already-cloned desktop repos: `bray-density-wave-galaxy` (→ Galaxy_Sim), `Visual_Studio_Settings`.
- Confirmed MISSING on desktop: Obsidian vault (none anywhere), KOTR project, Ollama models (incl. Gir), Node/npm, Claude Code CLI in WSL.

## TODO — LAPTOP (plain WSL terminal; no Claude needed)
1. **Obsidian vault → GitHub**
   cp -r "/mnt/c/Users/<laptop-user>/path/to/Obsidian_Vault" ~/obsidian-vault
   cd ~/obsidian-vault && printf '.obsidian/workspace*\n.obsidian/cache\n.trash/\n' > .gitignore
   git init && git add -A && git commit -m "Initial vault"
   git branch -M main
   git remote add origin https://github.com/mediumunwell/obsidian-vault.git   # create repo at github.com/new (Private) first
   git push -u origin main
2. **WSL env capture**: in laptop's Visual_Studio_Settings → `git pull`, run `cli/wsl/export-wsl-env.sh`, review for secrets, commit, push.
3. **Gir model**: run `ollama show gir --modelfile`. If `FROM <base>` + prompt → tiny, commit Modelfile. If `FROM *.gguf` → `ollama push mediumunwell/gir` (registry) or copy the GGUF.
4. **Fix laptop Claude**: PowerShell `wsl --shutdown` then relaunch; check `~/.claude/settings.json` for a `hooks`→`SessionStart` entry (prime suspect for the two terminals); screenshot the error terminals.

## TODO — DESKTOP (I do these once login done / laptop pushes)
1. Complete the GitHub browser login → push the committed env scripts.
2. Clone `obsidian-vault` → add to workspace → open as vault / copy to Windows → take the REAL KOTR graph screenshot.
3. Clone `Warcraft_III` (KOTR) → fix routine paths: `C:\Users\Morph\...` → `C:\Users\ureth\...` (desktop user is `ureth`, NOT `Morph`).
4. `ollama create gir -f gir.Modelfile` (or pull) → verify in Ollama dropdown.
5. Run `cli/wsl/import-wsl-env.sh` → installs Node/npm + Claude Code in WSL.

## Watch-outs
- Desktop Win user is `ureth` (laptop-written KOTR prompts wrongly assume `Morph`).
- NEVER commit `~/.codex/auth.json` or any Claude/Codex credentials.
- Session titles derive from hostname; rename laptop to `LAPTOP-500FSE5` to stop "desktop-500fse5" sessions.
