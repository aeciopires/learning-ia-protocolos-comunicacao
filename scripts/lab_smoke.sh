#!/usr/bin/env bash
# Sobe o lab, executa o cenário, confere a telemetria e derruba tudo, preservando o código de saída.
# Uso: lab_smoke.sh <número do lab>
set -uo pipefail
source "$(dirname "$0")/lib.sh"

lab="$1"
lab_dir="$(echo "labs/lab-${lab}-"*)"
cleanup() { make --no-print-directory lab-clean LAB="$lab" >/dev/null 2>&1; }
trap cleanup EXIT

make --no-print-directory lab-start LAB="$lab" || exit 1
make --no-print-directory lab-run LAB="$lab" || exit 1
if grep -q 'observability/compose.yaml' "$lab_dir/compose.yaml"; then
  PROMETHEUS_PORT="$(env_value PROMETHEUS_PORT)" JAEGER_UI_PORT="$(env_value JAEGER_UI_PORT)" \
    LOKI_PORT="$(env_value LOKI_PORT)" GRAFANA_PORT="$(env_value GRAFANA_PORT)" \
    GRAFANA_USER="$(env_value GRAFANA_ADMIN_USER)" GRAFANA_PASSWORD="$(env_value GRAFANA_ADMIN_PASSWORD)" \
    python3 "$(dirname "$0")/verify_telemetry.py" "lab-$lab" || exit 1
fi
ok "Smoke test passed: lab-$lab"
