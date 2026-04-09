#!/usr/bin/env python3
"""
dev_tools/scripts/prompt_patch.py

Patches the NL2SQL and RAG system prompt files to reflect the post-migration schema.

Specifically:
  - agentic_system/agents_core/nl2sql/prompts/system.md
  - agentic_system/agents_core/rag/prompts/system.md

Replaces field references so the agents use `merged_at IS NOT NULL` instead of
`merged = 1`, and updates type annotations from `UInt8` to `Nullable(DateTime)`.

Returns a list of PromptChange records describing every file modified.

Used by schema_sync.py as Step 4.
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

AGENTS_DIR = Path(__file__).resolve().parents[2] / "agentic_system" / "agents_core"

# Prompt files to patch
PROMPT_FILES: list[Path] = [
    AGENTS_DIR / "nl2sql" / "prompts" / "system.md",
    AGENTS_DIR / "rag" / "prompts" / "system.md",
]

# Ordered text replacements applied to each prompt file.
# Using regex for precise, context-aware matching.
_REPLACEMENTS: list[tuple[str, str]] = [
    # Schema table: merged UInt8 row
    (
        r"\|\s*merged\s*\|\s*UInt8\s*\|([^\n]*)\|",
        "| merged_at | Nullable(DateTime) | Post-migration. NULL = not merged; non-NULL = merged timestamp. Replaces `merged UInt8`. |",
    ),
    # Inline type annotation in prose
    (r"\bmerged\s+UInt8\b", "merged_at Nullable(DateTime)"),
    # SQL predicate: merged = 1
    (r"\bmerged\s*=\s*1\b", "merged_at IS NOT NULL"),
    # SQL predicate: merged = 0
    (r"\bmerged\s*=\s*0\b", "merged_at IS NULL"),
    # sum(merged) aggregate pattern
    (r"\bsum\(merged\)", "countIf(isNotNull(merged_at))"),
    # Use merged = 1 instructions
    (
        r"Use `merged = 1` for merged PRs and `merged = 0` for unmerged \(pre-migration\)\.",
        (
            "Use `merged_at IS NOT NULL` for merged PRs and `merged_at IS NULL` for unmerged "
            "(post-migration field; `merged = 1` returns 0 rows after migration)."
        ),
    ),
    # Inline backtick SQL references
    (r"`merged = 1`", "`merged_at IS NOT NULL`"),
    (r"`merged = 0`", "`merged_at IS NULL`"),
    # Description lines mentioning the old flag
    (
        r"\*\*1\*\* if the PR was merged, \*\*0\*\* if closed without merging\. Subject of the migration in this dataset\.",
        "**non-NULL** (timestamp) if the PR was merged, **NULL** if closed without merging. Post-migration field.",
    ),
    # "pre-migration state" label in schema comment
    (r"\(pre-migration state\)", "(post-migration state)"),
    (r"\(pre-migration\)", "(post-migration)"),
]


@dataclass
class PromptChange:
    file: str
    replacements_applied: int

    def __str__(self) -> str:
        return f"prompt:patched:{self.file} ({self.replacements_applied} replacement(s))"


def _apply_replacements(text: str) -> tuple[str, int]:
    count = 0
    for pattern, replacement in _REPLACEMENTS:
        new_text, n = re.subn(pattern, replacement, text)
        count += n
        text = new_text
    return text, count


def patch(dry_run: bool = False) -> list[PromptChange]:
    """
    Patch all prompt files. Returns list of PromptChange for files that changed.
    """
    changes: list[PromptChange] = []

    for path in PROMPT_FILES:
        if not path.exists():
            continue

        original = path.read_text(encoding="utf-8")
        patched, n = _apply_replacements(original)

        if n == 0:
            continue

        changes.append(PromptChange(str(path.relative_to(Path(__file__).resolve().parents[2])), n))

        if not dry_run:
            path.write_text(patched, encoding="utf-8")

    return changes


# ── CLI ────────────────────────────────────────────────────────────────────────

def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Patch NL2SQL and RAG prompts for post-migration schema"
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    tag = "[DRY RUN] " if args.dry_run else ""
    print(f"{tag}==> Prompt Patch")
    print()

    changes = patch(dry_run=args.dry_run)

    if not changes:
        print("  No changes — prompts already reflect post-migration schema.")
        return 0

    for c in changes:
        print(f"  {c}")

    action = "would be " if args.dry_run else ""
    print(f"\n  {len(changes)} file(s) {action}patched.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
