#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/dev-common.sh
source "$SCRIPT_DIR/lib/dev-common.sh"

rollback() {
  printf "\nStartup failed. Stopping any services started in this attempt...\n" >&2
  stop_service web >/dev/null 2>&1 || true
  stop_service obs >/dev/null 2>&1 || true
  stop_service core >/dev/null 2>&1 || true
}

trap rollback ERR

check_prereqs
check_port_available core
check_port_available obs
check_port_available web

printf "Starting Core on %s...\n" "$CORE_URL"
start_service core
wait_for_http core "$CORE_URL/healthz" 30
wait_for_http core "$CORE_URL/readyz" 30

printf "Starting Observability on %s...\n" "$OBS_URL"
start_service obs
wait_for_http obs "$OBS_URL/health" 30

printf "Starting UI on %s...\n" "$WEB_URL"
start_service web
wait_for_http web "$WEB_URL/api/core/healthz" 45

trap - ERR

printf "\nStateLock local stack is up.\n"
printf "Core          %s\n" "$CORE_URL"
printf "Observability %s\n" "$OBS_URL"
printf "UI            %s\n" "$WEB_URL"
printf "\nLogs:\n"
printf "  core: %s\n" "$CORE_LOG_FILE"
printf "  obs:  %s\n" "$OBS_LOG_FILE"
printf "  web:  %s\n" "$WEB_LOG_FILE"
