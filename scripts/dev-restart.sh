#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

printf "Restarting StateLock local stack...\n"
bash "$SCRIPT_DIR/dev-down.sh"
printf "\n"
bash "$SCRIPT_DIR/dev-up.sh"
