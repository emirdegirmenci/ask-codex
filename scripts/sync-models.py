#!/usr/bin/env python3
"""Regenerate MODELS.md from the Codex CLI model cache.

ask-codex intentionally exposes only its approved GPT-6 routing set. The local
Codex cache remains the source of truth for availability and supported
reasoning efforts, but legacy/user-visible models outside the allowlist are not
reintroduced into MODELS.md.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MODELS_MD = REPO_ROOT / "skills" / "ask-codex" / "MODELS.md"

ALLOWED_MODELS = (
    "gpt-6-luna",
    "gpt-6-sol",
    "gpt-6-astra",
)

RECOMMENDED_FOR = {
    "gpt-6-luna": "Default: code review, plan critique/approval, focused debugging, well-scoped coding",
    "gpt-6-sol": "Architecture, security, migrations, subtle cross-cutting bugs, whole-repo/high-blast-radius analysis",
    "gpt-6-astra": "Exceptional escalation for the hardest end-to-end or unresolved tasks",
}

ROUTING_EFFORT = {
    "gpt-6-luna": "high",
    "gpt-6-sol": "high",
    "gpt-6-astra": "medium",
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
        "ask-codex intentionally exposes only its approved GPT-6 routing set.",
        "Pass the slug as `model`, and reasoning effort as `config={\"model_reasoning_effort\": \"<effort>\"}`.",
        "",
        "## Allowed models",
        "",
        "| slug | use it for | routing default | supported efforts |",
        "|---|---|---|---|",
    ]

    present = set()
    for m in models:
        slug = m["slug"]
        present.add(slug)
        efforts = [e["effort"] for e in m.get("supported_reasoning_levels", [])]
        lines.append(
            f"| `{slug}` | {RECOMMENDED_FOR[slug]} | `{ROUTING_EFFORT[slug]}` | "
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
        "1. Start with **`gpt-6-luna/high`** for normal review and plan validation.",
        "2. Use **`gpt-6-sol/high`** for architecture/security/migrations/broad cross-cutting reasoning.",
        "3. Use **`gpt-6-astra/medium`** only for exceptional escalation.",
        "4. Prefer `high` → `xhigh` before casually escalating to Astra.",
        "5. Do **not** use GPT-5.x, Terra, or legacy aliases.",
        "6. If an approved model is unavailable, report that plainly; do not silently substitute a legacy model.",
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
