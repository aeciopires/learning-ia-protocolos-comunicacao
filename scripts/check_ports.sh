#!/usr/bin/env bash
# Detecta portas ocupadas antes de subir o lab e indica a variável que muda cada uma.
# Uso: check_ports.sh <arquivo compose> <projeto compose>
set -euo pipefail
source "$(dirname "$0")/lib.sh"

compose_file="$1"
project="$2"
status=0

ports="$(docker compose --env-file .env -f "$compose_file" config --format json \
  | python3 -c 'import json,sys
for s in json.load(sys.stdin)["services"].values():
    if "scenario" in s.get("profiles", []): continue
    for p in s.get("ports", []): print(p["published"])' | sort -u)"

for port in $ports; do
  if (exec 3<>"/dev/tcp/127.0.0.1/$port") 2>/dev/null; then
    # A porta pode pertencer ao próprio lab, quando ele já está de pé.
    if ! docker ps --filter "label=com.docker.compose.project=$project" --format '{{.Ports}}' | grep -q ":$port->"; then
      fail "Port $port is in use. Change the matching *_PORT variable in .env or stop the other process."
      status=1
    fi
  fi
done
exit "$status"
