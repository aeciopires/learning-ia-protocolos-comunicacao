"""Confere a telemetria de um lab em execução: métricas, exemplars, traces, logs e correlação."""

import base64
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import UTC, datetime, timedelta


def get(url: str, headers: dict[str, str] | None = None) -> dict:
    request = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(request, timeout=15) as response:
        return json.load(response)


def prometheus(path: str, **params: str) -> list:
    query = urllib.parse.urlencode(params)
    return get(f"http://localhost:{os.environ['PROMETHEUS_PORT']}/api/v1/{path}?{query}")["data"]


def wait_for(description: str, check, attempts: int = 12):
    for _ in range(attempts):
        result = check()
        if result:
            print(f"[ ok ] {description}")
            return result
        time.sleep(5)
    print(f"[fail] {description}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    lab = sys.argv[1]
    now = int(time.time())
    wait_for(
        "metrics reached Prometheus",
        lambda: prometheus("query", query=f'{{__name__=~"lab_.*",lab_id="{lab}"}}'),
    )
    exemplars = wait_for(
        "exemplars reached Prometheus",
        lambda: prometheus(
            "query_exemplars",
            query=f'{{__name__=~"lab_.*_bucket",lab_id="{lab}"}}',
            start=str(now - 900),
            end=str(int(time.time()) + 60),
        ),
    )
    trace_id = exemplars[0]["exemplars"][-1]["labels"]["trace_id"]

    def trace_in_jaeger() -> bool:
        try:
            return bool(get(f"http://localhost:{os.environ['JAEGER_UI_PORT']}/api/v3/traces/{trace_id}"))
        except OSError:
            return False

    wait_for(f"exemplar trace {trace_id} found in Jaeger", trace_in_jaeger)

    def logs() -> list:
        start = int((datetime.now(UTC) - timedelta(minutes=15)).timestamp()) * 10**9
        params = urllib.parse.urlencode({"query": f'{{service_name=~"{lab}-.*"}}', "start": str(start), "limit": "50"})
        data = get(f"http://localhost:{os.environ['LOKI_PORT']}/loki/api/v1/query_range?{params}")
        return data["data"]["result"]

    streams = wait_for("logs reached Loki", logs)
    if any(stream["stream"].get("trace_id") for stream in streams):
        print("[ ok ] logs carry trace_id")
    else:
        print("[fail] logs do not carry trace_id", file=sys.stderr)
        sys.exit(1)

    token = base64.b64encode(f"{os.environ['GRAFANA_USER']}:{os.environ['GRAFANA_PASSWORD']}".encode()).decode()
    auth = {"Authorization": f"Basic {token}"}
    base = f"http://localhost:{os.environ['GRAFANA_PORT']}"
    for uid in ("prometheus", "jaeger", "loki"):
        health = get(f"{base}/api/datasources/uid/{uid}/health", auth)
        if str(health.get("status")).upper() != "OK":
            print(f"[fail] Grafana datasource {uid}: {health}", file=sys.stderr)
            sys.exit(1)
    print("[ ok ] Grafana datasources are healthy")
    dashboards = get(f"{base}/api/search?type=dash-db", auth)
    if not any(item["uid"] == lab for item in dashboards):
        print(f"[fail] dashboard {lab} is not provisioned", file=sys.stderr)
        sys.exit(1)
    print(f"[ ok ] dashboard {lab} is provisioned")

    # Um painel sem dados costuma indicar nome de métrica errado: confere cada métrica usada.
    panels = get(f"{base}/api/dashboards/uid/{lab}", auth)["dashboard"]["panels"]
    used = {
        name
        for panel in panels
        for target in panel.get("targets", [])
        for name in re.findall(r"lab_[a-z0-9_]+", target.get("expr", ""))
    }
    expected = used - {"lab_id"}

    def missing_metrics() -> set[str]:
        return expected - set(prometheus("label/__name__/values"))

    # Os serviços exportam a cada 5 s, então a última métrica pode chegar depois das demais.
    for _ in range(12):
        missing = missing_metrics()
        if not missing:
            break
        time.sleep(5)
    if missing:
        print(f"[fail] dashboard uses metrics without data: {sorted(missing)}", file=sys.stderr)
        sys.exit(1)
    print(f"[ ok ] all {len(used - {'lab_id'})} dashboard metrics have data")


if __name__ == "__main__":
    main()
