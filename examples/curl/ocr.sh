#!/usr/bin/env bash
# PDF or JPG -> text. ASYNCHRONOUS: returns a uuid, then polls until done.
# shellcheck source-path=SCRIPTDIR
# shellcheck source=_common.sh
source "$(dirname "$0")/_common.sh"

FILE="${1:?usage: ocr.sh <file.pdf|file.jpg> [summarize]}"
SUMMARIZE="${2:-false}"

UUID=$(curl -sS -X POST "$BASE/io/v1/ocr" "${AUTH[@]}" "${FORM[@]}" \
  -F "file=@${FILE}" -F "should_summarize=${SUMMARIZE}" \
  | jq -r '.file.uuid')

echo "uuid: $UUID"
exec "$(dirname "$0")/poll.sh" "$UUID" ocr
