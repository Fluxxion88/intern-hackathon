#!/usr/bin/env bash
# The §5.9 curl walkthrough, end-to-end against a real uvicorn.
# Self-contained: boots the server on :8010, runs every step, asserts, cleans up.
#
#   bash tests/api/test_walkthrough.sh            # from repo root
#   PORT=8000 KEEP_DATA=1 bash tests/api/test_walkthrough.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PORT="${PORT:-8010}"
BASE="http://localhost:${PORT}"
PY="$ROOT/.venv/bin/python"
TMP="$(mktemp -d /tmp/intern-walkthrough.XXXXXX)"
COOKIES="$TMP/cookies.txt"

export INTERN_DATA_DIR="${INTERN_DATA_DIR:-$TMP/data}"
export STUB_SLEEP_SCALE="${STUB_SLEEP_SCALE:-0.2}"   # quick but still streams live

cleanup() {
  [[ -n "${SERVER_PID:-}" ]] && kill "$SERVER_PID" 2>/dev/null || true
  [[ -z "${KEEP_DATA:-}" ]] && rm -rf "$TMP" || true
}
trap cleanup EXIT

jsonget() { "$PY" -c "import json,sys;d=json.load(sys.stdin);print(d$1)"; }

cd "$ROOT"
"$PY" -m uvicorn api.main:app --port "$PORT" --log-level warning &
SERVER_PID=$!

for _ in $(seq 1 50); do
  curl -sf "$BASE/api/health" >/dev/null 2>&1 && break
  sleep 0.2
done
curl -sf "$BASE/api/health" >/dev/null || { echo "FAIL: server did not start"; exit 1; }
echo "server up on :$PORT"

# ── the walkthrough, §5.9, verbatim shapes ────────────────────────────
curl -sf -c "$COOKIES" -XPOST "$BASE/api/session" -d '{"name":"Andrei","email":"a@b.co"}' \
  | jsonget "['user']['name']" | grep -qx "Andrei"
echo "1. session         OK"

JOB=$(curl -sf -b "$COOKIES" -XPOST "$BASE/api/jobs" -d @mock/brief.json | jsonget "['job_id']")
NQ=$(curl -sf -b "$COOKIES" "$BASE/api/jobs/$JOB" | jsonget "['job']['status']")
[[ "$NQ" == "questioning" ]]
echo "2. jobs            OK  job_id=$JOB"

SLUG=$(curl -sf -b "$COOKIES" -XPOST "$BASE/api/jobs/$JOB/answers" -d @mock/answers.json \
  | jsonget "['spec']['slug']")
[[ "$SLUG" == andrei-dispatch* ]]
echo "3. answers         OK  slug=$SLUG"

curl -sf -b "$COOKIES" -F role=input    -F file=@mock/manifest_2026-07-14.csv    "$BASE/api/jobs/$JOB/files" >/dev/null
curl -sf -b "$COOKIES" -F role=input    -F file=@mock/carrier_rates_2026-07.csv  "$BASE/api/jobs/$JOB/files" >/dev/null
NCOLS=$(curl -sf -b "$COOKIES" -F role=expected -F file=@mock/dispatch_summary_14.07.csv "$BASE/api/jobs/$JOB/files" \
  | jsonget "['preview']['columns']" )
[[ "$NCOLS" == *"Load (t)"* ]]
echo "4. files x3        OK  expected columns: $NCOLS"

STREAM=$(curl -sf -b "$COOKIES" -XPOST "$BASE/api/jobs/$JOB/train" | jsonget "['stream']")
[[ "$STREAM" == "/api/jobs/$JOB/events" ]]
echo "5. train (202)     OK  stream=$STREAM"

EVENTS="$TMP/events.txt"
curl -sf -b "$COOKIES" -N --max-time 60 "$BASE$STREAM" > "$EVENTS"
SCORED=$(grep -c 'attempt.scored' "$EVENTS")
grep -q '"type":"converged"' "$EVENTS"
grep -q '"outcome":"PERFECT"' "$EVENTS"
[[ "$SCORED" == 5 ]]
echo "6. events (SSE)    OK  5 attempts scored, converged PERFECT"

# replay: reconnect after convergence, full backlog comes back
curl -sf -b "$COOKIES" -N --max-time 20 "$BASE$STREAM" > "$EVENTS.replay"
[[ "$(grep -c 'attempt.scored' "$EVENTS.replay")" == 5 ]]
echo "7. events replay   OK"

STATUS=$(curl -sf -b "$COOKIES" "$BASE/api/jobs/$JOB" | jsonget "['job']['status']")
[[ "$STATUS" == "ready" ]]
echo "8. get job         OK  status=ready"

curl -sf -b "$COOKIES" "$BASE/api/jobs/$JOB/attempts/1/diff" \
  | jsonget "['wrong_cells'][0]" >/dev/null
echo "9. diff            OK"

curl -sf -b "$COOKIES" "$BASE/api/jobs/$JOB/artifact" | grep -q "pandas"
echo "10. artifact       OK  (pandas script)"

curl -sf -b "$COOKIES" "$BASE/api/jobs/$JOB/guard" | jsonget "['pass']" | grep -qx "True"
echo "11. guard          OK  pass=true"

RUN="$TMP/run.json"
curl -sf -b "$COOKIES" -F file=@mock/manifest_2026-07-17.csv -F file=@mock/carrier_rates_2026-07b.csv \
  "$BASE/api/i/$SLUG/run" > "$RUN"
DL=$(jsonget "['download_url']" < "$RUN")
MS=$(jsonget "['ms']" < "$RUN")
curl -sf -b "$COOKIES" "$BASE$DL" | head -1 | grep -q "Date,Route,Truck"
echo "12. /i/$SLUG/run   OK  ${MS}ms  download=$DL"

echo
echo "WALKTHROUGH PASS"
