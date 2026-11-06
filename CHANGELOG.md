# Changelog

## 2.0.0 — 2026-11-06

**Breaking: Codex is now driven through the CLI (`codex exec`), not the MCP server.**

Codex CLI 0.160.1 removed the `codex mcp-server` subcommand, so the `mcp__codex__codex` and
`mcp__codex__codex-reply` tools that 1.x relied on no longer exist.

### Changed
- `ask-codex` skill: command templates built on `codex exec` (prompt via stdin from a temp file,
  explicit sandbox (`-s`, or `-c 'sandbox_mode=...'` on resume/review), `-C`, `-o` for the final message, `--json` to capture the session id), multi-turn
  via `codex exec resume <thread_id>`, and the native
  `codex exec review --uncommitted|--base|--commit` path for plain diff reviews. Flags that were
  not exercised are labelled unverified in the skill.
- `codex-teammate` agent: uses Bash + `codex exec` / `codex exec resume` instead of MCP tools.
- Model routing updated for the current catalogue: `gpt-6.1-sol/high` default, `gpt-6.1-terra`
  balanced, `gpt-6-luna` cheap/fast, `gpt-6-astra` for the hardest work; `gpt-6-sol` (previous
  generation) only when a 6.1 model is unavailable on the seat, `gpt-5.6-*` (legacy) only on explicit
  request; hidden models never used.
  Efforts now include `max` and `ultra` where the model supports them.
- `scripts/sync-models.py` and `MODELS.md` regenerated for the new slugs, status column and efforts.
- Removed the MCP badge, the `claude mcp add codex` install step and the `mcp` keywords.

### Upgrading from 1.x
The plugin no longer uses the `codex` MCP server. Clean up the old registration yourself (the
plugin does not touch your config):

1. `claude mcp remove codex`
2. Delete the `[mcp_servers.codex]` block from `~/.codex/config.toml`, if present.
3. Update the plugin, and re-copy `skills/ask-codex` / `agents/codex-teammate.md` if you installed
   them manually outside the plugin system.

Requires a Codex CLI with `codex exec` (verified with 0.160.1).

## 1.1.1 and earlier

MCP-based releases (`mcp__codex__codex`), GPT-6 Luna/Sol/Astra routing.
