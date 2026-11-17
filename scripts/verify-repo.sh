#!/usr/bin/env bash
set -euo pipefail

root="$(git rev-parse --show-toplevel)"
config="$root/.repo-model.json"
required_files=(
  "IA.md"
  "README.md"
  ".env.example"
  ".repo-model.json"
  "docs/PROJECT.md"
  "docs/architecture.md"
  "docs/getting-started.md"
  "docs/testing.md"
  "docs/sdd.md"
  ".github/workflows/ci.yml"
)

fail() {
  printf 'Repository model check failed: %s\n' "$1" >&2
  exit 1
}

for file in "${required_files[@]}"; do
  [[ -f "$root/$file" ]] || fail "missing required file: $file"
done

status="$(sed -nE 's/^[[:space:]]*"status"[[:space:]]*:[[:space:]]*"([^"]+)".*/\1/p' "$config")"
[[ "$status" == "template" || "$status" == "active" ]] || fail 'status must be "template" or "active"'

if [[ "$status" == "active" ]]; then
  for document in docs/PROJECT.md docs/architecture.md docs/getting-started.md docs/testing.md; do
    ! grep -q 'TODO' "$root/$document" || fail "$document still contains TODO"
  done

  validation_command="$(sed -nE 's/^[[:space:]]*"validation_command"[[:space:]]*:[[:space:]]*"(.*)"[,]?$/\1/p' "$config")"
  [[ -n "$validation_command" ]] || fail 'active repositories need validation_command'
fi

if [[ -n "${GITHUB_OUTPUT:-}" ]]; then
  printf 'active=%s\n' "$([[ "$status" == "active" ]] && printf true || printf false)" >> "$GITHUB_OUTPUT"
fi

printf 'Repository model check passed (%s).\n' "$status"
