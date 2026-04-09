#!/usr/bin/env bash
set -euo pipefail

# Live sequential verification for the full lifecycle.
# Runs the exact lifecycle and restores schema at the end.

MIGRATED=0
BACKUP_DIR="$(mktemp -d)"
FILES_TO_RESTORE=(
  "agentic_system/schema/github_events.yaml"
  "agentic_system/agents_core/nl2sql/prompts/system.md"
  "agentic_system/agents_core/rag/prompts/system.md"
)

for file in "${FILES_TO_RESTORE[@]}"; do
  mkdir -p "$BACKUP_DIR/$(dirname "$file")"
  cp "$file" "$BACKUP_DIR/$file"
done

cleanup() {
  if [[ "$MIGRATED" -eq 1 ]]; then
    echo
    echo "==> Restoring pre-migration DB/Chroma state (make rollback)"
    make rollback || true
  fi
  for file in "${FILES_TO_RESTORE[@]}"; do
    cp "$BACKUP_DIR/$file" "$file" || true
  done
  rm -f dev_tools/.schema_sync_rollback.json || true
  rm -rf "$BACKUP_DIR" || true
}
trap cleanup EXIT

echo "==> Step 0/6: normalize pre-migration state"
make rollback || true

echo
echo "==> Step 1/6: pre-migration baseline"
uv run pytest -m pre_migration --tb=short -q

echo
echo "==> Step 2/6: apply migration"
make migrate
MIGRATED=1

echo
echo "==> Step 3/6: verify broken post-migration state"
uv run pytest -m post_migration --tb=short -q

echo
echo "==> Step 4/6: apply fully guided fix"
uv run python dev_tools/schema_sync.py --table github_events

echo
echo "==> Step 5/6: verify fixed state"
uv run pytest -m "schema_sync or complete_flow" --tb=short -q

echo
echo "==> Step 6/6: complete. Rollback will run now to restore baseline."
