#!/usr/bin/env sh

set -eu

ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
VOLUME_MODE="keep"
CLEAR_IMAGES=0
START_AFTER=0
DRY_RUN=0

usage() {
  cat <<'EOF'
Usage: scripts/cleanup_infra.sh [--keep-volumes|--clear-volumes] [--clear-images] [--start-after] [--dry-run]

Cleans up local infrastructure resources used by this repository:
- compose stack from ./docker-compose.yml
- temporary INF-07 verification containers
- manual live containers created during infra task verification

Options:
  --keep-volumes   Keep Docker volumes (default)
  --clear-volumes  Remove known project/verification Docker volumes
  --clear-images   Remove known project/verification Docker images
  --start-after    Start compose stack after cleanup using docker-compose.yml
  --dry-run        Print commands without executing them
  -h, --help       Show this help
EOF
}

run_cmd() {
  if [ "${DRY_RUN}" -eq 1 ]; then
    printf '[dry-run] %s\n' "$*"
  else
    printf '[run] %s\n' "$*"
    "$@"
  fi
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --keep-volumes)
      VOLUME_MODE="keep"
      ;;
    --clear-volumes)
      VOLUME_MODE="clear"
      ;;
    --start-after)
      START_AFTER=1
      ;;
    --clear-images)
      CLEAR_IMAGES=1
      ;;
    --dry-run)
      DRY_RUN=1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      printf 'Unknown argument: %s\n' "$1" >&2
      usage >&2
      exit 1
      ;;
  esac
  shift
done

printf 'Cleaning infrastructure resources in %s\n' "${ROOT_DIR}"

# 1) Bring down the primary compose stack if present.
if [ -f "${ROOT_DIR}/docker-compose.yml" ]; then
  run_cmd docker compose -f "${ROOT_DIR}/docker-compose.yml" down
fi

# 2) Remove compose verification containers and one-off manual containers.
CONTAINER_PATTERNS="
skills_talk_inf07_verify-
skills-talk-clickhouse-live
skills-talk-clickhouse-seed
skills-talk-chromadb-live
skills-talk-mlflow-live
"

for pattern in ${CONTAINER_PATTERNS}; do
  ids="$(docker ps -aq --filter "name=${pattern}" || true)"
  if [ -n "${ids}" ]; then
    run_cmd docker rm -f ${ids}
  fi
done

# 3) Remove compose verification network if still present.
verify_networks="$(docker network ls -q --filter "name=skills_talk_inf07_verify_default" || true)"
if [ -n "${verify_networks}" ]; then
  run_cmd docker network rm ${verify_networks}
fi

# 4) Optionally remove known volumes.
if [ "${VOLUME_MODE}" = "clear" ]; then
  VOLUME_PATTERNS="
skills_talk_agent_camp_2026_
skills_talk_inf07_verify_
skills-talk-clickhouse-
skills-talk-chromadb-
skills-talk-mlflow-
"
  for pattern in ${VOLUME_PATTERNS}; do
    vids="$(docker volume ls -q --filter "name=${pattern}" || true)"
    if [ -n "${vids}" ]; then
      run_cmd docker volume rm ${vids}
    fi
  done
fi

# 5) Optionally remove known images.
if [ "${CLEAR_IMAGES}" -eq 1 ]; then
  IMAGE_PATTERNS="
skills_talk_agent_camp_2026-
skills_talk_inf07_verify-
skills-talk-clickhouse:
skills-talk-chromadb:
skills-talk-mlflow:
tmp-
"
  for pattern in ${IMAGE_PATTERNS}; do
    iids="$(docker images --format '{{.Repository}}:{{.Tag}}' | grep "${pattern}" || true)"
    if [ -n "${iids}" ]; then
      run_cmd docker rmi ${iids}
    fi
  done
fi

# 6) Optionally start stack after cleanup.
if [ "${START_AFTER}" -eq 1 ] && [ -f "${ROOT_DIR}/docker-compose.yml" ]; then
  run_cmd docker compose -f "${ROOT_DIR}/docker-compose.yml" up -d
fi

printf 'Cleanup completed.\n'
