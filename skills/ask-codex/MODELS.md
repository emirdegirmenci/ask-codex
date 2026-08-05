# Codex models reference

> **Generated file — do not hand-edit.** Regenerate with `python scripts/sync-models.py`.
> Source: `$CODEX_HOME/models_cache.json` · fetched `2026-08-05T06:23:54.147234200Z` · Codex CLI `0.146.0`.

In a `mcp__codex__codex` / `codex-reply` call: pass the slug as `model`, and the reasoning effort as `config={"model_reasoning_effort": "<effort>"}`.

## Available models

| slug | recommended for | default effort | supported efforts |
|---|---|---|---|
| `gpt-5.6-sol` | Hardest coding, architecture, deep debugging, whole-repo analysis | `medium` | `low`, `medium`, `high`, `xhigh`, `max`, `ultra` |
| `gpt-5.6-terra` | Everyday coding; balanced quality / speed / cost | `medium` | `low`, `medium`, `high`, `xhigh`, `max`, `ultra` |
| `gpt-5.6-luna` | Fast, repetitive, well-defined, high-volume work | `medium` | `low`, `medium`, `high`, `xhigh`, `max` |
| `gpt-5.5` | Previous-gen frontier: complex coding, research, real-world work | `xhigh` | `low`, `medium`, `high`, `xhigh` |
| `gpt-5.4` | Economical general coding | `medium` | `low`, `medium`, `high`, `xhigh` |
| `gpt-5.4-mini` | Small, fast, cost-efficient simple tasks + subagent work | `medium` | `low`, `medium`, `high`, `xhigh` |

## Presets

| preset | model | effort |
|---|---|---|
| **strongest** | `gpt-5.6-sol` | `high` |
| **maximum_depth** | `gpt-5.6-sol` | `max` |
| **balanced** | `gpt-5.6-terra` | `medium` |
| **fast_and_cheap** | `gpt-5.6-luna` | `medium` |

## Rules

- Never pass an effort a model does not list above — the call fails.
- Only the slugs in the table exist on this seat. Do not invent slugs (no `-codex-spark`, no `-preview`, etc.).
- If a model you expect is missing, the seat changed — rerun `sync-models.py` to refresh.
