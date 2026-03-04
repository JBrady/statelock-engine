#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
API_KEY="${API_KEY:-dev-key}"
AUTH="Authorization: Bearer ${API_KEY}"

print_json() {
  if command -v jq >/dev/null 2>&1; then
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
}

echo ""
echo "---- Create Conversation ----"
CREATE_RESP="$(curl -s -X POST "$BASE_URL/v2/conversations" -H "$AUTH" -H 'content-type: application/json' -d '{"title":"demo"}')"
printf '%s\n' "$CREATE_RESP" | print_json
echo ""
CID="$(printf '%s\n' "$CREATE_RESP" | python3 -c 'import sys,json; print(json.load(sys.stdin)["conversation_id"])')"
echo "conversation_id=$CID"
echo ""

echo "---- Add Turn ----"
TURN_RESP="$(curl -s -X POST "$BASE_URL/v2/conversations/$CID/turns" -H "$AUTH" -H 'content-type: application/json' -d '{"speaker":"user","text":"Help debug packet loss","thread_hint":"networking"}')"
printf '%s\n' "$TURN_RESP" | print_json
echo ""
TURN_ID="$(printf '%s\n' "$TURN_RESP" | python3 -c 'import sys,json; print(json.load(sys.stdin)["turn_id"])')"

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
  -d "{\"turn_id\":\"$TURN_ID\",\"query\":\"packet loss troubleshooting\",\"mode\":\"minimal\"}"

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
