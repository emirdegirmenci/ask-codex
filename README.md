<div align="center">

# 🤝 ask-codex

**Make OpenAI Codex a teammate inside Claude Code.**

Delegate reviews, plans, refactors, and implementations to Codex over the local
first-party `codex` MCP server — with the model + reasoning effort matched to the task,
and a subagent that keeps multi-turn loops out of your main context.

[![Claude Code Plugin](https://img.shields.io/badge/Claude_Code-Plugin-D97757?logo=anthropic&logoColor=white)](https://docs.claude.com/en/docs/claude-code)
[![OpenAI Codex](https://img.shields.io/badge/OpenAI-Codex-412991?logo=openai&logoColor=white)](https://developers.openai.com/codex/cli/)
[![MCP](https://img.shields.io/badge/protocol-MCP-1f6feb)](https://modelcontextprotocol.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](./LICENSE)
[![Version](https://img.shields.io/badge/version-1.0.0-blue)](https://github.com/emirdegirmenci/ask-codex/releases)

`#claude-code` · `#codex` · `#mcp` · `#ai-pair-programming` · `#code-review` · `#developer-tools`

</div>

---

## Why

Claude Code is great. So is Codex. They're better together — one drafts, the other checks;
one plans, the other stress-tests. **ask-codex** teaches Claude *when* to bring Codex in,
*which* Codex model + effort fits the job, and *how* to phrase the hand-off so the answer
comes back tight instead of as a wall of tokens.

Everything runs **locally on your own Codex/ChatGPT seat** through OpenAI's first-party
`codex mcp-server`. There is **no third-party bridge** and no key sharing.

## What you get

| Piece | What it does |
|---|---|
| **`ask-codex` skill** | Fires on "ask codex", "second opinion", "let codex review/plan/refactor" — and **proactively offers** Codex on high-stakes calls (architecture, irreversible changes, stubborn bugs, security-critical diffs). Never a silent call: it offers, you decide. |
| **`codex-teammate` subagent** | Runs multi-turn Codex loops (implement → self-review → fix) in an isolated context and returns only the outcome. |
| **`scripts/sync-models.py`** | Regenerates the model list from Codex's own cache so the skill never suggests a model that doesn't exist or an effort a model can't do. |

## Requirements

- [Claude Code](https://docs.claude.com/en/docs/claude-code)
- [OpenAI Codex CLI](https://developers.openai.com/codex/cli/) (`codex`), signed in to your seat
- Python 3.9+ (only for the optional `sync-models.py` maintenance script)

## Install

### 1. Register Codex as an MCP server for Claude Code

ask-codex talks to Codex through the MCP server that ships with the Codex CLI:

```bash
claude mcp add codex -- codex mcp-server
```

(On Windows, if `codex` is a shim: `claude mcp add codex -- cmd /c codex mcp-server`.)

Verify it's connected with `/mcp` inside Claude Code — you should see the `codex` server
exposing `codex` and `codex-reply` tools.

### 2. Add the plugin

From inside Claude Code:

```
/plugin marketplace add emirdegirmenci/ask-codex
/plugin install ask-codex@ask-codex
```

That's it. The skill and the `codex-teammate` subagent are now available.

> A git release tag is **not** required to install — a Claude Code marketplace is just a repo
> with `.claude-plugin/marketplace.json`. Tags/releases (like `v1.0.0`) are provided for
> version tracking and discoverability.

## Use it

Just talk to Claude Code:

- *"Ask Codex to review my uncommitted diff."* → read-only review, findings ranked by severity.
- *"Get a second opinion on this plan from Codex."* → verdict + reasoning in ≤10 lines.
- *"Let Codex refactor `parser.py` to remove the duplication."* → Codex writes, returns the diff.
- *"Have Codex implement the retry logic and self-review it."* → multi-turn loop via the subagent.

On a heavy call you didn't ask about, Claude will *offer*:

> *"This is an architecture decision with real blast radius — want a Codex second opinion too?
> (`gpt-5.6-sol`/`high`, read-only.)"*

You say yes or no. It never spends your Codex seat silently.

## Picking the model + effort

The skill matches the model to the weight of the work:

| Task | Model | Effort |
|---|---|---|
| Hard / architecture / deep debugging / whole-repo | `gpt-5.6-sol` | `high` (→ `max`/`ultra` for the hardest) |
| Everyday coding, balanced | `gpt-5.6-terra` | `medium` |
| Fast, simple, repetitive | `gpt-5.6-luna` | `medium` |

The full, always-accurate list lives in
[`skills/ask-codex/MODELS.md`](./skills/ask-codex/MODELS.md) — it's **generated** from the
Codex CLI's own model cache, so it can't drift into suggesting models that aren't on your seat.

### Keeping the model list fresh

If OpenAI ships new Codex models (or your seat changes), refresh the list:

```bash
python scripts/sync-models.py           # rewrite MODELS.md from your Codex cache
python scripts/sync-models.py --check    # CI-friendly: exit 1 if MODELS.md is stale
```

It reads `$CODEX_HOME/models_cache.json` (default `~/.codex/models_cache.json`). If that cache
isn't present, the committed `MODELS.md` is kept as the shipped fallback.

## How it stays cheap

Delegation only saves tokens if the hand-off is thin both ways. The skill enforces four habits:
pass **paths + `cwd`** (Codex reads the repo itself, Claude never loads the files), **bound the
reply** ("diff only", "findings only"), prefer **`read-only`** for review/plan/consult, and run
heavy multi-turn work in the **`codex-teammate`** subagent so the chatter never hits your main
context.

## Trust boundary

`read-only` inspects; `workspace-write` lets Codex edit files in `cwd`; `danger-full-access`
removes the sandbox and is never used unless you explicitly ask. Central policy lives in your
`$CODEX_HOME/config.toml`.

## License

[MIT](./LICENSE) © Emir Degirmenci

---

<div align="center">
<sub>Not affiliated with OpenAI or Anthropic. "Codex" and "Claude" are trademarks of their respective owners.</sub>
</div>
