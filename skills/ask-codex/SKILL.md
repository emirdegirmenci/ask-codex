---
name: ask-codex
description: Use when the user wants a second opinion, code review, plan, or implementation from OpenAI Codex — triggers include "ask codex", "codex'e sor", "codex ne diyor", "let codex review/plan/refactor", "second opinion", "get codex to implement X". Also fires proactively as an OFFER (never a silent call) on high-stakes engineering decisions: architecture choices, irreversible/high-blast-radius changes, stubborn deep-debugging, a genuine fork between two strong approaches, or a security-critical diff. Delegates coding work to the local first-party `codex` MCP server (OpenAI Codex CLI running as `codex mcp-server`, stdio). Runs entirely locally; no third-party bridge code.
---

# ask-codex — delegate to OpenAI Codex, natively

Claude and Codex are teammates. This skill defines **when** to hand work to Codex,
**which model + effort** to use, and **how** to phrase the request so it comes back tight.
Codex runs on the user's own Codex/ChatGPT seat through the local `codex` MCP server
(`codex mcp-server`, first-party OpenAI). No third-party bridge is involved.

## Tools

The `codex` MCP server exposes two tools. If they aren't loaded in the session yet, resolve
them first with `ToolSearch("codex")`:

- **`mcp__codex__codex`** — start a Codex task. Key params: `prompt` (required), `cwd`
  (working directory — Codex reads the repo from here), `sandbox`
  (`read-only` | `workspace-write` | `danger-full-access`), `model`, `approval-policy`,
  and `config` (per-call overrides, e.g. reasoning effort).
- **`mcp__codex__codex-reply`** — continue an existing Codex conversation by `conversationId`
  + `prompt` (multi-turn without re-sending context).

Policy defaults (sandbox, approval) live centrally in `$CODEX_HOME/config.toml`. Only override
per call when the task needs it.

## Model + effort: match the work, then say what you picked

Do **not** silently fall back to the config default, and do **not** stall the user with a bare
"which model?". Match the model + reasoning effort to the weight of the task, then either apply
it (stating your choice in one line) or offer 2–3 sensible candidates. **Only the slugs listed in
[MODELS.md](MODELS.md) exist** — that file is generated from the Codex seat's own cache, so it is
the source of truth. Never invent a slug or pass an effort a model does not support.

Quick map (full table + supported efforts in [MODELS.md](MODELS.md)):

- **Hard / architecture / deep debugging / whole-repo analysis** → `gpt-5.6-sol` at `high`
  (step up to `max` or `ultra` for the truly hardest).
- **Everyday coding, balanced quality / speed / cost** → `gpt-5.6-terra` at `medium`.
- **Fast, simple, repetitive, well-defined** → `gpt-5.6-luna` at `medium`.

Say it in one line, e.g. *"This is heavy — asking with `gpt-5.6-sol`/`high`."* or offer a choice:
*"`gpt-5.6-sol`/`high` (deep) or `gpt-5.6-terra`/`medium` (fast) — which one?"*. If the user already
named a model + effort, use it directly and skip the question.

Map the choice onto the call:
- **model** → the `model` param (e.g. `model="gpt-5.6-sol"`).
- **reasoning effort** → `config={"model_reasoning_effort": "high"}`.

If [MODELS.md](MODELS.md) looks stale (a model is missing, or a call rejects an effort), refresh it:
`python scripts/sync-models.py`. It rewrites the table from `$CODEX_HOME/models_cache.json`.

## Proactively offering Codex (offer — never a silent call)

On high-stakes engineering moments, don't wait to be asked. Surface a **one-line offer** to bring
in Codex as a second set of eyes, pre-picking a sensible model + effort. Offer when the moment is:

- an **architecture / design** decision with lasting consequences,
- an **irreversible or high-blast-radius** change (schema, auth, migrations, deletes, deploys),
- a **stubborn bug** you've circled without a confirmed root cause,
- a genuine **fork between two strong approaches** where a tie-breaker helps,
- a **security-critical** diff or one touching secrets / public surfaces.

Example: *"This is an architecture call with real blast radius — want me to get a Codex second
opinion too? (`gpt-5.6-sol`/`high`, read-only.)"* Then **wait for a yes**. Do not silently spend
the user's Codex seat, and do not offer on trivial or well-understood work — a noisy offer is worse
than none. This preserves the standing rule: **ask before calling; the user always decides.**

