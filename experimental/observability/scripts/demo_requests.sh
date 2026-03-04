#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
API_KEY="${API_KEY:-dev-key}"
PRETTY=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --pretty)
      PRETTY=1
      shift
      ;;
    --base)
      BASE_URL="$2"
      shift 2
      ;;
    --token)
      API_KEY="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
  esac
done

AUTH="Authorization: Bearer ${API_KEY}"

print_json() {
  if [[ "$PRETTY" -eq 1 ]] && command -v jq >/dev/null 2>&1; then
    jq . 2>/dev/null || cat
  else
    cat
  fi
}

run_call() {
  local label="$1"
  shift
  echo ""
  echo "---- ${label} ----"
  local resp
  resp="$(curl -s "$@")"
  printf '%s\n' "$resp" | print_json
  echo ""
  LAST_RESP="$resp"
}

run_call "Create Conversation" \
  -X POST "$BASE_URL/v2/conversations" \
  -H "$AUTH" -H 'content-type: application/json' \
  -d '{"title":"demo"}'
CID="$(printf '%s\n' "$LAST_RESP" | python3 -c 'import sys,json; print(json.load(sys.stdin)["conversation_id"])')"
echo "CID=$CID"

run_call "Add Turn" \
  -X POST "$BASE_URL/v2/conversations/$CID/turns" \
  -H "$AUTH" -H 'content-type: application/json' \
  -d '{"speaker":"user","text":"Help debug packet loss","thread_hint":"networking"}'
TURN_ID="$(printf '%s\n' "$LAST_RESP" | python3 -c 'import sys,json; print(json.load(sys.stdin)["turn_id"])')"
echo "last TID=$TURN_ID"

run_call "Segment" \
  -X POST "$BASE_URL/v2/conversations/$CID/segment" \
  -H "$AUTH" -H 'content-type: application/json' \
  -d '{"mode":"incremental"}'

run_call "Build Working Context" \
  -X POST "$BASE_URL/v2/conversations/$CID/working_context" \
  -H "$AUTH" -H 'content-type: application/json' \
  -d '{"query":"packet loss troubleshooting"}'

run_call "Telemetry Snapshot" \
  -X POST "$BASE_URL/v2/conversations/$CID/telemetry" \
  -H "$AUTH" -H 'content-type: application/json' \
  -d "{\"turn_id\":\"$TURN_ID\",\"query\":\"packet loss troubleshooting\",\"mode\":\"verbose\"}"

run_call "Recent Telemetry" \
  "$BASE_URL/v2/conversations/$CID/telemetry/recent?limit=5" \
  -H "$AUTH"

run_call "Run Groups" \
  "$BASE_URL/v2/conversations/$CID/telemetry/run_groups/recent?limit=5" \
  -H "$AUTH"

run_call "List Spans" \
  "$BASE_URL/v2/conversations/$CID/spans?include_quarantined=true" \
  -H "$AUTH"

run_call "Distill Memory" \
  -X POST "$BASE_URL/v2/conversations/$CID/memory/distill" \
  -H "$AUTH" -H 'content-type: application/json' \
  -d '{"trigger":"user_done"}'

run_call "List Memory" \
  "$BASE_URL/v2/memory?conversation_id=$CID" \
  -H "$AUTH"
