# ask-codex — design

Date: 2026-08-05

## Problem

The original `ask-codex` skill lived only in `~/.claude/` and carried a hand-typed model
reference (`MODELS.md`) that had drifted from reality: it listed a model that does not exist
(`gpt-5.3-codex-spark`), claimed efforts models don't support (e.g. `none` for `gpt-5.5`,
`max` for `gpt-5.4`), and omitted real ones (`ultra` for `gpt-5.6-sol`/`terra`, `xhigh` for
`gpt-5.4-mini`). That is why Claude sometimes suggested nonsensical model/effort combinations.
The skill was also not shareable, and it only acted when explicitly asked.

## Goals

1. **Accurate model + effort data**, generated from ground truth, that can't silently drift.
2. **A shareable, installable Claude Code plugin** published to GitHub as a marketplace.
3. **Proactive (but consented) delegation**: Claude offers Codex on high-stakes decisions
   without being asked — and never calls Codex silently.

## Ground truth for models

The Codex CLI caches the models available on the user's seat in
`$CODEX_HOME/models_cache.json`. Each entry carries `slug`, `visibility`,
`supported_in_api`, `default_reasoning_level`, and the exact `supported_reasoning_levels`.
`scripts/sync-models.py` reads that cache and rewrites `skills/ask-codex/MODELS.md`, keeping
only user-facing models (`visibility == "list"` and `supported_in_api == true`). The committed
`MODELS.md` is the shipped fallback for machines without a Codex cache. The script is a
maintainer tool (`--check` mode makes it CI-friendly); it never fails the build when the cache
is absent.

## Architecture

```
ask-codex/                          (public GitHub repo = single-plugin marketplace)
├── .claude-plugin/
│   ├── plugin.json                 name, version, keywords, skill/agent paths
│   └── marketplace.json            marketplace listing this one plugin (source ./)
├── skills/ask-codex/
│   ├── SKILL.md                    when/how to delegate; proactive-offer rules; prompt recipe
│   └── MODELS.md                   GENERATED from the Codex cache — source of truth for slugs
├── agents/
│   └── codex-teammate.md           multi-turn Codex loop, isolated context, returns outcome only
├── scripts/
│   └── sync-models.py              cache → MODELS.md generator (+ --check)
├── docs/DESIGN.md                  this file
├── README.md                       install, usage, discoverability (badges, topics)
└── LICENSE                         MIT
```

## Behavior: proactive offer, never silent call

The skill adds a "proactively offering Codex" section. On architecture decisions, irreversible /
high-blast-radius changes, stubborn deep-debugging, a genuine fork between strong approaches, or
security-critical diffs, Claude surfaces a **one-line offer** with a pre-picked model + effort and
waits for a yes. It does not spend the user's Codex seat without consent, and it does not offer on
trivial work. This preserves the standing rule: *ask before calling; the user decides.*

## Prompt quality

SKILL.md defines a four-part prompt recipe — role + method, concrete target (paths, not pasted
files), definition of done, and a return contract — plus worked examples for review / plan /
refactor. The return contract is called out as the single biggest quality + token lever.

## Distribution

The repo doubles as its own marketplace (`source: "./"`). Users run
`/plugin marketplace add emirdegirmenci/ask-codex` then `/plugin install ask-codex@ask-codex`.
A `v1.0.0` git tag + GitHub release is published for version tracking and discoverability, though
a tag is not required for marketplace installation.

## Non-goals

- No third-party bridge; Codex runs on the user's own seat via `codex mcp-server`.
- No silent/auto invocation of Codex.
- No editing of the user's other repositories.