## The five methods

Pick the method, then set `sandbox` + the return shape accordingly.

| Method | When | `sandbox` | Ask Codex to return |
|---|---|---|---|
| **review** | second pair of eyes on a diff | `read-only` | findings only, ranked by severity |
| **plan** | design / approach for a task | `read-only` | the plan only, numbered steps |
| **refactor** | restructure existing code | `workspace-write` | the diff only |
| **implement** | build a feature / fix | `workspace-write` | diff + ≤5-line summary |
| **consult** | critique of Claude's own approach | `read-only` | verdict + reasoning, ≤10 lines |

## Writing the prompt: make Codex's job unambiguous

A good Codex prompt has four parts, in order. Skipping any of them is where weak results come from:

1. **Role + method** — one line naming what Codex is doing: *"Act as a reviewer."* /
   *"You are implementing a fix."*
2. **Concrete target** — the paths, the diff, the failing test, the exact error. Point at the repo,
   don't describe it. *"Review the uncommitted changes in `src/auth/` (see `git diff`)."*
3. **Definition of done** — the bar the answer must clear. *"Focus on correctness and security;
   ignore style."* / *"Behavior must stay identical."*
4. **Return contract** — the exact shape and size of the reply. *"Return only a severity-ranked
   list. No praise, no summary, no restated code."*

The single biggest quality lever is the return contract: an unconstrained Codex reply is a wall of
text that lands back in Claude's context and costs tokens for nothing. Always bound it.

## Token discipline (this is where the savings come from)

Delegating to Codex only saves tokens if you delegate **thin** and receive **thin**:

1. **Pass paths + `cwd`, not file contents.** Codex reads the repo itself from `cwd`. Claude's
   context never loads the files just to "hand them over".
2. **Constrain the output** (return contract above). A bounded reply is a cheap reply.
3. **Use `read-only` for review / plan / consult.** Safer and cheaper than write mode.
4. **Heavy multi-turn → run in the `codex-teammate` subagent.** The back-and-forth stays in the
   subagent's isolated context; only its final result returns to the main thread.

## Summarize vs. pass raw

Default: send Codex a **tight** instruction, not the whole conversation. **But when correctness
depends on full fidelity** (a subtle bug, an exact error string, a spec that must not be
paraphrased), pass the material **verbatim** — do not summarize. If the user says "don't summarize,
give it as-is", honor it: put the raw text / diff / error into the `prompt` unchanged. Losing a
detail to summarization is worse than spending the tokens.

## Sandbox = trust boundary

`read-only` inspects only. `workspace-write` lets Codex edit files in `cwd`. `danger-full-access`
removes the sandbox entirely — never use it unless the user explicitly asks and trusts the repo.
For anything that only inspects code (review / plan / consult), stay `read-only`.

## Examples

Each call carries the chosen `model` + `config.model_reasoning_effort`. The `<model>` / `<effort>`
placeholders stand in for that choice.

**Review the current diff (thin in, thin out):**
```
mcp__codex__codex(
  prompt="Act as a reviewer. In this repo, review the uncommitted changes (git diff).
          Focus on correctness and security; ignore style. Return only a severity-ranked
          list of findings — no praise, no summary, no restated code.",
  cwd="<abs repo path>",
  sandbox="read-only",
  model="<model>",
  config={"model_reasoning_effort": "<effort>"})
```

**Second opinion on Claude's plan (pass the plan raw):**
```
mcp__codex__codex(
  prompt="Critique this approach, given verbatim below. Where does it break? What did it miss?
          Verdict + reasoning in ≤10 lines.\n\n<PLAN>\n...\n</PLAN>",
  cwd="<abs repo path>",
  sandbox="read-only",
  model="<model>",
  config={"model_reasoning_effort": "<effort>"})
```

**Delegate a refactor (Codex writes, returns the diff):**
```
mcp__codex__codex(
  prompt="You are refactoring <file> to <goal>. Behavior must stay identical.
          Return the diff only.",
  cwd="<abs repo path>",
  sandbox="workspace-write",
  model="<model>",
  config={"model_reasoning_effort": "<effort>"})
```

## Relationship to the subagent

For a one-shot call, invoke the tool directly from the main thread. For anything that will take
several Codex turns (iterate on a plan, implement → self-review → fix), dispatch the
**`codex-teammate`** subagent instead — it owns the loop and returns only the outcome.
