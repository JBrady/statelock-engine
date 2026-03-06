#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/dev-common.sh
source "$SCRIPT_DIR/lib/dev-common.sh"

printf "StateLock Stack Status\n\n"
printf "Overall: %s\n\n" "$(stack_overall_status)"
print_status_block core
printf "\n"
print_status_block obs
printf "\n"
print_status_block web
