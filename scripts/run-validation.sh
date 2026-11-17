#!/usr/bin/env bash
set -euo pipefail

root="$(git rev-parse --show-toplevel)"
config="$root/.repo-model.json"
command="$(sed -nE 's/^[[:space:]]*"validation_command"[[:space:]]*:[[:space:]]*"(.*)"[,]?$/\1/p' "$config")"

if [[ -z "$command" ]]; then
  printf 'validation_command is required for active repositories.\n' >&2
  exit 1
fi

cd "$root"
exec bash -lc "$command"
