#!/usr/bin/env python3
"""
dev_tools/schema_sync.py

Act 3 developer tool — fully automated schema-sync procedure.

Detects drift between the live ClickHouse schema and every layer of the agentic
system (YAML contract, ChromaDB RAG chunks, NL2SQL + RAG prompts), then patches
all four layers in one pass and prints a SchemaSyncReport.

Usage:
    python dev_tools/schema_sync.py --table github_events
    python dev_tools/schema_sync.py --table github_events --dry-run
    python dev_tools/schema_sync.py --table github_events --rollback

Steps:
    1. Introspect live ClickHouse schema
    2. Patch YAML contract (agentic_system/schema/<table>.yaml)
    3. Patch stale ChromaDB chunks (re-embed + upsert)
    4. Patch NL2SQL + RAG system prompts

Flags:
    --dry-run   Show what would change, touch nothing.
    --rollback  Reverse the most recent sync using the saved rollback state.
                Requires a prior successful (non-dry-run) sync.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

ROLLBACK_STATE_FILE = Path(__file__).resolve().parent / ".schema_sync_rollback.json"


# ── Rollback helpers ───────────────────────────────────────────────────────────

def _save_rollback_state(table: str, state: dict) -> None:
    with ROLLBACK_STATE_FILE.open("w") as f:
        json.dump({"table": table, "saved_at": datetime.utcnow().isoformat(), **state}, f, indent=2)


def _load_rollback_state() -> dict:
    if not ROLLBACK_STATE_FILE.exists():
        raise FileNotFoundError(
            "No rollback state found. Run schema_sync without --rollback first."
        )
    with ROLLBACK_STATE_FILE.open() as f:
        return json.load(f)


def _do_rollback(table: str) -> None:
    """Reverse a previous schema_sync by restoring saved snapshots."""
    import yaml as _yaml

    state = _load_rollback_state()
    print(f"==> Rolling back schema-sync (saved {state.get('saved_at', '?')})")
    print()

    # 1. Restore YAML contract
    yaml_snapshot = state.get("yaml_snapshot")
    if yaml_snapshot:
        schema_path = Path(__file__).resolve().parents[1] / "agentic_system" / "schema" / f"{table}.yaml"
        with schema_path.open("w") as f:
            _yaml.dump(yaml_snapshot, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        print(f"  ✓ YAML contract restored: {schema_path.name}")
    else:
        print("  – YAML snapshot not found in rollback state, skipping")

    # 2. Restore prompt files
    prompt_snapshots: dict[str, str] = state.get("prompt_snapshots", {})
    if prompt_snapshots:
        for rel_path, content in prompt_snapshots.items():
            p = Path(__file__).resolve().parents[1] / rel_path
            p.write_text(content, encoding="utf-8")
            print(f"  ✓ Prompt restored: {rel_path}")
    else:
        print("  – No prompt snapshots found, skipping")

    # 3. Restore ChromaDB chunk content + clear stale flag
    # Re-seed from the original source files (the ground truth for pre-migration state)
    print()
    print("  ChromaDB: to fully restore, run: make seed-vectors")
    print("  (Re-seeds from source files, which contain the pre-migration schema text)")

    print()
    print("Rollback complete.")
    print("  YAML contract and prompts restored to pre-sync state.")
    print("  Run 'make seed-vectors' to restore ChromaDB chunks.")


# ── Main sync ──────────────────────────────────────────────────────────────────

def sync(table: str, dry_run: bool) -> "SchemaSyncReport":
    import yaml as _yaml

    from dev_tools.models import SchemaSyncReport
    from dev_tools.scripts.clickhouse_introspect import introspect
    from dev_tools.scripts.chroma_patch import patch as chroma_patch
    from dev_tools.scripts.prompt_patch import patch as prompt_patch
    from dev_tools.scripts.yaml_patch import patch as yaml_patch

    report = SchemaSyncReport(table=table, dry_run=dry_run)

    # ── Step 0: capture rollback snapshots (before touching anything) ──────
    rollback_state: dict = {}

    schema_path = Path(__file__).resolve().parents[1] / "agentic_system" / "schema" / f"{table}.yaml"
    if schema_path.exists():
        with schema_path.open() as f:
            rollback_state["yaml_snapshot"] = _yaml.safe_load(f)

    prompt_snapshots: dict[str, str] = {}
    from dev_tools.scripts.prompt_patch import PROMPT_FILES
    for p in PROMPT_FILES:
        if p.exists():
            rel = str(p.relative_to(Path(__file__).resolve().parents[1]))
            prompt_snapshots[rel] = p.read_text(encoding="utf-8")
    rollback_state["prompt_snapshots"] = prompt_snapshots

    # ── Step 1: introspect live schema ─────────────────────────────────────
    print("── Step 1/4  ClickHouse introspect ─────────────────────────────")
    try:
        live = introspect(table)
        report.live_schema = live
        for name, typ in live.items():
            print(f"  {name:25s}  {typ}")
    except Exception as exc:
        msg = f"ClickHouse introspect failed: {exc}"
        print(f"  ERROR: {msg}")
        report.errors.append(msg)
        return report
    print()

    # ── Step 2: patch YAML contract ────────────────────────────────────────
    print("── Step 2/4  YAML contract patch ───────────────────────────────")
    try:
        yaml_changes = yaml_patch(table, live, dry_run=dry_run)
        report.yaml_changes = [str(c) for c in yaml_changes]
        if yaml_changes:
            for c in yaml_changes:
                print(f"  {c}")
        else:
            print("  No changes needed.")
    except Exception as exc:
        msg = f"YAML patch failed: {exc}"
        print(f"  ERROR: {msg}")
        report.errors.append(msg)
    print()

    # ── Step 3: patch ChromaDB chunks ──────────────────────────────────────
    print("── Step 3/4  ChromaDB chunk patch ──────────────────────────────")
    try:
        chroma_changes = chroma_patch(dry_run=dry_run)
        report.chroma_changes = [str(c) for c in chroma_changes]
        if chroma_changes:
            for c in chroma_changes:
                print(f"  {c}")
        else:
            print("  No stale chunks found.")
    except Exception as exc:
        msg = f"ChromaDB patch failed: {exc}"
        print(f"  ERROR: {msg}")
        report.errors.append(msg)
    print()

    # ── Step 4: patch agent prompts ────────────────────────────────────────
    print("── Step 4/4  Agent prompt patch ────────────────────────────────")
    try:
        p_changes = prompt_patch(dry_run=dry_run)
        report.prompt_changes = [str(c) for c in p_changes]
        if p_changes:
            for c in p_changes:
                print(f"  {c}")
        else:
            print("  No changes needed.")
    except Exception as exc:
        msg = f"Prompt patch failed: {exc}"
        print(f"  ERROR: {msg}")
        report.errors.append(msg)
    print()

    # ── Save rollback state (only on actual sync, not dry-run) ─────────────
    if not dry_run and report.total_changes > 0:
        report.rollback_state = rollback_state
        _save_rollback_state(table, rollback_state)

    return report


# ── Entry point ────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="schema_sync — patch all agentic system layers after a schema migration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python dev_tools/schema_sync.py --table github_events
  python dev_tools/schema_sync.py --table github_events --dry-run
  python dev_tools/schema_sync.py --table github_events --rollback
""",
    )
    parser.add_argument("--table", default="github_events", help="ClickHouse table to sync")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without touching any files or databases",
    )
    parser.add_argument(
        "--rollback",
        action="store_true",
        help="Reverse the most recent sync using saved rollback state",
    )
    args = parser.parse_args()

    if args.dry_run and args.rollback:
        print("ERROR: --dry-run and --rollback are mutually exclusive.")
        return 1

    print(f"==> schema_sync  table={args.table}")
    if args.dry_run:
        print("    Mode: DRY RUN (nothing will be written)")
    elif args.rollback:
        print("    Mode: ROLLBACK")
    else:
        print("    Mode: SYNC (patching all layers)")
    print()

    if args.rollback:
        try:
            _do_rollback(args.table)
        except FileNotFoundError as exc:
            print(f"ERROR: {exc}")
            return 1
        return 0

    report = sync(args.table, dry_run=args.dry_run)
    report.print()

    return 1 if report.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
