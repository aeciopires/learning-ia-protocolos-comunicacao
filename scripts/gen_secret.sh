#!/usr/bin/env bash
# Cria o .env a partir do .env.example e gera os segredos locais ainda marcados como CHANGEME.
# Chaves de terceiros, como as de LLM e do GitHub, nunca são geradas.
set -euo pipefail
source "$(dirname "$0")/lib.sh"

GENERATED=(GRAFANA_ADMIN_PASSWORD POSTGRES_PASSWORD KEYCLOAK_ADMIN_PASSWORD KEYCLOAK_DEMO_PASSWORD MCP_BEARER_TOKEN)

if [ ! -f .env ]; then
  cp .env.example .env
  chmod 600 .env
  info "Created .env from .env.example"
fi

for name in "${GENERATED[@]}"; do
  if [ "$(env_value "$name")" = CHANGEME ]; then
    value="$(openssl rand -hex 24)"
    tmp="$(mktemp)"
    sed "s|^${name}=.*|${name}=${value}|" .env >"$tmp"
    cat "$tmp" >.env
    rm -f "$tmp"
    ok "Generated $name"
  fi
done
