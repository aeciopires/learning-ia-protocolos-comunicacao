#!/usr/bin/env bash
# Compara as imagens fixadas da stack com as releases mais recentes. Não altera nada.
set -uo pipefail
source "$(dirname "$0")/lib.sh"

compose=labs/observability/compose.yaml
compare() {
  local label="$1" pattern="$2" repo="$3" current latest
  current="$(grep -E "image: ${pattern}:" "$compose" | sed -E 's/.*:v?//' | head -1)"
  latest="$(curl -fsS -m 20 "https://api.github.com/repos/${repo}/releases/latest" \
    | python3 -c 'import json,sys; print(json.load(sys.stdin)["tag_name"].lstrip("v"))' 2>/dev/null || echo unknown)"
  if [ "$latest" = unknown ]; then
    warn "$label: could not check (GitHub API unavailable); pinned $current"
  elif [ "$current" = "$latest" ]; then
    ok "$label $current"
  else
    warn "$label: pinned $current, latest $latest"
  fi
}
compare Grafana grafana/grafana grafana/grafana
compare Prometheus prom/prometheus prometheus/prometheus
compare Jaeger cr.jaegertracing.io/jaegertracing/jaeger jaegertracing/jaeger
compare Loki grafana/loki grafana/loki
compare "OpenTelemetry Collector" otel/opentelemetry-collector-contrib open-telemetry/opentelemetry-collector-releases
