#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/dev-common.sh
source "$SCRIPT_DIR/lib/dev-common.sh"

printf "StateLock local stack status\n\n"
print_status_line core
print_status_line obs
print_status_line web
