#!/usr/bin/env bash
# Short MP3 -> text, in one round trip. Synchronous.
# shellcheck source-path=SCRIPTDIR
# shellcheck source=_common.sh
source "$(dirname "$0")/_common.sh"

FILE="${1:?usage: transcribe-instant.sh <file.mp3>}"

curl -sS -X POST "$BASE/io/v1/transcribe/instant" "${AUTH[@]}" "${FORM[@]}" \
  -F "file=@${FILE}"
echo
