# KOTR Builder queue

Highest priority first. `- [ ]` = todo, `- [x]` = done. Each item tags an **engine
affinity**: `(any)` = any engine, `(desktop)` = needs the desktop app's Chrome MCP /
computer-use (the WSL `claude -p` loop must skip these). Pick the top unchecked item whose
affinity matches you. Keep items small enough to finish + verify in one cycle.

## Foundation (done first, every machine)
- [x] Permissions-first: curated-broad allow-list + app grants + kill switch
      (`Systems_Migration/bootstrap/grant_all_permissions.md`)

## Finish the stretch items
- [ ] `(desktop)` **Standalone KOTR bot app.** Drive Opera GX via the Chrome MCP through
      discord.com/developers/applications → create application+bot "KOTR" (posting only) →
      reset + read token → save to `cli/discord/.env` as `KOTR_BOT_TOKEN` → OAuth2 invite
      (scope `bot`; Send Messages + Read History) → authorize into "Hugz & Ticklez
      Enterprisez". Captcha → append to `STAGED_FOR_EVAN.md`. Verify:
      `post_as_bot.py --whoami --token-env KOTR_BOT_TOKEN` shows the KOTR bot.
- [ ] `(any)` **Bidirectional KOTR↔Gir.** Duplicate `~/Gir/tools/discord_operator_listener.py`
      into a tiny KOTR gateway listening in `#kotr-ai-builders` on `KOTR_BOT_TOKEN`; run in
      tmux. Demonstrate KOTR posts → Gir acks → KOTR acks back. Verify by screenshot.
      (Blocked until the KOTR bot token exists.)
- [x] `(any)` **Gir Ollama backend live.** Make Windows Ollama reachable from WSL
      (`OLLAMA_HOST=0.0.0.0` + firewall allow 11434, or run the ollama call Windows-side).
      Start `~/Gir/tools/discord_operator_listener.py run-loop` in tmux. Verify: send
      `gir help` in `#gir-ops-private`, screenshot Gir's reply.
      <!-- DONE 2026-06-15 claude-p: Ollama reachable @localhost:11434 (generate eval_count=30);
      run-loop pid51810 alive+polling; GIR bot r/w #gir-ops-private; response path proven via
      prod funcs -> GIR menu reply msg 1515970670155268197. Human-typed auto-trigger staged for Evan. -->
- [x] `(any)` **Order 7 map push.** Push `Knights_of_the_Round_Table_v0.50.w3x` +
      `_extract_v050/war3map.j` + `_crew/` to the `Warcraft_III` repo (Git LFS for the
      `.w3x` if >100 MB). Verify the files on GitHub.

## Then: KOTR feature/dev work
- [ ] `(any)` Pull the next item from `Maps/KOTR/_crew/we_diffs/` (apply-order) or the
      hero-inventory command-hub spec; advance one verified unit; log it.
