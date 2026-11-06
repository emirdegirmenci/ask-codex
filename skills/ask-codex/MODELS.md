# Codex models reference

> **Generated file — do not hand-edit.** Regenerate with `python scripts/sync-models.py`.
> Source: `$CODEX_HOME/models_cache.json` · fetched `2026-11-06T07:09:11.106836400Z` · Codex CLI `0.164.0`.

ask-codex exposes only the user-facing models in its allowlist (hidden models are never used).
Pass the slug with `-m <slug>` and the effort with `-c 'model_reasoning_effort="<effort>"'` (a TOML value: single quotes around the whole argument).

## Allowed models

| slug | status | use it for | routing default | supported efforts |
|---|---|---|---|---|
| `gpt-6.1-sol` | current | Default workhorse: code review, plan critique/approval, debugging, implementation, architecture/security | `high` | `low`, `medium`, `high`, `xhigh`, `max`, `ultra` |
| `gpt-6.1-terra` | current | Balanced: well-scoped refactors and implementations, routine review where cost matters | `high` | `low`, `medium`, `high`, `xhigh`, `max`, `ultra` |
| `gpt-6-astra` | current | Frontier: the hardest, most demanding or still-unresolved work (escalation) | `medium` | `low`, `medium`, `high`, `xhigh`, `max`, `ultra` |
| `gpt-6-luna` | current | Fast and cheap: quick consults, easy or mechanical tasks | `high` | `low`, `medium`, `high`, `xhigh`, `max` |
| `gpt-6-sol` | previous gen | Previous-generation workhorse; only if a 6.1 model is unavailable on the seat | `high` | `low`, `medium`, `high`, `xhigh`, `max`, `ultra` |
| `gpt-5.6-sol` | legacy | Legacy; only on explicit user request | `high` | `low`, `medium`, `high`, `xhigh`, `max`, `ultra` |
| `gpt-5.6-terra` | legacy | Legacy; only on explicit user request | `high` | `low`, `medium`, `high`, `xhigh`, `max`, `ultra` |
| `gpt-5.6-luna` | legacy | Legacy; only on explicit user request | `high` | `low`, `medium`, `high`, `xhigh`, `max` |

## Routing policy

1. Start with **`gpt-6.1-sol/high`** for review, plan critique, debugging and implementation.
2. Use **`gpt-6.1-terra/high`** for well-scoped refactors/implementations where a balanced model is enough.
3. Use **`gpt-6-luna/high`** for quick, cheap consults and easy mechanical tasks.
4. Use **`gpt-6-astra/medium`** only for the hardest or still-unresolved work; try `xhigh` on the current model first.
5. `gpt-6-sol` (previous gen) only when a 6.1 model is unavailable on the seat; `gpt-5.6-*` (legacy) only on explicit user request.
6. If a model is unavailable on this seat, report that plainly; do not silently substitute another one.
