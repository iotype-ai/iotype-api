#!/usr/bin/env bash
# Fetch the current state of one file.
# shellcheck source=examples/curl/_common.sh
source "$(dirname "$0")/_common.sh"

UUID="${1:?usage: track.sh <uuid>}"

curl -sS -X POST "$BASE/io/v1/file/track" "${AUTH[@]}" "${JSON[@]}" \
  -d "$(jq -nc --arg u "$UUID" '{uuid:$u}')" | jq
