#!/usr/bin/env bash
# Poll a uuid until the requested process carries a result.
# Backoff: 5s doubling to a 60s ceiling. Overall deadline: 30 minutes.
# shellcheck source-path=SCRIPTDIR
# shellcheck source=_common.sh
source "$(dirname "$0")/_common.sh"

UUID="${1:?usage: poll.sh <uuid> [process-type]}"
WANT="${2:-}"
BACKOFF=5
DEADLINE=$(( $(date +%s) + 1800 ))

while :; do
  BODY=$(curl -sS -X POST "$BASE/io/v1/file/track" "${AUTH[@]}" "${JSON[@]}" \
          -d "$(jq -nc --arg u "$UUID" '{uuid:$u}')")

  RESULT=$(echo "$BODY" | jq -r --arg w "$WANT" '
      .file.processes[]?
      | select(($w == "") or (.type == $w))
      | select(.result != null)
      | .result' | head -1)

  if [ -n "$RESULT" ]; then echo "$RESULT"; exit 0; fi

  if [ "$(date +%s)" -gt "$DEADLINE" ]; then
    echo "timed out after 30 minutes; uuid $UUID is still processing" >&2; exit 1
  fi

  sleep "$BACKOFF"
  BACKOFF=$(( BACKOFF * 2 ))
  if [ "$BACKOFF" -gt 60 ]; then BACKOFF=60; fi
done
