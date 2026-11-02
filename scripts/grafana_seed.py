"""Cria a variável global e o notebook do lab pela API do Grafana. Usa só a biblioteca padrão."""

import base64
import json
import os
import pathlib
import sys
import urllib.error
import urllib.request

API = "/apis/dashboard.grafana.app/v2beta1/namespaces/default"


def post(path: str, body: dict) -> int:
    credentials = f"{os.environ['GRAFANA_USER']}:{os.environ['GRAFANA_PASSWORD']}".encode()
    request = urllib.request.Request(
        os.environ["GRAFANA_URL"] + path,
        data=json.dumps(body).encode(),
        headers={
            "Authorization": "Basic " + base64.b64encode(credentials).decode(),
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return response.status
    except urllib.error.HTTPError as error:
        # 409 significa que o recurso já existe: a operação é idempotente.
        if error.code == 409:
            return error.code
        print(f"[warn] POST {path}: {error.code} {error.read()[:300]!r}", file=sys.stderr)
        raise


def latency_variable() -> dict:
    """Limite de latência compartilhado entre dashboards, usado nos thresholds."""
    options = [{"text": value, "value": value, "selected": value == "0.5"} for value in ("0.1", "0.5", "1", "2.5")]
    return {
        "apiVersion": "dashboard.grafana.app/v2beta1",
        "kind": "Variable",
        "metadata": {"name": "latency_threshold"},
        "spec": {
            "kind": "CustomVariable",
            "spec": {
                "name": "latency_threshold",
                "label": "Latency threshold (s)",
                "query": "0.1,0.5,1,2.5",
                "current": {"text": "0.5", "value": "0.5"},
                "options": options,
                "multi": False,
                "includeAll": False,
                "hide": "dontHide",
                "skipUrlSync": False,
                "allowCustomValue": True,
            },
        },
    }


def notebook(lab: str, text: str) -> dict:
    return {
        "apiVersion": "dashboard.grafana.app/v2beta1",
        "kind": "Notebook",
        "metadata": {"name": f"{lab}-investigation"},
        "spec": {
            "title": f"{lab}: investigation",
            "tags": ["lab", lab],
            "timeSettings": {
                "from": "now-30m",
                "to": "now",
                "autoRefresh": "",
                "autoRefreshIntervals": ["10s", "30s"],
                "hideTimepicker": False,
                "fiscalYearStartMonth": 0,
            },
            "elements": {
                "guide": {
                    "kind": "CellKind",
                    "spec": {"content": {"kind": "MarkdownCellContentKind", "spec": {"text": text}}},
                }
            },
            "layout": {
                "kind": "NotebookLayout",
                "spec": {
                    "cells": [
                        {
                            "kind": "NotebookLayoutItem",
                            "spec": {"element": {"kind": "ElementReference", "name": "guide"}, "source": "markdown"},
                        }
                    ]
                },
            },
        },
    }


def main() -> int:
    lab_dir = pathlib.Path(sys.argv[1])
    try:
        post(f"{API}/variables", latency_variable())
        guide = lab_dir / "grafana-notebook.txt"
        if guide.exists():
            post(f"{API}/notebooks", notebook(lab_dir.name, guide.read_text(encoding="utf-8")))
    except OSError:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
