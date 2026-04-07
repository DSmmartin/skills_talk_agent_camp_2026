#!/usr/bin/env sh

set -eu

ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
PROJECT_NAME="$(basename "${ROOT_DIR}")"
CLEAN_FIRST=0
CLEAR_VOLUMES=0
DRY_RUN=0
MLFLOW_HOST_PORT="5000"
CUSTOM_MLFLOW_PORT=0

usage() {
  cat <<'EOF'
Usage: scripts/setup_infra.sh [--clean-first] [--clear-volumes] [--mlflow-host-port <port>] [--dry-run]

Starts local infrastructure using docker-compose.yml.

Options:
  --clean-first             Run cleanup before startup (keeps volumes by default)
  --clear-volumes           Use with --clean-first to reset volumes before startup
  --mlflow-host-port <n>    Publish MLflow on host port <n> (default: 5000)
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

select_fallback_mlflow_port() {
  for candidate in 5002 5003 5004 5005 5006 5007 5008 5009 5010; do
    if ! is_port_busy "${candidate}"; then
      printf '%s\n' "${candidate}"
      return 0
    fi
  done
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
    --mlflow-host-port)
      shift
      if [ "$#" -eq 0 ]; then
        echo "Missing value for --mlflow-host-port" >&2
        exit 1
      fi
      MLFLOW_HOST_PORT="$1"
      CUSTOM_MLFLOW_PORT=1
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

case "${MLFLOW_HOST_PORT}" in
  ''|*[!0-9]*)
    echo "MLflow host port must be numeric" >&2
    exit 1
    ;;
esac

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
effective_compose_file="${compose_file}"

# Resolve MLflow host port conflicts.
if is_port_busy "${MLFLOW_HOST_PORT}"; then
  if [ "${CUSTOM_MLFLOW_PORT}" -eq 1 ]; then
    printf 'Requested MLflow host port %s is already in use.\n' "${MLFLOW_HOST_PORT}" >&2
    exit 1
  fi

  fallback_port="$(select_fallback_mlflow_port || true)"
  if [ -z "${fallback_port}" ]; then
    echo "Could not find a free fallback port for MLflow in range 5002-5010." >&2
    exit 1
  fi
  printf 'Port %s is busy; using MLflow host port %s for this startup.\n' "${MLFLOW_HOST_PORT}" "${fallback_port}"
  MLFLOW_HOST_PORT="${fallback_port}"
fi

if [ "${MLFLOW_HOST_PORT}" != "5000" ]; then
  effective_compose_file="/tmp/skills-talk-setup-compose-${MLFLOW_HOST_PORT}.yml"
  sed \
    -e "s#\"5000:5000\"#\"${MLFLOW_HOST_PORT}:5000\"#" \
    -e "s#context: \./#context: ${ROOT_DIR}/#g" \
    -e "s#- \./#- ${ROOT_DIR}/#g" \
    "${compose_file}" > "${effective_compose_file}"
fi

run_cmd docker compose -p "${PROJECT_NAME}" -f "${effective_compose_file}" up -d
run_cmd docker compose -p "${PROJECT_NAME}" -f "${effective_compose_file}" ps

printf 'Infra startup complete. MLflow host port: %s\n' "${MLFLOW_HOST_PORT}"
