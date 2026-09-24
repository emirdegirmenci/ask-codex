# Codex models reference

> Routing policy for ask-codex. The plugin intentionally uses only the current GPT-6 Codex family.

Pass the slug as `model`, and reasoning effort as
`config={"model_reasoning_effort": "<effort>"}`.

## Allowed models

| slug | use it for | routing default | supported efforts |
|---|---|---|---|
| `gpt-6-luna` | **Default.** Code review, plan critique/approval, focused debugging, well-scoped coding | `high` | `none`, `low`, `medium`, `high`, `xhigh`, `max` |
| `gpt-6-sol` | Architecture, security, subtle cross-cutting bugs, migrations, whole-repo/high-blast-radius analysis | `high` | `none`, `low`, `medium`, `high`, `xhigh`, `max` |
| `gpt-6-astra` | Exceptional escalation when Sol/high is insufficient or the task is unusually hard/end-to-end | `medium` | `low`, `medium`, `high`, `xhigh`, `max` |

## Routing policy

1. Start with **`gpt-6-luna/high`** for normal review and plan validation.
2. Use **`gpt-6-sol/high`** when correctness risk is high or reasoning spans architecture/security/many components.
3. Use **`gpt-6-astra/medium`** only for the hardest cases, or after a Sol pass is still inconclusive.
4. Raise effort before raising model when sensible: `high` → `xhigh`; reserve `max` for exceptional cases.
5. Do **not** use GPT-5.x, Terra, or legacy aliases in this plugin.
6. If an allowed model is unavailable on the user's seat, report it plainly instead of silently substituting a legacy model.
