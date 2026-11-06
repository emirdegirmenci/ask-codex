<div align="center">

# 🤝 ask-codex

**Make OpenAI Codex a teammate inside Claude Code.**

Delegate reviews, plan validation, refactors, and implementations to Codex through the local
Codex CLI (`codex exec`) — with a small GPT-6.1 routing policy and optional multi-turn loops.

[![Claude Code Plugin](https://img.shields.io/badge/Claude_Code-Plugin-D97757?logo=anthropic&logoColor=white)](https://docs.claude.com/en/docs/claude-code)
[![OpenAI Codex](https://img.shields.io/badge/OpenAI-Codex-412991?logo=openai&logoColor=white)](https://developers.openai.com/codex/cli/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](./LICENSE)
[![Version](https://img.shields.io/badge/version-2.0.0-blue)](https://github.com/emirdegirmenci/ask-codex/releases)

</div>

---

## What it does

ask-codex teaches Claude Code when to bring Codex in, which model to use, and how to keep the
handoff compact. It is optimized for the two jobs this plugin is used for most:

- **code review**
- **plan critique / approval**

It also keeps the `codex-teammate` subagent for multi-turn workflows such as
implement → self-review → fix.

Everything runs locally on your own Codex/ChatGPT seat: Claude calls OpenAI's first-party
`codex exec` CLI through Bash. There is no MCP server and no third-party bridge.

## Model routing

| Task | Model | Effort |
|---|---|---|
| Code review, plan critique / approval, debugging, implementation, architecture / security (default) | `gpt-6.1-sol` | `high` |
| Well-scoped refactors / implementations where cost matters | `gpt-6.1-terra` | `high` |
| Quick consults, easy or mechanical tasks | `gpt-6-luna` | `high` |
| Hardest or still-unresolved work (escalation) | `gpt-6-astra` | `medium` |

The normal default is **`gpt-6.1-sol/high`**. Raise the effort (`xhigh`, `max`) before reaching
for Astra. `gpt-6-sol` (previous generation) and `gpt-5.6-*` (legacy) are used only on explicit
request or when a 6.1 model is unavailable; hidden models are never used.

## Multi-turn stays supported

One-shot review and plan requests call `codex exec` directly (the CLI's native
`codex exec review --uncommitted|--base|--commit` is used for plain diff reviews).

For workflows that genuinely benefit from multiple turns, Claude can use the
`codex-teammate` subagent:

- implement → self-review → fix
- iterative plan refinement
- deep-review follow-ups

The agent uses the same routing policy and continues a conversation with
`codex exec resume <thread_id>`, keeping the model stable within it. If escalation is needed,
it starts a fresh stronger conversation rather than bouncing models mid-thread.

## Install

### 1. Install the Codex CLI and sign in

Install `codex` (the OpenAI Codex CLI) and run it once to sign in. Verified with
`codex-cli 0.160.1`; `codex exec` must be available. Nothing needs to be registered with
Claude Code.

### 2. Install the plugin

```
/plugin marketplace add emirdegirmenci/ask-codex
/plugin install ask-codex@ask-codex
```

### Upgrading from 1.x

1.x used the `codex` MCP server, which Codex CLI 0.160.1 no longer ships. After updating, remove
the old registration (the plugin no longer uses it):

```bash
claude mcp remove codex
```

and delete any `[mcp_servers.codex]` block from `~/.codex/config.toml`. See
[CHANGELOG.md](./CHANGELOG.md).

## Examples

- *"Ask Codex to review my uncommitted diff."* → `gpt-6.1-sol/high`, native `codex exec review --uncommitted`.
- *"Get Codex to challenge and approve this plan."* → `gpt-6.1-sol/high`, read-only.
- *"Review this auth migration architecture."* → `gpt-6.1-sol/high`, read-only (`xhigh` if it stays inconclusive).
- *"Have Codex implement this, review itself, then fix confirmed issues."* → multi-turn subagent.

## Model list maintenance

`skills/ask-codex/MODELS.md` is generated from the local Codex model cache
(`$CODEX_HOME/models_cache.json`), but `scripts/sync-models.py` applies an explicit allowlist and
only renders user-facing models, so refreshing the cache cannot silently reintroduce an
unreviewed or hidden model.

```bash
python scripts/sync-models.py
python scripts/sync-models.py --check
```

If a model is unavailable on the current seat, the plugin reports that instead of silently
falling back to another one.

## Token discipline

- Pass `-C <repo>` + paths instead of pasting repository contents.
- Keep review/plan/consult read-only (`-s read-only`, always passed explicitly).
- Bound Codex replies (return contract) and read only the `-o` last-message file.
- Use direct one-shot calls by default.
- Use the multi-turn subagent only when another turn materially improves the result.

## Trust boundary

`read-only` inspects. `workspace-write` allows edits in the working root.
`danger-full-access` is never used unless explicitly requested. The sandbox is always passed
explicitly (`-s` on `codex exec`, `-c sandbox_mode=...` on `resume`) because your
`~/.codex/config.toml` defaults may be more permissive.

## License

[MIT](./LICENSE) © Emir Degirmenci

---

<div align="center">
<sub>Not affiliated with OpenAI or Anthropic. "Codex" and "Claude" are trademarks of their respective owners.</sub>
</div>
