#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/dev-common.sh
source "$SCRIPT_DIR/lib/dev-common.sh"

rollback() {
  local service
  if [[ "${#STARTED_SERVICES[@]}" -eq 0 ]]; then
    printf "\nStartup failed. No newly started services to roll back.\n" >&2
    return
  fi

  printf "\nStartup failed. Stopping services started in this attempt...\n" >&2
  for (( idx=${#STARTED_SERVICES[@]}-1 ; idx>=0 ; idx-- )); do
    service="${STARTED_SERVICES[idx]}"
    stop_service "$service" >/dev/null 2>&1 || true
  done
}

STARTED_SERVICES=()

trap rollback ERR

check_prereqs

ensure_service_running core "Core"
if [[ "$ENSURE_SERVICE_ACTION" == "started" ]]; then
  STARTED_SERVICES+=(core)
fi

ensure_service_running obs "Observability"
if [[ "$ENSURE_SERVICE_ACTION" == "started" ]]; then
  STARTED_SERVICES+=(obs)
fi

ensure_service_running web "UI"
if [[ "$ENSURE_SERVICE_ACTION" == "started" ]]; then
  STARTED_SERVICES+=(web)
fi

trap - ERR

printf "\nStateLock local stack is up.\n"
printf "Overall       %s\n" "$(stack_overall_status)"
printf "Core          %s\n" "$CORE_URL"
printf "Observability %s\n" "$OBS_URL"
printf "UI            %s\n" "$WEB_URL"
printf "\nStatus:\n"
print_status_block core
printf "\n"
print_status_block obs
printf "\n"
print_status_block web
printf "\nLogs:\n"
printf "  core: %s\n" "$CORE_LOG_FILE"
printf "  obs:  %s\n" "$OBS_LOG_FILE"
printf "  web:  %s\n" "$WEB_LOG_FILE"
