#!/usr/bin/env python3
"""Regenerate MODELS.md from the Codex CLI's own model cache.

The Codex CLI stores the list of models available on your seat in
``$CODEX_HOME/models_cache.json`` (default ``~/.codex/models_cache.json``).
That file is the ground truth: it carries every model slug, its default
reasoning level, and the exact set of reasoning efforts each model supports.

This script reads that cache and rewrites ``skills/ask-codex/MODELS.md`` so the
ask-codex skill never offers a model that does not exist or an effort a model
does not support. It only lists user-facing models (``visibility == "list"``
and ``supported_in_api == true``); internal routing aliases and review models
are excluded.

Usage:
    python scripts/sync-models.py            # write MODELS.md
    python scripts/sync-models.py --check     # exit 1 if MODELS.md is stale
    python scripts/sync-models.py --cache PATH

If the cache is not present (e.g. the repo is checked out on a machine without
Codex), the committed MODELS.md is left untouched and the script exits 0 with a
notice. The committed file is the shipped fallback.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MODELS_MD = REPO_ROOT / "skills" / "ask-codex" / "MODELS.md"

# Editorial guidance keyed by slug. Facts come from the cache; this only adds a
# human "recommended for" hint. Unknown slugs still render (with a blank hint),
# so a new model never silently disappears.
RECOMMENDED_FOR = {
    "gpt-5.6-sol": "Hardest coding, architecture, deep debugging, whole-repo analysis",
    "gpt-5.6-terra": "Everyday coding; balanced quality / speed / cost",
    "gpt-5.6-luna": "Fast, repetitive, well-defined, high-volume work",
    "gpt-5.5": "Previous-gen frontier: complex coding, research, real-world work",
    "gpt-5.4": "Economical general coding",
    "gpt-5.4-mini": "Small, fast, cost-efficient simple tasks + subagent work",
}


def default_cache_path() -> Path:
    codex_home = os.environ.get("CODEX_HOME")
    base = Path(codex_home) if codex_home else Path.home() / ".codex"
    return base / "models_cache.json"


def substantive(md: str) -> str:
    """Content used for staleness comparison, ignoring the volatile provenance line.

    The generated file embeds `fetched_at` in a `> Source:` line that changes every time
    the Codex cache refreshes, even when the model set is identical. `--check` should flag
    real drift (models / efforts changing), not a cache-timestamp bump, so drop that line.
    """
    return "\n".join(
        ln for ln in md.splitlines() if not ln.startswith("> Source:")
    ).strip()


def load_cache(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def visible_models(cache: dict) -> list[dict]:
    out = []
    for m in cache.get("models", []):
        if m.get("visibility") != "list":
            continue
        if not m.get("supported_in_api", False):
            continue
        out.append(m)
    out.sort(key=lambda m: m.get("priority", 999))
    return out


def render(cache: dict) -> str:
    models = visible_models(cache)
    fetched = cache.get("fetched_at", "unknown")
    client = cache.get("client_version", "unknown")

    lines: list[str] = []
    lines.append("# Codex models reference")
    lines.append("")
    lines.append(
        "> **Generated file — do not hand-edit.** Regenerate with "
        "`python scripts/sync-models.py`."
    )
    lines.append(f"> Source: `$CODEX_HOME/models_cache.json` · fetched `{fetched}` · Codex CLI `{client}`.")
    lines.append("")
    lines.append(
        "In a `mcp__codex__codex` / `codex-reply` call: pass the slug as `model`, "
        "and the reasoning effort as `config={\"model_reasoning_effort\": \"<effort>\"}`."
    )
    lines.append("")
    lines.append("## Available models")
    lines.append("")
    lines.append("| slug | recommended for | default effort | supported efforts |")
    lines.append("|---|---|---|---|")
    for m in models:
        slug = m["slug"]
        efforts = [e["effort"] for e in m.get("supported_reasoning_levels", [])]
        rec = RECOMMENDED_FOR.get(slug, m.get("description", "").rstrip("."))
        lines.append(
            f"| `{slug}` | {rec} | `{m.get('default_reasoning_level', '?')}` | "
            f"{', '.join('`' + e + '`' for e in efforts)} |"
        )
    lines.append("")
    lines.append("## Presets")
    lines.append("")
    lines.append("| preset | model | effort |")
    lines.append("|---|---|---|")
    lines.append("| **strongest** | `gpt-5.6-sol` | `high` |")
    lines.append("| **maximum_depth** | `gpt-5.6-sol` | `max` |")
    lines.append("| **balanced** | `gpt-5.6-terra` | `medium` |")
    lines.append("| **fast_and_cheap** | `gpt-5.6-luna` | `medium` |")
    lines.append("")
    lines.append("## Rules")
    lines.append("")
    lines.append(
        "- Never pass an effort a model does not list above — the call fails."
    )
    lines.append(
        "- Only the slugs in the table exist on this seat. Do not invent slugs "
        "(no `-codex-spark`, no `-preview`, etc.)."
    )
    lines.append(
        "- If a model you expect is missing, the seat changed — rerun "
        "`sync-models.py` to refresh."
    )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cache", type=Path, default=None, help="Path to models_cache.json")
    ap.add_argument("--check", action="store_true", help="Exit 1 if MODELS.md is stale")
    args = ap.parse_args()

    cache_path = args.cache or default_cache_path()
    if not cache_path.exists():
        print(
            f"[sync-models] cache not found at {cache_path}; "
            "keeping committed MODELS.md as-is."
        )
        return 0

    cache = load_cache(cache_path)
    new_content = render(cache)

    if args.check:
        current = MODELS_MD.read_text(encoding="utf-8") if MODELS_MD.exists() else ""
        if substantive(current) != substantive(new_content):
            print("[sync-models] MODELS.md is stale — run `python scripts/sync-models.py`.")
            return 1
        print("[sync-models] MODELS.md is up to date.")
        return 0

    MODELS_MD.parent.mkdir(parents=True, exist_ok=True)
    MODELS_MD.write_text(new_content, encoding="utf-8")
    n = len(visible_models(cache))
    print(f"[sync-models] wrote {MODELS_MD.relative_to(REPO_ROOT)} ({n} models).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
