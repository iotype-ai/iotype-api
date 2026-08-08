#!/usr/bin/env bash
# Long MP3 -> text. ASYNCHRONOUS: returns a uuid, then polls until done.
# shellcheck source-path=SCRIPTDIR
# shellcheck source=_common.sh
source "$(dirname "$0")/_common.sh"

FILE="${1:?usage: transcribe.sh <file.mp3> [lang] [summarize]}"
LANG_="${2:-fa}"          # fa | en | ar
SUMMARIZE="${3:-false}"   # true | false

UUID=$(curl -sS -X POST "$BASE/io/v1/transcribe" "${AUTH[@]}" "${FORM[@]}" \
  -F "file=@${FILE}" -F "source_lang=${LANG_}" -F "should_summarize=${SUMMARIZE}" \
  | jq -r '.file.uuid')

echo "uuid: $UUID"
exec "$(dirname "$0")/poll.sh" "$UUID" transcribe
