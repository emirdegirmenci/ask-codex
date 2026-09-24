<div align="center">

# 🤝 ask-codex

**Make OpenAI Codex a teammate inside Claude Code.**

Delegate reviews, plan validation, refactors, and implementations to Codex over the local
first-party `codex` MCP server — with a small GPT-6 routing policy and optional multi-turn loops.

[![Claude Code Plugin](https://img.shields.io/badge/Claude_Code-Plugin-D97757?logo=anthropic&logoColor=white)](https://docs.claude.com/en/docs/claude-code)
[![OpenAI Codex](https://img.shields.io/badge/OpenAI-Codex-412991?logo=openai&logoColor=white)](https://developers.openai.com/codex/cli/)
[![MCP](https://img.shields.io/badge/protocol-MCP-1f6feb)](https://modelcontextprotocol.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](./LICENSE)
[![Version](https://img.shields.io/badge/version-1.1.0-blue)](https://github.com/emirdegirmenci/ask-codex/releases)

</div>

---

## What it does

ask-codex teaches Claude Code when to bring Codex in, which model to use, and how to keep the
handoff compact. It is optimized for the two jobs this plugin is used for most:

- **code review**
- **plan critique / approval**

It also keeps the `codex-teammate` subagent for multi-turn workflows such as
implement → self-review → fix.

Everything runs locally on your own Codex/ChatGPT seat through OpenAI's first-party
`codex mcp-server`.

## Model routing

The plugin intentionally uses only the current GPT-6 routing set:

| Task | Model | Effort |
|---|---|---|
| Normal code review | `gpt-6-luna` | `high` |
| Plan critique / approval | `gpt-6-luna` | `high` |
| Focused debugging / well-scoped coding | `gpt-6-luna` | `high` |
| Architecture / security / migrations / broad cross-cutting reasoning | `gpt-6-sol` | `high` |
| Exceptional escalation | `gpt-6-astra` | `medium` |

The normal default is **`gpt-6-luna/high`**. The plugin escalates to Sol only when the
correctness risk or reasoning scope justifies it, and reserves Astra for genuinely hard cases.

GPT-5.x, Terra, and legacy aliases are deliberately excluded from routing.

## Multi-turn stays supported

One-shot review and plan requests call Codex directly.

For workflows that genuinely benefit from multiple turns, Claude can use the
`codex-teammate` subagent:

- implement → self-review → fix
- iterative plan refinement
- deep-review follow-ups

The agent uses the same routing policy and keeps a model stable within a conversation.
If escalation is needed, it starts a fresh stronger conversation rather than bouncing models
mid-thread.

## Install

### 1. Register Codex MCP

```bash
claude mcp add codex -- codex mcp-server
```

On Windows, if `codex` is a shim:

```bash
claude mcp add codex -- cmd /c codex mcp-server
```

### 2. Install the plugin

```
/plugin marketplace add emirdegirmenci/ask-codex
/plugin install ask-codex@ask-codex
```

## Examples

- *"Ask Codex to review my uncommitted diff."* → `gpt-6-luna/high`, read-only.
- *"Get Codex to challenge and approve this plan."* → `gpt-6-luna/high`, read-only.
- *"Review this auth migration architecture."* → `gpt-6-sol/high`, read-only.
- *"Have Codex implement this, review itself, then fix confirmed issues."* → multi-turn subagent.

## Model list maintenance

`skills/ask-codex/MODELS.md` is generated from the local Codex model cache, but
`scripts/sync-models.py` applies an explicit GPT-6 allowlist so refreshing the cache cannot
silently reintroduce old models.

```bash
python scripts/sync-models.py
python scripts/sync-models.py --check
```

If an approved model is unavailable on the current seat, the plugin reports that instead of
silently falling back to a legacy model.

## Token discipline

- Pass `cwd` + paths instead of pasting repository contents.
- Keep review/plan/consult read-only.
- Bound Codex replies.
- Use direct one-shot calls by default.
- Use the multi-turn subagent only when another turn materially improves the result.

## Trust boundary

`read-only` inspects. `workspace-write` allows edits in `cwd`.
`danger-full-access` is never used unless explicitly requested.

## License

[MIT](./LICENSE) © Emir Degirmenci

---

<div align="center">
<sub>Not affiliated with OpenAI or Anthropic. "Codex" and "Claude" are trademarks of their respective owners.</sub>
</div>
