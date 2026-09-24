# Codex models reference

> **Generated file — do not hand-edit.** Regenerate with `python scripts/sync-models.py`.
> Source: `$CODEX_HOME/models_cache.json` · fetched `2026-09-24T10:24:00.059288900Z` · Codex CLI `0.155.0`.

ask-codex intentionally exposes only its approved GPT-6 routing set.
Pass the slug as `model`, and reasoning effort as `config={"model_reasoning_effort": "<effort>"}`.

## Allowed models

| slug | use it for | routing default | supported efforts |
|---|---|---|---|
| `gpt-6-luna` | Default: code review, plan critique/approval, focused debugging, well-scoped coding | `high` | `low`, `medium`, `high`, `xhigh`, `max` |
| `gpt-6-sol` | Architecture, security, migrations, subtle cross-cutting bugs, whole-repo/high-blast-radius analysis | `high` | `low`, `medium`, `high`, `xhigh`, `max`, `ultra` |
| `gpt-6-astra` | Exceptional escalation for the hardest end-to-end or unresolved tasks | `medium` | `low`, `medium`, `high`, `xhigh`, `max`, `ultra` |

## Routing policy

1. Start with **`gpt-6-luna/high`** for normal review and plan validation.
2. Use **`gpt-6-sol/high`** for architecture/security/migrations/broad cross-cutting reasoning.
3. Use **`gpt-6-astra/medium`** only for exceptional escalation.
4. Prefer `high` → `xhigh` before casually escalating to Astra.
5. Do **not** use GPT-5.x, Terra, or legacy aliases.
6. If an approved model is unavailable, report that plainly; do not silently substitute a legacy model.
