#!/usr/bin/env bash
# Cria no Grafana recursos sem provisionamento por arquivo: variável global e notebook do lab.
# As APIs estão em preview ou são experimentais, então uma falha aqui só gera um aviso.
# Uso: grafana_seed.sh <diretório do lab>
set -uo pipefail
source "$(dirname "$0")/lib.sh"

lab_dir="$1"
grep -q 'observability/compose.yaml' "$lab_dir/compose.yaml" || exit 0
if ! GRAFANA_URL="http://localhost:$(env_value GRAFANA_PORT)" \
  GRAFANA_USER="$(env_value GRAFANA_ADMIN_USER)" \
  GRAFANA_PASSWORD="$(env_value GRAFANA_ADMIN_PASSWORD)" \
  python3 "$(dirname "$0")/grafana_seed.py" "$lab_dir"; then
  warn "Could not create the shared variable or notebook. The dashboards do not depend on them."
fi
