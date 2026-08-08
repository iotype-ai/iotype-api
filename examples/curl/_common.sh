#!/usr/bin/env bash
# Shared setup for every example. Source this, don't run it.
#
# shellcheck disable=SC2034
# The variables below are consumed by the scripts that source this file, so
# shellcheck cannot see their use when checking this file on its own.
set -euo pipefail

: "${IOTYPE_TOKEN:?Set IOTYPE_TOKEN first:  export IOTYPE_TOKEN='your-token'}"

BASE="https://iotype.com"

AUTH=(-H "Authorization: Bearer ${IOTYPE_TOKEN}")
JSON=(-H "Content-Type: application/json" -H "Accept: application/json" -H "X-Requested-With: XMLHttpRequest")
FORM=(-H "Accept: application/json" -H "X-Requested-With: XMLHttpRequest")
