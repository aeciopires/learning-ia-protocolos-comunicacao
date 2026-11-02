#!/usr/bin/env bash
# Confere as dependências e indica o próximo comando para cada ausência.
set -uo pipefail
source "$(dirname "$0")/lib.sh"

mise_bin="$(command -v mise || echo "$HOME/.local/bin/mise")"
missing=0

check() {
  local label="$1" hint="$2"
  shift 2
  if "$@" >/dev/null 2>&1; then
    ok "$label"
  else
    fail "$label is missing. $hint"
    missing=1
  fi
}

check make "Run: make install-dependencies" command -v make
check curl "Run: make install-dependencies" command -v curl
check git "Run: make install-dependencies" command -v git
check mise "Run: make install-dependencies" test -x "$mise_bin"
check Python "Run: make install" "$mise_bin" exec -- python --version
check uv "Run: make install" "$mise_bin" exec -- uv --version
check Node.js "Run: make install (needed by the MCP Inspector)" "$mise_bin" exec -- node --version
check "Docker CLI" "Run: make install-dependencies" command -v docker
check "Docker Compose v2" "Run: make install-dependencies" docker compose version
check "Docker buildx" "Run: make install-dependencies" docker buildx version
if [ "$(uname -s)" = Darwin ]; then
  check "Docker daemon" "Start the VM: colima start --cpu 4 --memory 8" docker info
else
  check "Docker daemon" "Start it: sudo systemctl start docker (https://docs.docker.com/engine/install/linux-postinstall/)" docker info
fi

if [ "$missing" -ne 0 ]; then
  exit 1
fi
ok "All dependencies found."
