#!/usr/bin/env python3
"""Regenerate MODELS.md from the Codex CLI model cache.

The local Codex cache is the source of truth for availability and supported
reasoning efforts. Only user-facing models (visibility == "list" and
supported_in_api) are rendered; hidden models (e.g. gpt-reserve,
codex-auto-review) are never exposed. ALLOWED_MODELS is an explicit allowlist
so a cache refresh cannot silently reintroduce a model nobody reviewed; when
OpenAI ships a new slug, add it here (and to RECOMMENDED_FOR / STATUS).
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MODELS_MD = REPO_ROOT / "skills" / "ask-codex" / "MODELS.md"

# Order = display order (current generation first, legacy last).
ALLOWED_MODELS = (
    "gpt-6.1-sol",
    "gpt-6.1-terra",
    "gpt-6-astra",
    "gpt-6-luna",
    "gpt-6-sol",
    "gpt-5.6-sol",
    "gpt-5.6-terra",
    "gpt-5.6-luna",
)

# current = routed by default; legacy = only on explicit user request.
STATUS = {
    "gpt-6.1-sol": "current",
    "gpt-6.1-terra": "current",
    "gpt-6-astra": "current",
    "gpt-6-luna": "current",
    "gpt-6-sol": "previous gen",
    "gpt-5.6-sol": "legacy",
    "gpt-5.6-terra": "legacy",
    "gpt-5.6-luna": "legacy",
}

RECOMMENDED_FOR = {
    "gpt-6.1-sol": "Default workhorse: code review, plan critique/approval, debugging, implementation, architecture/security",
    "gpt-6.1-terra": "Balanced: well-scoped refactors and implementations, routine review where cost matters",
    "gpt-6-astra": "Frontier: the hardest, most demanding or still-unresolved work (escalation)",
    "gpt-6-luna": "Fast and cheap: quick consults, easy or mechanical tasks",
    "gpt-6-sol": "Previous-generation workhorse; only if a 6.1 model is unavailable on the seat",
    "gpt-5.6-sol": "Legacy; only on explicit user request",
    "gpt-5.6-terra": "Legacy; only on explicit user request",
    "gpt-5.6-luna": "Legacy; only on explicit user request",
}

ROUTING_EFFORT = {
    "gpt-6.1-sol": "high",
    "gpt-6.1-terra": "high",
    "gpt-6-astra": "medium",
    "gpt-6-luna": "high",
    "gpt-6-sol": "high",
    "gpt-5.6-sol": "high",
    "gpt-5.6-terra": "high",
    "gpt-5.6-luna": "high",
}

def default_cache_path() -> Path:
    codex_home = os.environ.get("CODEX_HOME")
    base = Path(codex_home) if codex_home else Path.home() / ".codex"
    return base / "models_cache.json"

def substantive(md: str) -> str:
    return "\n".join(line for line in md.splitlines() if not line.startswith("> Source:")).strip()

def load_cache(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)

def approved_models(cache: dict) -> list[dict]:
    by_slug = {
        m.get("slug"): m
        for m in cache.get("models", [])
        if m.get("visibility") == "list" and m.get("supported_in_api", False)
    }
    return [by_slug[slug] for slug in ALLOWED_MODELS if slug in by_slug]

def render(cache: dict) -> str:
    models = approved_models(cache)
    fetched = cache.get("fetched_at", "unknown")
    client = cache.get("client_version", "unknown")

    lines: list[str] = [
        "# Codex models reference",
        "",
        "> **Generated file — do not hand-edit.** Regenerate with `python scripts/sync-models.py`.",
        f"> Source: `$CODEX_HOME/models_cache.json` · fetched `{fetched}` · Codex CLI `{client}`.",
        "",
        "ask-codex exposes only the user-facing models in its allowlist (hidden models are never used).",
        "Pass the slug with `-m <slug>` and the effort with `-c 'model_reasoning_effort=\"<effort>\"'` (a TOML value: single quotes around the whole argument).",
        "",
        "## Allowed models",
        "",
        "| slug | status | use it for | routing default | supported efforts |",
        "|---|---|---|---|---|",
    ]

    present = set()
    for m in models:
        slug = m["slug"]
        present.add(slug)
        efforts = [e["effort"] for e in m.get("supported_reasoning_levels", [])]
        lines.append(
            f"| `{slug}` | {STATUS[slug]} | {RECOMMENDED_FOR[slug]} | `{ROUTING_EFFORT[slug]}` | "
            f"{', '.join('`' + e + '`' for e in efforts)} |"
        )

    missing = [slug for slug in ALLOWED_MODELS if slug not in present]
    if missing:
        lines.extend(["", "## Unavailable on this seat", "",
                      "The following approved models were not present in the local Codex cache:", "",
                      *[f"- `{slug}`" for slug in missing]])

    lines.extend([
        "",
        "## Routing policy",
        "",
        "1. Start with **`gpt-6.1-sol/high`** for review, plan critique, debugging and implementation.",
        "2. Use **`gpt-6.1-terra/high`** for well-scoped refactors/implementations where a balanced model is enough.",
        "3. Use **`gpt-6-luna/high`** for quick, cheap consults and easy mechanical tasks.",
        "4. Use **`gpt-6-astra/medium`** only for the hardest or still-unresolved work; try `xhigh` on the current model first.",
        "5. `gpt-6-sol` (previous gen) only when a 6.1 model is unavailable on the seat; `gpt-5.6-*` (legacy) only on explicit user request.",
        "6. If a model is unavailable on this seat, report that plainly; do not silently substitute another one.",
        "",
    ])
    return "\n".join(lines)

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cache", type=Path, default=None)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    cache_path = args.cache or default_cache_path()
    if not cache_path.exists():
        print(f"[sync-models] cache not found at {cache_path}; keeping committed MODELS.md as-is.")
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
    print(f"[sync-models] wrote {MODELS_MD.relative_to(REPO_ROOT)} ({len(approved_models(cache))}/{len(ALLOWED_MODELS)} approved models available).")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
