#!/usr/bin/env bash
# Mostra as URLs do lab, respeitando as portas configuradas no .env.
# Uso: lab_urls.sh <diretório do lab>
set -euo pipefail
source "$(dirname "$0")/lib.sh"

lab_dir="$1"
echo ""
ok "$(basename "$lab_dir") is up"
if grep -q 'observability/compose.yaml' "$lab_dir/compose.yaml"; then
  echo "  Grafana     http://localhost:$(env_value GRAFANA_PORT)  (user: $(env_value GRAFANA_ADMIN_USER); password in .env)"
  echo "  Prometheus  http://localhost:$(env_value PROMETHEUS_PORT)"
  echo "  Jaeger      http://localhost:$(env_value JAEGER_UI_PORT)"
  echo "  Loki        http://localhost:$(env_value LOKI_PORT)/ready"
fi
if grep -q 'LAB_SERVICE_PORT' "$lab_dir/compose.yaml"; then
  echo "  Service     http://localhost:$(env_value LAB_SERVICE_PORT)"
fi
echo ""
echo "  Next: make lab-run LAB=$(basename "$lab_dir" | cut -d- -f2)"
