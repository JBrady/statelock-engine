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
ENSURE_SERVICE_ACTION=""

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

process_command() {
  local pid="$1"
  ps -p "$pid" -o command= 2>/dev/null || true
}

pid_matches_service() {
  local service="$1"
  local pid="$2"
  local command
  command="$(process_command "$pid")"
  if [[ -z "$command" ]]; then
    return 1
  fi

  case "$service" in
    core)
      [[ "$command" == *"uvicorn main:app"* ]]
      ;;
    obs)
      [[ "$command" == *"uvicorn app.main:app"* ]]
      ;;
    web)
      [[ "$command" == *"npm run dev"* || "$command" == *"next dev"* || "$command" == *"next/dist/bin/next"* ]]
      ;;
    *)
      return 1
      ;;
  esac
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
  if [[ -z "${pid:-}" ]]; then
    return 0
  fi

  if ! pid_is_running "$pid"; then
    rm -f "$pid_file"
    printf "%s: repaired stale pid file (%s was not running)\n" "$service" "$pid" >&2
    return 0
  fi

  if ! pid_matches_service "$service" "$pid"; then
    rm -f "$pid_file"
    printf "%s: repaired stale pid file (%s did not match expected process)\n" "$service" "$pid" >&2
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

port_listener_pids() {
  local port="$1"
  lsof -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null || true
}

ensure_command() {
  local cmd="$1"
  local help="$2"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    printf "Missing required command: %s\nNext step: %s\n" "$cmd" "$help" >&2
    exit 1
  fi
}

ensure_file() {
  local path="$1"
  local help="$2"
  if [[ ! -f "$path" ]]; then
    printf "Missing required file: %s\nNext step: %s\n" "$path" "$help" >&2
    exit 1
  fi
}

check_prereqs() {
  ensure_command python3 "install python3 so the launcher can spawn detached local services"
  ensure_command curl "install curl so the launcher can perform health checks"
  ensure_command lsof "install lsof so the launcher can validate ports before startup"
  ensure_command node "install Node.js so apps/web can run"
  ensure_command npm "install npm so apps/web can run"

  ensure_file "$REPO_ROOT/.venv/bin/python" "from repo root run: python3 -m venv .venv && source .venv/bin/activate && make setup-dev"
  ensure_file "$REPO_ROOT/experimental/observability/.venv/bin/python" "from repo root run: cd experimental/observability && python3.11 -m venv .venv && ./.venv/bin/python -m pip install -e '.[dev]'"
  ensure_file "$REPO_ROOT/apps/web/package-lock.json" "restore or create apps/web/package-lock.json before using the launcher"
  ensure_file "$REPO_ROOT/apps/web/node_modules/next/package.json" "from repo root run: cd apps/web && npm ci"
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

service_health_code() {
  local service="$1"
  case "$service" in
    core)
      if http_ok "$CORE_URL/healthz" && http_ok "$CORE_URL/readyz"; then
        printf "healthy"
      elif http_ok "$CORE_URL/healthz"; then
        printf "degraded"
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
        printf "degraded"
      else
        printf "unhealthy"
      fi
      ;;
    *)
      printf "unknown"
      ;;
  esac
}

service_health_phrase() {
  local service="$1"
  case "$(service_health_code "$service")" in
    healthy)
      printf "healthy"
      ;;
    degraded)
      case "$service" in
        core) printf "process up, not ready" ;;
        web) printf "process up, proxy not ready" ;;
        *) printf "degraded" ;;
      esac
      ;;
    unhealthy)
      printf "unhealthy"
      ;;
    *)
      printf "unknown"
      ;;
  esac
}

