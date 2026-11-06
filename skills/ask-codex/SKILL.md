---
name: ask-codex
description: >-
  Use when the user wants a second opinion, code review, plan, or implementation from OpenAI Codex
  — triggers include "ask codex", "codex'e sor", "codex ne diyor", "let codex
  review/plan/refactor", "second opinion", "get codex to implement X". Also fires proactively as
  an OFFER (never a silent call) on high-stakes engineering decisions: architecture choices,
  irreversible/high-blast-radius changes, stubborn deep-debugging, a genuine fork between two
  strong approaches, or a security-critical diff. Delegates coding work to the local Codex CLI
  (`codex exec`, run through Bash on the user's own seat). Runs entirely locally; no MCP server
  and no third-party bridge code.
---

# ask-codex — delegate to OpenAI Codex through the CLI

Claude and Codex are teammates. This skill defines **when** to hand work to Codex, **which
model + effort** to use, and **how** to call `codex exec` and keep the hand-off compact. Codex runs
on the user's own Codex/ChatGPT seat; Claude drives it with the Bash tool.

Verified against `codex-cli 0.160.1` on Windows (Git Bash). Anything not run end to end is marked
**(unverified)**.

## Calling Codex: `codex exec`

Always run Codex through Bash. Rules that apply to every call:

1. **Prompt goes through stdin from a temp file**, never as a long argv string (quoting, the
   ~8k Windows command limit, non-ASCII paths such as `arşiv`). Write the file with a quoted
   heredoc, then `... - < "$T/p.txt"`.
2. **Always pass `-s` explicitly** on `codex exec`. The user's `~/.codex/config.toml` may default
   to no approvals and full access, so relying on defaults is unsafe.
3. **Always pass `-m` and `-c model_reasoning_effort="<effort>"`** (the value is TOML, keep the
   quotes). Slugs and efforts come from [MODELS.md](MODELS.md).
4. **Capture the answer with `-o <file>`** and read that file; do not scrape stdout. Redirect
   stdout/stderr to files so they never flood the context.
5. **Calls can take minutes.** Use the Bash tool with `run_in_background: true` (you are notified
   on exit) or a long `timeout`; do not poll.
6. Set `PYTHONUTF8=1` if Codex or your own helper scripts will touch Python on Windows.
7. `-C <dir>` sets Codex's working root (verified with a non-ASCII path). Add
   `--skip-git-repo-check` when the directory is not a git repo.

### Start a task (verified)

```bash
T=$(mktemp -d)
cat > "$T/p.txt" <<'EOF'
<the four-part prompt, see "Prompt recipe">
EOF
PYTHONUTF8=1 codex exec \
  -m gpt-6.1-sol -c model_reasoning_effort="high" \
  -s read-only -C "<abs repo path>" --skip-git-repo-check \
  --json -o "$T/last.txt" - < "$T/p.txt" > "$T/events.jsonl" 2> "$T/err.txt"
echo "exit=$?"; cat "$T/last.txt"
```

- The final reply is in `$T/last.txt`. Exit code `0` = turn completed.
- `-s` is one of `read-only`, `workspace-write`, `danger-full-access` (see Methods).
- Drop `--json` and `> events.jsonl` if you do not need the session id (single one-shot call).
- Add `--ephemeral` for a one-shot you will never resume (nothing is persisted to disk).
- `--output-schema <file.json>` constrains the final message to a JSON Schema **(unverified)**.
- `-i <image>` attaches an image **(unverified)**; `--add-dir <dir>` grants extra writable dirs
  **(unverified)**.

### The session id (verified)

With `--json`, stdout is JSONL. The **first event** is:

```json
{"type":"thread.started","thread_id":"01a1afa6-3904-70b1-8ae3-693724b6fa17"}
```

The field is **`thread_id`** on the `thread.started` event; that UUID is the `SESSION_ID` for
`resume`. Extract it:

```bash
ID=$(sed -n 's/.*"type":"thread.started".*"thread_id":"\([^"]*\)".*/\1/p' "$T/events.jsonl" | head -1)
```

Other events seen: `turn.started`, `item.completed` (with `item.type` `agent_message` carrying
`text`, or `command_execution`), `turn.completed` (with token `usage`). Codex may also emit
`item.completed` events of `item.type: "error"` that only carry config warnings such as
"unrecognized configuration settings" from the user's `config.toml`; they are noise, not a failed
run. Judge success by the exit code and `turn.completed`.

### Continue a conversation (verified)

```bash
cat > "$T/p2.txt" <<'EOF'
<one focused follow-up>
EOF
cd "<abs repo path>"   # resume looks sessions up by cwd; there is no -C here
PYTHONUTF8=1 codex exec resume \
  -m gpt-6.1-sol -c model_reasoning_effort="high" \
  -c sandbox_mode="read-only" --skip-git-repo-check \
  --json -o "$T/last2.txt" "$ID" - < "$T/p2.txt" > "$T/events2.jsonl" 2> "$T/err2.txt"
```

Verified: the resumed turn kept the earlier context and reported the same `thread_id`.
`codex exec resume` accepts `-m`, `-c`, `-i`, `--json`, `-o`, `--skip-git-repo-check`,
`--ephemeral`, `--output-schema`, `--last`, `--all`; it **rejects `-s` and `-C`**
(`unexpected argument`). Do **not** rely on the original sandbox being inherited: restate it with
`-c sandbox_mode="<mode>"` on every resume (verified: `read-only` was enforced and a write was
denied). Use `--last` instead of an id only when you are sure no other Codex session ran in that
directory. Resuming from a different cwd than the original run is **(unverified)**.
`codex exec fork <SESSION_ID>` branches a session into a new one **(unverified)**.

### Native review (verified)

For "review my diff" the CLI has a built-in reviewer:

```bash
cd "<abs repo path>"
PYTHONUTF8=1 codex exec review --uncommitted \
  -m gpt-6.1-sol -c model_reasoning_effort="high" \
  --json -o "$T/last.txt" > "$T/events.jsonl" 2> "$T/err.txt"
# other targets: --base <branch>   |   --commit <sha> [--title "<text>"]
```

- Targets: `--uncommitted` (staged + unstaged + untracked), `--base <branch>`, `--commit <sha>`.
- Verified: **a target flag cannot be combined with a `[PROMPT]`** (`--uncommitted`, `--base`,
  `--commit` each error with "cannot be used with `[PROMPT]`"). So the native path takes no
  custom instructions.
- `codex exec review` has no `-s` and no `-C`; run it from inside the repo. It returns
  severity-tagged findings (`[P1] ...` with file and line) in the `-o` file.
- When you need a custom focus (auth only, migration safety, "findings only, ≤10 lines") use a
  normal `codex exec -s read-only` call with a review prompt instead (see Examples).

## Model routing — automatic, small, opinionated

Do not ask the user to choose a model unless they want to. Pick from [MODELS.md](MODELS.md) and
never invent slugs or efforts. Hidden models (`gpt-reserve`, `codex-auto-review`) are never used.

| Situation | Model / effort |
|---|---|
| **Default** — review, plan critique/approval, debugging, implementation, architecture, security | `gpt-6.1-sol` / `high` |
| Well-scoped refactor or implementation where cost matters; routine review | `gpt-6.1-terra` / `high` |
| Quick consult, easy or mechanical task | `gpt-6-luna` / `high` |
| Hardest work: still inconclusive after Sol/high (and `xhigh`), unusually difficult end to end, or the user asks for the strongest model | `gpt-6-astra` / `medium` |

- Prefer raising effort on the current model (`high` → `xhigh` → `max`) before spending Astra.
  `ultra` exists on every model except Luna; use it only when asked.
- `gpt-6-sol` (previous generation) only if a 6.1 model is unavailable on the seat;
  `gpt-5.6-*` (legacy) only if the user explicitly asks for one.
- If a model is unavailable on the seat, say so plainly; do not silently substitute another.
- Tell the user the selected model in one short line only when useful.

## Proactively offering Codex

Offer a Codex second opinion on:

- architecture/design with lasting consequences,
- irreversible or high-blast-radius changes,
- a stubborn bug without a confirmed root cause,
- a genuine fork between strong approaches,
- security-critical changes.

Offer once, as a one-line offer naming the pre-selected model, then wait for consent. **Never
silently spend the user's Codex allowance.**

## Methods

| Method | When | `-s` | Return contract |
|---|---|---|---|
| **review** | second pair of eyes on a diff | `read-only` (or `codex exec review`) | findings only, ranked by severity |
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

1. Pass **`-C` + paths** in the prompt, not file contents, whenever Codex can read the repo itself.
2. Keep returned output bounded (return contract); read only `-o` files, never raw JSONL.
3. Review/plan/consult stay `read-only`.
4. One-shot work calls `codex exec` directly from the main thread.
5. **Multi-turn work stays supported**: use the `codex-teammate` subagent for
   implement → self-review → fix, iterative plan refinement, or deep review follow-ups.

## Multi-turn escalation

Keep the same model for a conversation. A good loop is:

- start with the routed model and `--json` to capture `thread_id`,
- ask one focused follow-up with `codex exec resume "$ID" -`,
- if the result is still uncertain, start a **fresh** `codex exec` on the next route
  (Sol → Astra, or a higher effort) with a concise summary of the unresolved question.

Do not bounce models every turn.

## Raw vs summarized context

Default to a tight instruction and repo paths. When correctness depends on exact material
(error text, spec language, a small critical diff), pass it verbatim in the prompt file. User
instructions such as "do not summarize" take precedence.

## Sandbox boundary

`read-only` for review/plan/consult. `workspace-write` only when edits are required.
Never use `danger-full-access`, `--dangerously-bypass-approvals-and-sandbox`, or `--approve-for-me`
unless the user explicitly requests it and understands the risk. Because `resume` has no `-s`,
pass `-c sandbox_mode="<mode>"` there (see above).

## Examples

All examples assume `T=$(mktemp -d)` and the start-a-task command above; only the prompt file and
the `-m` / `-s` values differ.

**Review current diff, native (default route)**
```bash
cd "<abs repo path>" && codex exec review --uncommitted \
  -m gpt-6.1-sol -c model_reasoning_effort="high" -o "$T/last.txt" > "$T/events.jsonl" 2> "$T/err.txt"
```

**Review with a custom focus — prompt file `p.txt`, `-s read-only`, `gpt-6.1-sol`/`high`**
```
Act as a code reviewer. Review the uncommitted diff in this repo (run git diff and git status).
Focus on correctness, regressions, security and missing tests.
Return only severity-ranked findings with file/line references.
```

**Critique / approve a plan — `-s read-only`, `gpt-6.1-sol`/`high`**
```
Act as a skeptical senior engineer. Critique the plan below against this repo.
Identify blockers, missed edge cases and unsafe assumptions. If it is sound,
say APPROVE and list only residual risks. Keep the answer under 12 lines.
<PLAN>...</PLAN>
```

**Implement a scoped change — `-s workspace-write`, `gpt-6.1-terra`/`high`**
```
Act as the implementer. In this repo, <task>. Constraints: <compat/security>.
Done when <test or behaviour>. Return the changed files and a summary of at most 5 lines.
```

**Quick consult — `-s read-only`, `gpt-6-luna`/`high`**
```
Is approach A or B safer for <situation>? Answer in at most 8 lines.
```

## Relationship to codex-teammate

Keep **`codex-teammate`** for multi-turn Codex loops. It must apply this same routing policy
and these same `codex exec` / `codex exec resume` templates rather than requiring the caller to
choose a model every time. One-shot review/plan requests should remain direct to avoid unnecessary
subagent overhead.
