SHELL := /bin/sh

ifneq (,$(wildcard .env))
include .env
export
endif

PROJECT_NAME ?= $(notdir $(CURDIR))
MLFLOW_HOST_PORT ?= 5000
CHROMA_HOST_PORT ?= 8000
CHROMA_BASE_URL ?= http://127.0.0.1:$(CHROMA_HOST_PORT)
GITHUB_ARCHIVE_TARGET_ROWS ?= 5000000
GITHUB_ARCHIVE_SOURCE_SUFFIXES ?= aa ab ac ad ae af ag

COMPOSE_CMD := docker compose -p $(PROJECT_NAME) -f docker-compose.yml
SETUP_MLFLOW_ARG :=

ifneq ($(MLFLOW_HOST_PORT),5000)
SETUP_MLFLOW_ARG := --mlflow-host-port $(MLFLOW_HOST_PORT)
endif

.PHONY: help up down seed seed-vectors migrate rollback reset logs

help:
	@printf '%s\n' 'Available targets:'
	@printf '%s\n' '  make up             Start infra stack (ClickHouse, ChromaDB, MLflow)'
	@printf '%s\n' '  make down           Stop infra stack'
	@printf '%s\n' '  make seed           Seed ClickHouse sample PR dataset'
	@printf '%s\n' '  make seed-vectors   Seed ChromaDB collections'
	@printf '%s\n' '  make migrate        Run schema migration script (when available)'
	@printf '%s\n' '  make rollback       Run schema rollback script (when available)'
	@printf '%s\n' '  make reset          Recreate infra from scratch (clears volumes)'
	@printf '%s\n' '  make logs           Print service logs'

up:
	./scripts/setup_infra.sh $(SETUP_MLFLOW_ARG)

down:
	$(COMPOSE_CMD) down

seed:
	$(COMPOSE_CMD) exec -T clickhouse sh -lc 'GITHUB_ARCHIVE_TARGET_ROWS=$(GITHUB_ARCHIVE_TARGET_ROWS) GITHUB_ARCHIVE_SOURCE_SUFFIXES="$(GITHUB_ARCHIVE_SOURCE_SUFFIXES)" /opt/demo/init/02_seed_data.sh'

seed-vectors:
	python3 db/vectordb/init/seed_vectors.py --base-url "$(CHROMA_BASE_URL)"

migrate:
	@if [ -f scripts/migrate_schema.py ]; then \
		python3 scripts/migrate_schema.py; \
	else \
		printf '%s\n' 'scripts/migrate_schema.py is not available yet (planned in MIG-01).'; \
		exit 1; \
	fi

rollback:
	@if [ -f scripts/rollback_schema.py ]; then \
		python3 scripts/rollback_schema.py; \
	else \
		printf '%s\n' 'scripts/rollback_schema.py is not available yet (planned in MIG-03).'; \
		exit 1; \
	fi

reset:
	./scripts/cleanup_infra.sh --clear-volumes
	./scripts/setup_infra.sh --clean-first --clear-volumes $(SETUP_MLFLOW_ARG)

logs:
	$(COMPOSE_CMD) logs --tail 200
