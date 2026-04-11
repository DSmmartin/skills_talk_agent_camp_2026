---
id: DEV-10
name: SchemaSyncReport Dataclass with Complete Change Log
epic: Epic 4 - Developer Tools (Act 3)
status: [x] Done
summary: Dataclass in dev_tools/models.py capturing the complete change log from a schema_sync run — yaml_changes, chroma_changes, prompt_changes, live schema snapshot, dry_run flag, timestamp, and rollback state.
---

# DEV-10 — SchemaSyncReport Dataclass with Complete Change Log

- Epic: Epic 4 - Developer Tools (Act 3)
- Priority: P0
- Estimate: S
- Status: [x] Done
- Source: [PRODUCT_BACKLOG.md](/Users/mmartin/projects/skills_talk_agent_camp_2026/PRODUCT_BACKLOG.md#L161)

## Objective

Provide a structured, printable output object that captures everything `schema_sync.py` did in a single run — which layers were patched, what exactly changed in each, and whether the run was a dry-run or live. This is the Act 3 proof artefact: the presenter shows the report to demonstrate that all four layers were patched in one pass.

## Description

`SchemaSyncReport` is a `@dataclass` in `dev_tools/models.py` with fields for each patching layer, a live schema snapshot, a timestamp, and a dry_run flag. It provides:

- `total_changes` property — sum of all change counts across layers.
- `layers_touched` property — human-readable list of layer names that had changes.
- `print()` method — formatted box with per-layer change lists and a summary line.
- `to_dict()` method — JSON-serialisable representation for saving/logging.

The `rollback_state` field holds the pre-sync snapshots (YAML doc and prompt file contents) that `schema_sync.py` saves to `.schema_sync_rollback.json` for the `--rollback` flag.

## Scope

- `dev_tools/models.py` — `SchemaSyncReport` dataclass with all fields, properties, and methods.

## Out Of Scope

- Persistence of the report to disk (rollback state is saved separately by `schema_sync.py`).
- Report comparison between runs.

## Deliverables

- `dev_tools/models.py`

## Acceptance Criteria

- `SchemaSyncReport` has fields: `table`, `dry_run`, `timestamp`, `live_schema`, `yaml_changes`, `chroma_changes`, `prompt_changes`, `rollback_state`, `errors`.
- `total_changes` returns the correct sum.
- `layers_touched` returns only layers that had at least one change.
- `print()` produces a box with `═` borders, per-layer sections, and a summary line.
- `to_dict()` returns a JSON-serialisable dict (all values are strings, lists, dicts, or None).

## Dependencies

- DEV-09: `schema_sync.py` instantiates and populates this dataclass.
- DEV-06, DEV-07, DEV-08: each patch script returns change objects that are converted to strings for the report lists.

## Assumptions

- Change lists are stored as `list[str]` (the `__str__` of each change object) for simplicity.
- `timestamp` defaults to `datetime.utcnow()` at instantiation time.

## Verification

```bash
# Syntax check
uv run python -c "import ast; ast.parse(open('dev_tools/models.py').read()); print('OK')"

# Import check
uv run python -c "from dev_tools.models import SchemaSyncReport; print('OK')"

# Smoke test
uv run python -c "
from dev_tools.models import SchemaSyncReport
r = SchemaSyncReport(table='github_events', dry_run=True)
r.yaml_changes = ['yaml:added:merged_at (Nullable(DateTime))']
r.chroma_changes = ['chroma:patched:schema_docs:pr_fields (8 replacement(s))']
r.prompt_changes = ['prompt:patched:...system.md (6 replacement(s))']
r.print()
print('total_changes:', r.total_changes)
print('layers_touched:', r.layers_touched)
"
```

Expected smoke test output:
```
════════════════════════════════════════════════════════════
  [DRY RUN] Schema Sync Report — github_events
  YYYY-MM-DD HH:MM:SS UTC
════════════════════════════════════════════════════════════

  YAML contract  (1 change(s))
    • yaml:added:merged_at (Nullable(DateTime))

  ChromaDB chunks  (1 chunk(s) patched)
    • chroma:patched:schema_docs:pr_fields (8 replacement(s))

  Agent prompts  (1 file(s) patched)
    • prompt:patched:...system.md (6 replacement(s))

  Total: 3 change(s) across YAML contract, ChromaDB chunks, Agent prompts.
  Run without --dry-run to apply.
════════════════════════════════════════════════════════════

total_changes: 3
layers_touched: ['YAML contract', 'ChromaDB chunks', 'Agent prompts']
```

## Notes

- Completed 2026-04-08.
- `print()` uses `═` (U+2550) border characters to visually separate the report from step output.
- `to_dict()` converts `datetime` to ISO string for JSON compatibility.
