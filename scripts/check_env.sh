#!/usr/bin/env bash
# Bloqueia a subida de um lab quando falta um segredo exigido por ele.
# O Compose só detecta valores ausentes: um CHANGEME passaria despercebido sem esta checagem.
# Uso: check_env.sh <diretório do lab>
set -euo pipefail
source "$(dirname "$0")/lib.sh"

lab_dir="$1"
if [ ! -f .env ]; then
  fail ".env not found. Run: make secret"
  exit 1
fi

status=0
# O arquivo required-env do lab lista um segredo por linha; comentários são ignorados.
if [ -f "$lab_dir/required-env" ]; then
  while read -r name; do
    case "$name" in '' | \#*) continue ;; esac
    value="$(env_value "$name")"
    if [ -z "$value" ] || [ "$value" = CHANGEME ]; then
      fail "$name is not set in .env. Run: make secret"
      status=1
    fi
  done <"$lab_dir/required-env"
fi

# Um provedor real de LLM exige o modelo e a chave correspondente.
provider="$(env_value LLM_PROVIDER)"
case "${provider:-fake}" in
  fake) ;;
  anthropic | openai | gemini)
    key_name="$(echo "$provider" | tr '[:lower:]' '[:upper:]')_API_KEY"
    key="$(env_value "$key_name")"
    if [ -z "$key" ] || [ "$key" = CHANGEME ]; then
      fail "LLM_PROVIDER=$provider requires $key_name in .env"
      status=1
    fi
    if [ -z "$(env_value LLM_MODEL)" ]; then
      fail "LLM_PROVIDER=$provider requires LLM_MODEL in .env"
      status=1
    fi
    ;;
  *)
    fail "Invalid LLM_PROVIDER: $provider (use fake, anthropic, openai or gemini)"
    status=1
    ;;
esac
exit "$status"