service_runtime_snapshot() {
  local service="$1"
  clear_stale_pid "$service"

  local pid=""
  local port
  local listeners
  local health

  port="$(service_port "$service")"
  health="$(service_health_code "$service")"

  if pid="$(service_pid_status "$service" 2>/dev/null)"; then
    if [[ "$health" == "healthy" ]]; then
      printf "launcher|healthy|%s\n" "$pid"
    elif [[ "$health" == "degraded" ]]; then
      printf "launcher|degraded|%s\n" "$pid"
    else
      printf "launcher|unhealthy|%s\n" "$pid"
    fi
    return 0
  fi

  listeners="$(port_listener "$port")"
  if [[ -n "$listeners" ]]; then
    if [[ "$health" == "healthy" ]]; then
      printf "unmanaged|healthy|-\n"
    elif [[ "$health" == "degraded" ]]; then
      printf "unmanaged|degraded|-\n"
    else
      printf "conflict|port-in-use|-\n"
    fi
    return 0
  fi

  printf "none|stopped|-\n"
}

wait_for_service_ready() {
  local service="$1"
  local timeout="${2:-}"
  case "$service" in
    core)
      wait_for_http core "$CORE_URL/healthz" "${timeout:-30}"
      wait_for_http core "$CORE_URL/readyz" "${timeout:-30}"
      ;;
    obs)
      wait_for_http obs "$OBS_URL/health" "${timeout:-30}"
      ;;
    web)
      wait_for_http web "$WEB_URL/api/core/healthz" "${timeout:-45}"
      ;;
    *)
      printf "Unknown service: %s\n" "$service" >&2
      return 1
      ;;
  esac
}

describe_port_conflict() {
  local service="$1"
  local port
  port="$(service_port "$service")"
  printf "%s cannot start because port %s is occupied by a non-StateLock process.\n" "$service" "$port" >&2
  port_listener "$port" >&2
}

ensure_service_running() {
  local service="$1"
  local label="$2"
  local snapshot owner health pid
  ENSURE_SERVICE_ACTION="none"

  snapshot="$(service_runtime_snapshot "$service")"
  IFS='|' read -r owner health pid <<<"$snapshot"

  case "$owner:$health" in
    launcher:healthy)
      ENSURE_SERVICE_ACTION="reused"
      printf "%s already running and healthy.\n" "$label"
      return 0
      ;;
    unmanaged:healthy)
      ENSURE_SERVICE_ACTION="reused"
      printf "%s already running and healthy on %s (not launcher-managed).\n" \
        "$label" "$(service_url "$service")"
      return 0
      ;;
    launcher:degraded)
      ENSURE_SERVICE_ACTION="reused"
      printf "%s already running and still settling; waiting for readiness...\n" "$label"
      wait_for_service_ready "$service" 15
      return 0
      ;;
    unmanaged:degraded)
      ENSURE_SERVICE_ACTION="reused"
      printf "%s is already serving on %s and looks like StateLock; waiting for readiness...\n" \
        "$label" "$(service_url "$service")"
      wait_for_service_ready "$service" 15
      return 0
      ;;
    launcher:unhealthy)
      ENSURE_SERVICE_ACTION="restarted"
      printf "%s is launcher-managed but unhealthy; restarting it...\n" "$label"
      stop_service "$service" >/dev/null
      ;;
    conflict:port-in-use)
      describe_port_conflict "$service"
      return 1
      ;;
    none:stopped)
      ENSURE_SERVICE_ACTION="started"
      ;;
    *)
      printf "%s is in an unexpected state (%s).\n" "$label" "$snapshot" >&2
      return 1
      ;;
  esac

  printf "Starting %s on %s...\n" "$label" "$(service_url "$service")"
  start_service "$service"
  wait_for_service_ready "$service"
}

stop_service() {
  local service="$1"
  local pid_file
  pid_file="$(service_pid_file "$service")"
  local pid
  pid="$(read_pid "$pid_file")"

  if [[ -z "${pid:-}" ]]; then
    local snapshot owner health _
    snapshot="$(service_runtime_snapshot "$service")"
    IFS='|' read -r owner health _ <<<"$snapshot"
    case "$owner:$health" in
      unmanaged:healthy|unmanaged:degraded)
        printf "%s: running on %s but not launcher-managed; leaving it alone\n" \
          "$service" "$(service_url "$service")"
        ;;
      conflict:port-in-use)
        printf "%s: port %s is occupied by a non-StateLock process; nothing stopped\n" \
          "$service" "$(service_port "$service")"
        ;;
      *)
        printf "%s: not running (no pid file)\n" "$service"
        ;;
    esac
    return 0
  fi

  if ! pid_is_running "$pid"; then
    rm -f "$pid_file"
    printf "%s: stale pid removed (%s)\n" "$service" "$pid"
    return 0
  fi

  if ! pid_matches_service "$service" "$pid"; then
    rm -f "$pid_file"
    printf "%s: pid file removed without killing pid %s (process no longer matched %s)\n" \
      "$service" "$pid" "$service"
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
  service_health_phrase "$service"
}

