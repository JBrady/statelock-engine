#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
RUN_DIR="$REPO_ROOT/.run"
LOG_DIR="$RUN_DIR/logs"

CORE_PORT="${STATELOCK_CORE_PORT:-8000}"
OBS_PORT="${STATELOCK_OBS_PORT:-8001}"
WEB_PORT="${STATELOCK_WEB_PORT:-3001}"

CORE_PID_FILE="$RUN_DIR/core.pid"
OBS_PID_FILE="$RUN_DIR/obs.pid"
WEB_PID_FILE="$RUN_DIR/web.pid"

CORE_LOG_FILE="$LOG_DIR/core.log"
OBS_LOG_FILE="$LOG_DIR/obs.log"
WEB_LOG_FILE="$LOG_DIR/web.log"

CORE_URL="http://127.0.0.1:${CORE_PORT}"
OBS_URL="http://127.0.0.1:${OBS_PORT}"
WEB_URL="http://127.0.0.1:${WEB_PORT}"

OBS_API_KEY="${STATELOCK_OBS_API_KEY:-dev-key}"
CORE_API_KEY="${STATELOCK_CORE_API_KEY:-}"

mkdir -p "$LOG_DIR"

service_pid_file() {
  case "$1" in
    core) printf "%s\n" "$CORE_PID_FILE" ;;
    obs) printf "%s\n" "$OBS_PID_FILE" ;;
    web) printf "%s\n" "$WEB_PID_FILE" ;;
    *) return 1 ;;
  esac
}

service_log_file() {
  case "$1" in
    core) printf "%s\n" "$CORE_LOG_FILE" ;;
    obs) printf "%s\n" "$OBS_LOG_FILE" ;;
    web) printf "%s\n" "$WEB_LOG_FILE" ;;
    *) return 1 ;;
  esac
}

service_port() {
  case "$1" in
    core) printf "%s\n" "$CORE_PORT" ;;
    obs) printf "%s\n" "$OBS_PORT" ;;
    web) printf "%s\n" "$WEB_PORT" ;;
    *) return 1 ;;
  esac
}

service_url() {
  case "$1" in
    core) printf "%s\n" "$CORE_URL" ;;
    obs) printf "%s\n" "$OBS_URL" ;;
    web) printf "%s\n" "$WEB_URL" ;;
    *) return 1 ;;
  esac
}

pid_is_running() {
  local pid="$1"
  kill -0 "$pid" 2>/dev/null
}

read_pid() {
  local pid_file="$1"
  if [[ -f "$pid_file" ]]; then
    tr -d '[:space:]' <"$pid_file"
  fi
}

clear_stale_pid() {
  local service="$1"
  local pid_file
  pid_file="$(service_pid_file "$service")"
  local pid
  pid="$(read_pid "$pid_file")"
  if [[ -n "${pid:-}" ]] && ! pid_is_running "$pid"; then
    rm -f "$pid_file"
  fi
}

service_pid_status() {
  local service="$1"
  clear_stale_pid "$service"
  local pid_file
  pid_file="$(service_pid_file "$service")"
  local pid
  pid="$(read_pid "$pid_file")"
  if [[ -n "${pid:-}" ]] && pid_is_running "$pid"; then
    printf "%s\n" "$pid"
    return 0
  fi
  return 1
}

port_listener() {
  local port="$1"
  lsof -nP -iTCP:"$port" -sTCP:LISTEN 2>/dev/null || true
}

ensure_command() {
  local cmd="$1"
  local help="$2"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    printf "Missing required command: %s\n%s\n" "$cmd" "$help" >&2
    exit 1
  fi
}

ensure_file() {
  local path="$1"
  local help="$2"
  if [[ ! -f "$path" ]]; then
    printf "Missing required file: %s\n%s\n" "$path" "$help" >&2
    exit 1
  fi
}

check_prereqs() {
  ensure_command python3 "Install python3 so the launcher can spawn detached local services."
  ensure_command curl "Install curl so the launcher can perform health checks."
  ensure_command lsof "Install lsof so the launcher can validate ports before startup."
  ensure_command node "Install Node.js so apps/web can run."
  ensure_command npm "Install npm so apps/web can run."

  ensure_file "$REPO_ROOT/.venv/bin/python" "Create the root Core virtualenv first: python3 -m venv .venv && make setup-dev"
  ensure_file "$REPO_ROOT/experimental/observability/.venv/bin/python" "Create the Observability virtualenv first: cd experimental/observability && python3.11 -m venv .venv && ./.venv/bin/python -m pip install -e '.[dev]'"
  ensure_file "$REPO_ROOT/apps/web/package-lock.json" "apps/web is missing package-lock.json."
  ensure_file "$REPO_ROOT/apps/web/node_modules/next/package.json" "Install UI dependencies first: cd apps/web && npm ci"
}

check_port_available() {
  local service="$1"
  local port
  port="$(service_port "$service")"
  local pid=""
  if pid="$(service_pid_status "$service" 2>/dev/null)"; then
    printf "%s already running via PID %s.\nUse make dev-status or make dev-down before starting again.\n" "$service" "$pid" >&2
    exit 1
  fi

  local listeners
  listeners="$(port_listener "$port")"
  if [[ -n "$listeners" ]]; then
    printf "Port %s is already in use, cannot start %s.\n%s\n" "$port" "$service" "$listeners" >&2
    exit 1
  fi
}

