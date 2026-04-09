SHELL := /bin/sh

ifneq (,$(wildcard .env))
include .env
export
endif

PROJECT_NAME ?= $(notdir $(CURDIR))
MLFLOW_HOST_PORT ?= 5002
CHROMA_HOST_PORT ?= 8000
CHROMA_BASE_URL ?= http://127.0.0.1:$(CHROMA_HOST_PORT)
GITHUB_ARCHIVE_TARGET_ROWS ?= 5000000
GITHUB_ARCHIVE_SOURCE_SUFFIXES ?= aa ab ac ad ae af ag
LOCAL ?= 0

COMPOSE_CMD := docker compose -p $(PROJECT_NAME) -f docker-compose.yml

.PHONY: help up down seed seed-vectors migrate rollback validate-schema schema-sync schema-sync-dry test-complete-flow verify-complete-flow reset logs clean-complete

help:
	@printf '%s\n' 'Available targets:'
	@printf '%s\n' '  make up             Start infra stack (ClickHouse, ChromaDB, MLflow)'
	@printf '%s\n' '  make down           Stop infra stack'
	@printf '%s\n' '  make seed           Seed ClickHouse with ~5M GitHub Archive PR events'
	@printf '%s\n' '  make seed LOCAL=1   Seed ClickHouse with local 18-row controlled dataset (offline)'
	@printf '%s\n' '  make seed-vectors   Seed ChromaDB collections'
	@printf '%s\n' '  make migrate        Phase 2: rename merged → merged_at (silent failure)'
	@printf '%s\n' '  make rollback       Restore pre-migration schema + ChromaDB state'
	@printf '%s\n' '  make validate-schema Diff live ClickHouse schema vs YAML contract'
	@printf '%s\n' '  make schema-sync    Phase 3: patch all layers after migration'
	@printf '%s\n' '  make schema-sync-dry Phase 3: dry-run schema-sync (show changes only)'
	@printf '%s\n' '  make test-complete-flow Run mocked stateful flow test (pre->migrate->sync)'
	@printf '%s\n' '  make verify-complete-flow Run live sequential verification and auto-rollback'
	@printf '%s\n' '  make reset          Recreate infra from scratch (clears volumes)'
	@printf '%s\n' '  make logs           Print service logs'
	@printf '%s\n' '  make clean-complete Nuclear clean: stop containers, remove images, volumes, and free ports'

up:
	./scripts/setup_infra.sh 
down:
	$(COMPOSE_CMD) down

seed:
ifeq ($(LOCAL),1)
	$(COMPOSE_CMD) cp db/clickhouse/init/03_seed_local.sql clickhouse:/tmp/03_seed_local.sql
	$(COMPOSE_CMD) exec -T clickhouse sh -c 'clickhouse-client --multiquery < /tmp/03_seed_local.sql'
else
	$(COMPOSE_CMD) exec -T clickhouse sh -lc 'GITHUB_ARCHIVE_TARGET_ROWS=$(GITHUB_ARCHIVE_TARGET_ROWS) GITHUB_ARCHIVE_SOURCE_SUFFIXES="$(GITHUB_ARCHIVE_SOURCE_SUFFIXES)" /opt/bootstrap/init/02_seed_data.sh'
endif

seed-vectors:
	python3 db/vectordb/init/seed_vectors.py --base-url "$(CHROMA_BASE_URL)"

migrate:
	uv run python scripts/migrate_schema.py

rollback:
	uv run python scripts/rollback_schema.py

validate-schema:
	uv run python scripts/validate_schema.py

schema-sync:
	uv run python dev_tools/schema_sync.py --table github_events

schema-sync-dry:
	uv run python dev_tools/schema_sync.py --table github_events --dry-run

test-complete-flow:
	uv run pytest tests/test_complete_flow_mocked.py -q

verify-complete-flow:
	./scripts/verify_complete_flow.sh

reset:
	./scripts/cleanup_infra.sh --clear-volumes
	./scripts/setup_infra.sh --clean-first --clear-volumes 
logs:
	$(COMPOSE_CMD) logs --tail 200

clean-complete:
	@printf '%s\n' '==> Stopping and removing containers, networks, volumes, and images...'
	$(COMPOSE_CMD) down --volumes --rmi all --remove-orphans
	@printf '%s\n' '==> Freeing ports (8123 9000 8000 5002)...'
	@for port in 8123 9000 8000 5002; do \
		pids=$$(lsof -ti tcp:$$port 2>/dev/null); \
		if [ -n "$$pids" ]; then \
			printf 'Killing PIDs on port %s: %s\n' "$$port" "$$pids"; \
			kill -9 $$pids 2>/dev/null || true; \
		fi; \
	done
	@printf '%s\n' '==> Pruning dangling images and build cache...'
	docker image prune -f
	docker builder prune -f
	@printf '%s\n' '==> Done.'
