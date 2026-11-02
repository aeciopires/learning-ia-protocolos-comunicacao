#!/usr/bin/env bash
# Lista os labs a partir da primeira linha de cada README: número, nome e documento.
set -euo pipefail

printf '%-4s %-30s %-6s %s\n' LAB NAME STACK DESCRIPTION
for dir in labs/lab-*; do
  [ -d "$dir" ] || continue
  name="$(basename "$dir")"
  number="$(echo "$name" | cut -d- -f2)"
  stack=no
  if grep -q 'observability/compose.yaml' "$dir/compose.yaml"; then stack=yes; fi
  summary="$(grep -m1 '^description' "$dir/pyproject.toml" | cut -d'"' -f2)"
  printf '%-4s %-30s %-6s %s\n' "$number" "${name#lab-"$number"-}" "$stack" "$summary"
done
