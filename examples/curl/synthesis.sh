#!/usr/bin/env bash
# Text to speech. Returns { "url": "...mp3" }. Synchronous.
# shellcheck source=examples/curl/_common.sh
source "$(dirname "$0")/_common.sh"

TEXT="${1:-سلام! امروز هوا بسیار عالی است.}"
SPEAKER="${2:-tanaz}"     # behrooz mehran farshid sara mitra siavash shirin kaveh amir tanaz mahsa
TONE="${3:-general}"      # general | formal

RESP=$(curl -sS -X POST "$BASE/io/v1/synthesis" "${AUTH[@]}" "${JSON[@]}" \
  -d "$(jq -nc --arg t "$TONE" --arg s "$SPEAKER" --arg x "$TEXT" \
        '{tone:$t, speaker:$s, text:$x}')")

echo "$RESP"
URL=$(echo "$RESP" | jq -r '.url // empty')
if [ -n "$URL" ]; then
  curl -sS -o narration.mp3 "$URL"
  echo "saved -> narration.mp3"
fi