launch_detached() {
  local workdir="$1"
  local log_file="$2"
  shift 2

  python3 - "$workdir" "$log_file" "$@" <<'PY'
import subprocess
import sys

workdir = sys.argv[1]
log_file = sys.argv[2]
command = sys.argv[3:]

with open(log_file, "ab", buffering=0) as log:
    process = subprocess.Popen(
        command,
        cwd=workdir,
        stdin=subprocess.DEVNULL,
        stdout=log,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )

print(process.pid)
PY
}

start_service() {
  local service="$1"
  local pid_file log_file pid
  pid_file="$(service_pid_file "$service")"
  log_file="$(service_log_file "$service")"
  rm -f "$pid_file"

  case "$service" in
    core)
      pid="$(
        launch_detached \
          "$REPO_ROOT" \
          "$log_file" \
          env \
          "PYTHONPATH=$REPO_ROOT" \
          "$REPO_ROOT/.venv/bin/python" \
          -m uvicorn main:app --host 127.0.0.1 --port "$CORE_PORT" --reload
      )"
      ;;
    obs)
      pid="$(
        launch_detached \
          "$REPO_ROOT/experimental/observability" \
          "$log_file" \
          env \
          "STATELOCK_API_KEY=$OBS_API_KEY" \
          "$REPO_ROOT/experimental/observability/.venv/bin/python" \
          -m uvicorn app.main:app --host 127.0.0.1 --port "$OBS_PORT" --reload
      )"
      ;;
    web)
      pid="$(
        launch_detached \
          "$REPO_ROOT/apps/web" \
          "$log_file" \
          env \
          "PORT=$WEB_PORT" \
          "STATELOCK_CORE_BASE_URL=$CORE_URL" \
          "STATELOCK_CORE_API_KEY=$CORE_API_KEY" \
          "STATELOCK_OBS_BASE_URL=$OBS_URL" \
          "STATELOCK_OBS_API_KEY=$OBS_API_KEY" \
          npm run dev -- --hostname 127.0.0.1
      )"
      ;;
    *)
      printf "Unknown service: %s\n" "$service" >&2
      exit 1
      ;;
  esac

  printf "%s\n" "$pid" >"$pid_file"
}

stop_service() {
  local service="$1"
  local pid_file
  pid_file="$(service_pid_file "$service")"
  local pid
  pid="$(read_pid "$pid_file")"

  if [[ -z "${pid:-}" ]]; then
    printf "%s: not running (no pid file)\n" "$service"
    return 0
  fi

  if ! pid_is_running "$pid"; then
    rm -f "$pid_file"
    printf "%s: stale pid removed (%s)\n" "$service" "$pid"
    return 0
  fi

  kill "$pid" 2>/dev/null || true
  local waited=0
  while pid_is_running "$pid" && [[ "$waited" -lt 10 ]]; do
    sleep 1
    waited=$((waited + 1))
  done

  if pid_is_running "$pid"; then
    kill -9 "$pid" 2>/dev/null || true
  fi

  rm -f "$pid_file"
  printf "%s: stopped (pid %s)\n" "$service" "$pid"
}

http_ok() {
  local url="$1"
  local header_name="${2:-}"
  local header_value="${3:-}"

  if [[ -n "$header_name" ]]; then
    curl -fsS -H "$header_name: $header_value" "$url" >/dev/null 2>&1
  else
    curl -fsS "$url" >/dev/null 2>&1
  fi
}

wait_for_http() {
  local service="$1"
  local url="$2"
  local timeout="${3:-30}"
  local header_name="${4:-}"
  local header_value="${5:-}"
  local elapsed=0

  while [[ "$elapsed" -lt "$timeout" ]]; do
    if http_ok "$url" "$header_name" "$header_value"; then
      return 0
    fi
    sleep 1
    elapsed=$((elapsed + 1))
  done

  printf "%s did not become healthy at %s within %ss.\nLog: %s\n" \
    "$service" "$url" "$timeout" "$(service_log_file "$service")" >&2
  return 1
}

health_summary() {
  local service="$1"
  case "$service" in
    core)
      if http_ok "$CORE_URL/healthz" && http_ok "$CORE_URL/readyz"; then
        printf "healthy"
      elif http_ok "$CORE_URL/healthz"; then
        printf "process up, not ready"
      else
        printf "unhealthy"
      fi
      ;;
    obs)
      if http_ok "$OBS_URL/health"; then
        printf "healthy"
      else
        printf "unhealthy"
      fi
      ;;
    web)
      if http_ok "$WEB_URL/api/core/healthz"; then
        printf "healthy"
      elif http_ok "$WEB_URL/"; then
        printf "process up, proxy not ready"
      else
        printf "unhealthy"
      fi
      ;;
    *)
      printf "unknown"
      ;;
  esac
}

print_status_line() {
  local service="$1"
  local url log_file pid listeners
  url="$(service_url "$service")"
  log_file="$(service_log_file "$service")"
  if pid="$(service_pid_status "$service" 2>/dev/null)"; then
    printf "%-5s running  pid=%-8s health=%-20s url=%s log=%s\n" \
      "$service" "$pid" "$(health_summary "$service")" "$url" "$log_file"
  elif listeners="$(port_listener "$(service_port "$service")")" && [[ -n "$listeners" ]]; then
    printf "%-5s external pid=%-8s health=%-20s url=%s log=%s\n" \
      "$service" "-" "port in use" "$url" "$log_file"
  else
    printf "%-5s stopped  pid=%-8s health=%-20s url=%s log=%s\n" \
      "$service" "-" "not running" "$url" "$log_file"
  fi
}
