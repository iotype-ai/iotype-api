#!/usr/bin/env bash
# Translate text between fa / en / ar. Synchronous.
source "$(dirname "$0")/_common.sh"

TEXT="${1:-سلام! امروز هوا بسیار عالی است.}"
FROM="${2:-fa}"
TO="${3:-en}"

curl -sS -X POST "$BASE/io/v1/translate" "${AUTH[@]}" "${JSON[@]}" \
  -d "$(jq -nc --arg s "$FROM" --arg d "$TO" --arg t "$TEXT" \
        '{source_lang:$s, destination_lang:$d, text:$t}')"
echo
