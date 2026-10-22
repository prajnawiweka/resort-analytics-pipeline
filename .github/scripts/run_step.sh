#!/usr/bin/env bash
# Run a pipeline command; if it fails, publish the last lines of its output as a GitHub
# annotation so the cause is visible on the run page (and through the API) without opening
# the full log. GitHub masks secret values in annotations as it does in logs.
set -uo pipefail
title="$1"; shift
log="$(mktemp)"
"$@" 2>&1 | tee "$log"
status=${PIPESTATUS[0]}
if [ "$status" -ne 0 ]; then
  message="$(grep -v "^ *\(File \|\^\|raise \|attempts = \|return \)" "$log" | tail -n 14 | sed 's/%/%25/g' | sed ':a;N;$!ba;s/\n/%0A/g')"
  echo "::error title=${title} failed::${message}"
fi
exit "$status"
