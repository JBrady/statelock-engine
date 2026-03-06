#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/dev-common.sh
source "$SCRIPT_DIR/lib/dev-common.sh"

bash "$SCRIPT_DIR/dev-up.sh"

if command -v open >/dev/null 2>&1; then
  open "$WEB_URL"
  printf "Opened %s\n" "$WEB_URL"
else
  printf "UI is ready at %s\n" "$WEB_URL"
fi
