#!/usr/bin/env bash
set -euo pipefail
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
VAULT=""
while [ $# -gt 0 ]; do
  case "$1" in
    --vault) VAULT="$2"; shift 2 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done
if [ -z "$VAULT" ]; then
  echo "usage: deploy.sh --vault PATH" >&2
  exit 2
fi
python3 "$HERE/deploy.py" --vault "$VAULT"
