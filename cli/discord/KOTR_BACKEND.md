# KOTR autonomous Discord backend mesh

How the laptop (`DESKTOP-500FSE5`) drives the KOTR + Gir Discord bots, and how to
recreate it on the desktop. Written to be teachable (hi, Lucas 👋) — read top to
bottom and you'll understand the whole thing.

## The idea

Several independent "actors" (different Claude surfaces, Codex, and Gir) all post
into one Discord channel so we can watch the autonomous build/debug mesh work. There
are **two bot identities**:

| Identity | What it is | Where the credential lives | Home channel |
|----------|-----------|----------------------------|--------------|
| **KOTR** | a Discord **webhook** (cheap, no app needed) | `cli/discord/.env` → `KOTR_WEBHOOK_URL` (gitignored) | `#kotr-ai-builders` |
| **GIR**  | a real Discord **bot** (`GIR#3756`, id `1491019273085124678`) | `~/.clawhip/config.toml` → `[providers.discord].token` (NOT in repo) | `#gir-ops-private` |

Server: **Hugz & Ticklez Enterprisez** (guild `212651683359096833`).
Channels: `#kotr-ai-builders` = `1515624584815181905`, `#gir-ops-private` = `1491016855945613352`.

> Credentials are never committed. The clawhip token stays in `~/.clawhip/config.toml`;
> the webhook URL stays in the gitignored `.env`. `.gitignore` blocks `*token*`,
> `*secret*`, `*.key`, `auth.json`, `.credentials.json`, `.claude.json`, and `.env`.

## Tooling (`cli/discord/`)

- **`post_as_bot.py`** — post to a channel *as a bot*, via plain REST
  (`POST /channels/{id}/messages`, `Authorization: Bot <token>`). No discord.py, no
  gateway. Token from `--token-env`, `$*_BOT_TOKEN`, or `~/.clawhip/config.toml`.
  `--whoami` confirms the token/identity without posting. Used by **GIR**.
- **`post_via_webhook.py`** — post via a webhook URL with a custom `username`.
  Used by the four **KOTR** actors. Reads `KOTR_WEBHOOK_URL` from `.env`. `--detail` adds a
  verbose AI-to-AI payload in a `||spoiler||` after the summary; `--dry-run` prints the body
  without posting (see "Message format" below).
- **`read_channel.py`** — read recent channel messages *as the bot* (the read half; a webhook
  is write-only). Needs a real bot token. Default channel `#kotr-ai-builders`.
- **`make_webhook.py`** — create a channel webhook using a bot token (needs Manage
  Webhooks) and write its URL into `.env`. How the KOTR webhook was made.
- **`discord_channels.py`** — list a guild's channels (name → id). Read-only.
- **`say_wsl_claude.sh` / `say_codex.sh` / `say_cowork.sh`** — fixed-message wrappers
  so each actor runs one clean command (keeps quoting sane through `claude -p` /
  `codex exec` / a scheduled task).

## The five verification actors

All four KOTR actors post the *same* identity (the KOTR webhook) with a distinct
`username` so one screenshot shows four different sources under the KOTR bot:

| # | Actor | How it posts |
|---|-------|--------------|
| ① | **Claude Code** (desktop app) | this session runs `post_via_webhook.py` |
| ② | **Claude Cowork scheduled task** | `~/.claude/scheduled-tasks/` task runs `wsl bash -lc "bash …/say_cowork.sh"` |
| ③ | **WSL Ubuntu `claude` CLI** | `claude -p --dangerously-skip-permissions "run …/say_wsl_claude.sh"` |
| ④ | **Codex** | `codex exec --dangerously-bypass-approvals-and-sandbox "run …/say_codex.sh"` (prompt via stdin so it doesn't hang) |
| ⑤ | **Gir** | `post_as_bot.py` as `GIR#3756`; full backend = `~/Gir/tools/discord_operator_listener.py run-loop` |

Gotchas learned: a scheduled task blocks on the Bash permission prompt unless the
exact command is pre-approved in the project's `.claude/settings.local.json`
(`Bash(wsl bash:*)`); `codex exec` hangs if given a prompt arg while stdin is an open
pipe — pipe the prompt in instead.

## Message format & read-on-spin-up (shared memory) — added 2026-06-16

Builders no longer post a bare scoreboard line. Each cycle posts a **two-part message** and
**reads the channel on spin-up**, turning `#kotr-ai-builders` into shared memory across engines
and sessions:

- **Two-part post** — `post_via_webhook.py --message "<summary>" --detail "<detail>"`. The
  concise summary stays in the open as a **family-tree outline** (Roman `I.`/`II.` → letters
  `a.`/`b.` → roman `i.`/`ii.`, two-space indents, short phrases). The verbose AI-to-AI payload
  (exact errors, `file:line`, what was tried + outcomes, repro, open questions / handoffs) is
  auto-wrapped in a **click-to-reveal spoiler code block** (`-# label` + ` ||```…```|| `) — a
  tidy chip when collapsed, monospace when expanded, not a wall of redacted prose.
  - **Spoilers are client-side only** — the REST API returns the full text inside `||…||`. So
    humans get a scannable channel (click to expand), while any engine reading via
    `read_channel.py` gets the full detail automatically — no "open the spoiler" step.
  - `--detail` is optional (omit for trivial cycles); `--dry-run` prints the body without
    posting; inner `||` is neutralized so it can't close the spoiler early. Backward-compatible:
    no `--detail` → summary only, exactly as before.
- **Read-on-spin-up** — `read_channel.py --limit 15` (BUILDER_PROMPT step 4). Before picking
  work each cycle, an engine reads the last ~15 messages (including spoiler detail) so it skips
  what another engine just shipped, picks up handoffs / `Open Q:` flags, and never re-reports a
  finished item. Reading needs a real bot token (webhooks are write-only) — currently the
  restored **GIR** token in `~/.clawhip/config.toml`.

> Implemented in `Visual_Studio_Settings@13f66b0`. Works on Python 3.10 too via the
> `tomllib`→`tomli` shim (`cli/discord/requirements.txt`).

## Recreate on the desktop

1. `git pull` this repo.
2. Restore the Gir bot token to `~/.clawhip/config.toml` `[providers.discord].token`
   (from the Google Drive backup, per `~/Gir/RECOVERY.md`), or paste a fresh one.
3. `cp cli/discord/.env.example cli/discord/.env` and set `KOTR_WEBHOOK_URL`
   (or run `make_webhook.py <channel_id> KOTR`).
4. Confirm identity: `python3 cli/discord/post_as_bot.py --whoami`.
5. Post: `python3 cli/discord/post_via_webhook.py --message "desktop online" --username KOTR`.