stack_overall_status() {
  local services=(core obs web)
  local healthy_count=0
  local degraded_count=0
  local conflict_count=0
  local stopped_count=0
  local service snapshot owner health pid

  for service in "${services[@]}"; do
    snapshot="$(service_runtime_snapshot "$service")"
    IFS='|' read -r owner health pid <<<"$snapshot"
    case "$owner:$health" in
      launcher:healthy|unmanaged:healthy) healthy_count=$((healthy_count + 1)) ;;
      launcher:degraded|unmanaged:degraded) degraded_count=$((degraded_count + 1)) ;;
      conflict:port-in-use) conflict_count=$((conflict_count + 1)) ;;
      none:stopped) stopped_count=$((stopped_count + 1)) ;;
      *) degraded_count=$((degraded_count + 1)) ;;
    esac
  done

  if [[ "$healthy_count" -eq 3 ]]; then
    printf "healthy"
  elif [[ "$conflict_count" -gt 0 ]]; then
    printf "blocked"
  elif [[ "$stopped_count" -eq 0 && "$degraded_count" -gt 0 && $((healthy_count + degraded_count)) -eq 3 ]]; then
    printf "degraded"
  elif [[ "$stopped_count" -eq 3 ]]; then
    printf "stopped"
  elif [[ "$healthy_count" -gt 0 || "$degraded_count" -gt 0 ]]; then
    printf "partial"
  else
    printf "mixed"
  fi
}

service_display_name() {
  case "$1" in
    core) printf "Core" ;;
    obs) printf "Observability" ;;
    web) printf "UI" ;;
    *) printf "%s" "$1" ;;
  esac
}

service_status_label() {
  local service="$1"
  local snapshot owner health pid
  snapshot="$(service_runtime_snapshot "$service")"
  IFS='|' read -r owner health pid <<<"$snapshot"

  case "$owner:$health" in
    launcher:healthy) printf "healthy" ;;
    launcher:degraded) printf "degraded" ;;
    launcher:unhealthy) printf "unhealthy" ;;
    unmanaged:healthy) printf "healthy (external)" ;;
    unmanaged:degraded) printf "degraded (external)" ;;
    conflict:port-in-use) printf "blocked" ;;
    none:stopped) printf "down" ;;
    *) printf "unknown" ;;
  esac
}

service_status_detail() {
  local service="$1"
  local snapshot owner health pid
  snapshot="$(service_runtime_snapshot "$service")"
  IFS='|' read -r owner health pid <<<"$snapshot"

  case "$owner:$health" in
    launcher:healthy)
      return 0
      ;;
    launcher:degraded|launcher:unhealthy)
      printf "launcher-managed, pid=%s, log=%s" "$pid" "$(service_log_file "$service")"
      ;;
    unmanaged:healthy|unmanaged:degraded)
      printf "running outside the launcher on the expected port"
      ;;
    conflict:port-in-use)
      printf "port %s is occupied by a non-StateLock process" "$(service_port "$service")"
      ;;
    none:stopped)
      return 0
      ;;
  esac
}

print_status_block() {
  local service="$1"
  local url detail

  printf "%s: %s\n" \
    "$(service_display_name "$service")" \
    "$(service_status_label "$service")"

  url="$(service_url "$service")"
  if [[ -n "$url" ]]; then
    printf "  %s\n" "$url"
  fi

  detail="$(service_status_detail "$service")" || true
  if [[ -n "${detail:-}" ]]; then
    printf "  %s\n" "$detail"
  fi
}
