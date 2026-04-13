# Known Issues — to diagnose if they recur

## gh CLI auth keeps dropping (suspected, 2026-04-12)

**Symptom:** When a tool (Claude, MCP, script) tries to call `gh`, it errors with "not logged in." Re-running `gh auth login --web` with 8-digit device code + 2FA phone code works, but feels like it has to happen repeatedly.

**Possible causes to investigate if it happens again:**

1. **Confusion between auth systems (most likely).** `gh` CLI auth, VS Code GitHub extension, git credential helper, Windows Credential Manager, and GHD all have independent token stores. A prompt from any one of them can *feel* like "gh logged me out" without actually being that.
2. **WSL vs Windows `gh` are separate installs** with separate `~/.config/gh/hosts.yml` files. Logging into one does not log into the other.
3. **Token revoked upstream.** Check github.com → Settings → Developer settings → Personal access tokens. If no "GitHub CLI" token is listed, it was revoked (password change with "sign out everywhere" does this).
4. **Config file permissions or wipe.** After the Plan folder reorg on 2026-04-12 we wondered if some file moves caused `~/.config/gh/` to lose its contents, but no evidence yet. If it recurs, check timestamps on `~/.config/gh/hosts.yml`.

**Diagnostic commands for next occurrence:**

```bash
gh auth status
cat ~/.config/gh/hosts.yml 2>/dev/null || echo "MISSING"
stat ~/.config/gh/hosts.yml 2>/dev/null
ls -la ~/.git-credentials
git config --global credential.helper
```

**Not the cause:**
- 2FA does not invalidate `gh` session tokens. It only gates initial auth.
- "Use my sign-in info to automatically finish setting up my device" (Win Settings → Accounts → Sign-in options) is already ON and did not resolve it.

**Also noted on 2026-04-12:**
- WSL was missing `wslu` (`wslview`), so `gh auth login --web` couldn't open the Windows browser. Fixed with `sudo apt install -y wslu`. If browser-launch fails from WSL again, re-install wslu.
