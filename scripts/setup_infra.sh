#!/usr/bin/env sh

set -eu

ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
PROJECT_NAME="$(basename "${ROOT_DIR}")"
CLEAN_FIRST=0
CLEAR_VOLUMES=0
DRY_RUN=0
MLFLOW_HOST_PORT="5002"

usage() {
  cat <<'EOF'
Usage: scripts/setup_infra.sh [--clean-first] [--clear-volumes] [--dry-run]

Starts local infrastructure using docker-compose.yml.

Options:
  --clean-first             Run cleanup before startup (keeps volumes by default)
  --clear-volumes           Use with --clean-first to reset volumes before startup
  --dry-run                 Print commands without executing them
  -h, --help                Show this help
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

is_port_busy() {
  port="$1"
  if lsof -n -P -iTCP:"${port}" -sTCP:LISTEN >/dev/null 2>&1; then
    return 0
  fi
  return 1
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --clean-first)
      CLEAN_FIRST=1
      ;;
    --clear-volumes)
      CLEAR_VOLUMES=1
      ;;
    --dry-run)
      DRY_RUN=1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
  shift
done

if [ "${CLEAN_FIRST}" -eq 0 ] && [ "${CLEAR_VOLUMES}" -eq 1 ]; then
  echo "--clear-volumes requires --clean-first" >&2
  exit 1
fi

printf 'Starting infrastructure in %s\n' "${ROOT_DIR}"

if [ "${CLEAN_FIRST}" -eq 1 ]; then
  if [ "${CLEAR_VOLUMES}" -eq 1 ]; then
    run_cmd "${ROOT_DIR}/scripts/cleanup_infra.sh" --clear-volumes
  else
    run_cmd "${ROOT_DIR}/scripts/cleanup_infra.sh" --keep-volumes
  fi
fi

compose_file="${ROOT_DIR}/docker-compose.yml"

# Fail fast if port 5002 is already in use.
# To free the port, find and kill the process holding it:
#   lsof -ti tcp:5002 | xargs kill -9
if is_port_busy "${MLFLOW_HOST_PORT}"; then
  printf 'MLflow host port %s is already in use. Free the port and retry.\n' "${MLFLOW_HOST_PORT}" >&2
  printf 'To kill the process:  lsof -ti tcp:%s | xargs kill -9\n' "${MLFLOW_HOST_PORT}" >&2
  exit 1
fi

run_cmd docker compose -p "${PROJECT_NAME}" -f "${compose_file}" up -d
run_cmd docker compose -p "${PROJECT_NAME}" -f "${compose_file}" ps

printf 'Infra startup complete. MLflow host port: %s\n' "${MLFLOW_HOST_PORT}"
