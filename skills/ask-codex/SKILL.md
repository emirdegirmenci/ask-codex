---
name: ask-codex
description: >-
  Use when the user wants a second opinion, code review, plan, or implementation from OpenAI Codex
  — triggers include "ask codex", "codex'e sor", "codex ne diyor", "let codex
  review/plan/refactor", "second opinion", "get codex to implement X". Also fires proactively as
  an OFFER (never a silent call) on high-stakes engineering decisions: architecture choices,
  irreversible/high-blast-radius changes, stubborn deep-debugging, a genuine fork between two
  strong approaches, or a security-critical diff. Delegates coding work to the local first-party
  codex MCP server (OpenAI Codex CLI running as codex mcp-server, stdio). Runs entirely locally;
  no third-party bridge code.
---

# ask-codex — delegate to OpenAI Codex, natively

Claude and Codex are teammates. This skill defines **when** to hand work to Codex,
**which current GPT-6 model + effort** to use, and **how** to keep the hand-off compact.
Codex runs on the user's own Codex/ChatGPT seat through the local first-party
`codex mcp-server`.

## Tools

Resolve the Codex MCP tools with `ToolSearch("codex")` when needed:

- **`mcp__codex__codex`** — start a task. Key params: `prompt`, `cwd`, `sandbox`,
  `model`, `approval-policy`, and `config`.
- **`mcp__codex__codex-reply`** — continue the same conversation by id + `prompt`.

Policy defaults live in `$CODEX_HOME/config.toml`. Override only when the task needs it.

## Model routing — automatic, small, opinionated

Do not ask the user to choose a model unless they explicitly want to. Pick it automatically.
Only use the three GPT-6 slugs in [MODELS.md](MODELS.md). **Never fall back to GPT-5.x,
Terra, or another legacy model.**

### Default

For the plugin's most common jobs — **code review and plan critique/approval** — use:

**`gpt-6-luna` / `high`**

This is the normal default, not just the "cheap" fallback.

### Escalate to Sol

Use **`gpt-6-sol` / `high`** when one or more apply:

- architecture or system-design decisions,
- auth/security/permissions/secrets,
- database schema changes or migrations,
- subtle concurrency/state/distributed-system bugs,
- broad refactors spanning several subsystems,
- whole-repo reasoning with meaningful blast radius,
- the first Luna review found uncertainty that needs a stronger second pass.

### Escalate to Astra

Use **`gpt-6-astra` / `medium`** only when the task is exceptional:
Sol/high was still inconclusive, the work is unusually difficult end-to-end, or the user
explicitly asks for the strongest available model. Prefer raising an existing model to
`xhigh` before spending Astra casually.

Supported efforts are listed in [MODELS.md](MODELS.md). Do not invent model names or efforts.

Map the choice onto each start call:

- `model="<slug>"`
- `config={"model_reasoning_effort": "<effort>"}`

Tell the user the selected model in one short line only when useful; don't turn model selection
into a conversation tax.

## Proactively offering Codex

Offer a Codex second opinion on:

- architecture/design with lasting consequences,
- irreversible or high-blast-radius changes,
- a stubborn bug without a confirmed root cause,
- a genuine fork between strong approaches,
- security-critical changes.

Offer once, with the already-selected model, then wait for consent. Never silently spend the
user's Codex allowance.

## Methods

| Method | When | sandbox | Return contract |
|---|---|---|---|
| **review** | second pair of eyes on a diff | `read-only` | findings only, ranked by severity |
| **plan** | critique/approve a design or implementation plan | `read-only` | verdict, missed risks, concrete fixes |
| **refactor** | restructure existing code | `workspace-write` | changed files + compact diff summary |
| **implement** | build a feature/fix | `workspace-write` | changed files + ≤5-line summary |
| **consult** | challenge Claude's approach | `read-only` | verdict + reasoning, ≤10 lines |

## Prompt recipe

Every Codex prompt should contain:

1. **Role + method** — reviewer, planner, implementer, etc.
2. **Concrete target** — repo/path/diff/failing test. Prefer paths over pasted files.
3. **Definition of done** — correctness/security/compatibility constraints.
4. **Return contract** — exact small output shape.

For plan approval, ask Codex to **challenge the plan rather than rewrite it by default**:
identify blockers, missing edge cases, unsafe assumptions, and only propose changes that matter.

For review, prioritize correctness, security, regressions, data loss, race conditions, API/schema
compatibility and missing tests. Do not waste tokens on praise or style nits unless asked.

## Token discipline

1. Pass **cwd + paths**, not file contents, whenever Codex can read the repo itself.
2. Keep returned output bounded.
3. Review/plan/consult stay `read-only`.
4. One-shot work should call Codex directly.
5. **Multi-turn work stays supported**: use the `codex-teammate` subagent for
   implement → self-review → fix, iterative plan refinement, or deep review follow-ups.

## Multi-turn escalation

Keep the same model for a conversation unless there is a clear reason to escalate. A good loop is:

- start with the routed model,
- ask one focused follow-up using `codex-reply`,
- if the result is still uncertain, escalate the **next fresh Codex conversation** to Sol or Astra
  with a concise summary of the unresolved question.

Do not bounce models every turn.

## Raw vs summarized context

Default to a tight instruction and repo paths. When correctness depends on exact material
(error text, spec language, a small critical diff), pass it verbatim. User instructions such as
"do not summarize" take precedence.

## Sandbox boundary

`read-only` for review/plan/consult. `workspace-write` only when edits are required.
Never use `danger-full-access` unless the user explicitly requests it and understands the risk.

## Examples

**Review current diff — default route**
```
mcp__codex__codex(
  prompt="Act as a code reviewer. Review the uncommitted diff in this repo.
          Focus on correctness, regressions, security and missing tests.
          Return only severity-ranked findings with file/line references.",
  cwd="<abs repo path>",
  sandbox="read-only",
  model="gpt-6-luna",
  config={"model_reasoning_effort": "high"})
```

**Critique / approve a plan — default route**
```
mcp__codex__codex(
  prompt="Act as a skeptical senior engineer. Critique the plan below against this repo.
          Identify blockers, missed edge cases and unsafe assumptions. If it is sound,
          say APPROVE and list only residual risks. Keep the answer under 12 lines.
          <PLAN>...</PLAN>",
  cwd="<abs repo path>",
  sandbox="read-only",
  model="gpt-6-luna",
  config={"model_reasoning_effort": "high"})
```

**High-blast-radius architecture review — Sol**
```
mcp__codex__codex(
  prompt="Review this architecture change across the repository. Focus on failure modes,
          migration/rollback, security boundaries and compatibility. Findings only.",
  cwd="<abs repo path>",
  sandbox="read-only",
  model="gpt-6-sol",
  config={"model_reasoning_effort": "high"})
```

## Relationship to codex-teammate

Keep **`codex-teammate`** for multi-turn Codex loops. It must apply this same routing policy
rather than requiring the caller to manually choose a model every time. One-shot review/plan
requests should remain direct to avoid unnecessary subagent overhead.
