#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/dev-common.sh
source "$SCRIPT_DIR/lib/dev-common.sh"

available_logs=()
for service in core obs web; do
  log_file="$(service_log_file "$service")"
  if [[ -f "$log_file" ]]; then
    available_logs+=("$service:$log_file")
  fi
done

if [[ "${#available_logs[@]}" -eq 0 ]]; then
  printf "No launcher logs found yet. Run make dev-up first.\n" >&2
  exit 1
fi

printf "Tailing launcher logs. Press Ctrl+C to stop.\n"

temp_dir="$(mktemp -d)"
trap 'rm -rf "$temp_dir"' EXIT

pids=()
for entry in "${available_logs[@]}"; do
  service="${entry%%:*}"
  log_file="${entry#*:}"
  fifo="$temp_dir/${service}.fifo"
  mkfifo "$fifo"

  sed "s/^/[$service] /" <"$fifo" &
  pids+=("$!")

  tail -n 20 -f "$log_file" >"$fifo" &
  pids+=("$!")
done

wait
