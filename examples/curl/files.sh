#!/usr/bin/env bash
# List every file this token has submitted. POST with an empty JSON body.
# shellcheck source=examples/curl/_common.sh
source "$(dirname "$0")/_common.sh"

curl -sS -X POST "$BASE/io/v1/files" "${AUTH[@]}" "${JSON[@]}" -d '{}' | jq
