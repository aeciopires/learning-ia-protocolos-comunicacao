"""Gera um dashboard por lab, com métricas, traces e logs ligados pelo trace_id.

Rode com `make dashboards`. Os arquivos gerados são versionados para o Grafana provisionar.
"""

import json
import pathlib
from dataclasses import dataclass, field

OUTPUT = pathlib.Path("labs/observability/grafana/dashboards")
PROM = {"type": "prometheus", "uid": "prometheus"}
LOKI = {"type": "loki", "uid": "loki"}
JAEGER = {"type": "jaeger", "uid": "jaeger"}


@dataclass
class Panel:
    title: str
    query: str
    legend: str = ""
    unit: str = "short"
    kind: str = "timeseries"
    description: str = ""


@dataclass
class Dashboard:
    lab: str
    title: str
    question: str
    panels: list[Panel] = field(default_factory=list)


def scope(extra: str = "") -> str:
    """Filtro comum: o dashboard mostra somente a telemetria do lab atual."""
    suffix = f",{extra}" if extra else ""
    return f'{{lab_id="%LAB%"{suffix}}}'


def rate(metric: str, by: str, extra: str = "") -> str:
    return f"sum by ({by}) (rate({metric}{scope(extra)}[1m]))"


def p95(by: str = "operation") -> str:
    return f"histogram_quantile(0.95, sum by (le, {by}) (rate(lab_operation_duration_seconds_bucket{scope()}[1m])))"


def common_panels() -> list[Panel]:
    return [
        Panel("Operations per second", rate("lab_operations_total", "operation, outcome"), "{{operation}} {{outcome}}"),
        Panel(
            "Latency p95 by operation",
            p95(),
            "{{operation}}",
            "s",
            description="Pontos com exemplar abrem o trace que gerou a medição.",
        ),
    ]


DASHBOARDS = [
    Dashboard(
        "lab-03",
        "Lab 03: camadas",
        "Quanto custa cada camada?",
        [
            Panel("Latency p95 by layer", p95("layer"), "{{layer}}", "s"),
            Panel("Calls by layer", rate("lab_operations_total", "layer"), "{{layer}}"),
        ],
    ),
    Dashboard(
        "lab-04",
        "Lab 04: host, client e server",
        "O circuit breaker protegeu o host?",
        [
            Panel(
                "Circuit breaker state (0 closed, 1 half-open, 2 open)",
                f"max by (server) (lab_circuit_breaker_state{scope()})",
                "{{server}}",
                kind="stat",
            ),
            Panel(
                "Calls by server and outcome", rate("lab_operations_total", "server, outcome"), "{{server}} {{outcome}}"
            ),
            Panel("Calls blocked by the breaker", rate("lab_circuit_breaker_blocked_total", "server"), "{{server}}"),
        ],
    ),
    Dashboard(
        "lab-05",
        "Lab 05: primitivos",
        "Como os primitivos são usados?",
        [
            Panel("Calls by primitive", rate("lab_operations_total", "primitive"), "{{primitive}}"),
        ],
    ),
    Dashboard(
        "lab-06",
        "Lab 06: prompts e inferência",
        "Quanto custa a inferência?",
        [
            Panel(
                "LLM tokens by direction",
                rate("lab_llm_tokens_total", "provider, direction"),
                "{{provider}} {{direction}}",
            ),
            Panel("Recursion depth refused", f"sum(lab_recursion_refused_total{scope()})", kind="stat"),
        ],
    ),
    Dashboard(
        "lab-07",
        "Lab 07: ecossistema",
        "Qual a diferença entre os servers?",
        [
            Panel("Latency p95 by server", p95("server"), "{{server}}", "s"),
            Panel("Calls by server", rate("lab_operations_total", "server, outcome"), "{{server}} {{outcome}}"),
            Panel(
                "Capabilities by server",
                f"max by (server, primitive) (lab_server_capabilities{scope()})",
                "{{server}} {{primitive}}",
                kind="stat",
            ),
        ],
    ),
    Dashboard(
        "lab-08",
        "Lab 08: SDK em TypeScript",
        "O cancelamento libera recursos?",
        [
            Panel(
                "Cancellations", f"sum by (operation) (lab_cancellations_total{scope()})", "{{operation}}", kind="stat"
            ),
        ],
    ),
    Dashboard(
        "lab-09",
        "Lab 09: Finance Admin",
        "A política financeira está funcionando?",
        [
            Panel("Bonus refusals by reason", rate("lab_bonus_rejections_total", "reason"), "{{reason}}"),
            Panel("Bonus granted (BRL)", f"sum(lab_bonus_granted_total{scope()})", unit="currencyBRL", kind="stat"),
            Panel("Batch items processed", f"sum(lab_batch_items_total{scope()})", kind="stat"),
        ],
    ),
    Dashboard(
        "lab-10",
        "Lab 10: injeção e dados adulterados",
        "Os ataques foram contidos?",
        [
            Panel(
                "Blocked content by reason",
                rate("lab_guard_blocked_total", "reason, pipeline"),
                "{{pipeline}} {{reason}}",
            ),
            Panel(
                "Dangerous actions executed by pipeline",
                f"sum by (pipeline) (lab_dangerous_actions_total{scope()})",
                "{{pipeline}}",
                kind="stat",
            ),
        ],
    ),
    Dashboard(
        "lab-11",
        "Lab 11: OAuth",
        "Quem acessou o quê?",
        [
            Panel(
                "Authorization decisions",
                rate("lab_authorization_decisions_total", "decision, reason"),
                "{{decision}} {{reason}}",
            ),
        ],
    ),
    Dashboard(
        "lab-12",
        "Lab 12: produção",
        "O deploy prova suas propriedades?",
        [
            Panel("Edge decisions", rate("lab_edge_decisions_total", "decision"), "{{decision}}"),
        ],
    ),
    Dashboard(
        "lab-13",
        "Lab 13: Tasks do A2A",
        "Como as Tasks evoluem?",
        [
            Panel("Task transitions by state", rate("lab_task_transitions_total", "state"), "{{state}}"),
        ],
    ),
    Dashboard(
        "lab-14",
        "Lab 14: padrões A2A",
        "Qual padrão custa mais?",
        [
            Panel("Latency p95 by pattern", p95("pattern"), "{{pattern}}", "s"),
            Panel(
                "Partial failures",
                f"sum by (pattern) (lab_partial_failures_total{scope()})",
                "{{pattern}}",
                kind="stat",
            ),
        ],
    ),
    Dashboard(
        "lab-15",
        "Lab 15: integrador",
        "O fluxo ponta a ponta está saudável?",
        [
            Panel("Rate by service", rate("lab_operations_total", "service_name"), "{{service_name}}"),
            Panel(
                "Error rate by service",
                rate("lab_operations_total", "service_name", 'outcome="error"'),
                "{{service_name}}",
            ),
            Panel("LLM tokens", rate("lab_llm_tokens_total", "direction"), "{{direction}}"),
        ],
    ),
]


def metric_panel(panel: Panel, panel_id: int, x: int, y: int, lab: str) -> dict:
    target = {
        "datasource": PROM,
        "expr": panel.query.replace("%LAB%", lab),
        "legendFormat": panel.legend or "__auto",
        "refId": "A",
        "range": True,
        # Exemplars são o ponto de partida da correlação entre métrica e trace.
        "exemplar": panel.kind == "timeseries",
    }
    defaults: dict = {"unit": panel.unit}
    if panel.unit == "s":
        # Variável em threshold (Grafana 13.3): o limite vem da variável global latency_threshold.
        defaults["thresholds"] = {
            "mode": "absolute",
            "steps": [
                {"color": "green", "value": None},
                {"color": "red", "value": 0.5, "valueExpr": "$latency_threshold"},
            ],
        }
        defaults["custom"] = {"thresholdsStyle": {"mode": "line"}}
    return {
        "id": panel_id,
        "type": panel.kind,
        "title": panel.title,
        "description": panel.description,
        "datasource": PROM,
        "gridPos": {"h": 8, "w": 12, "x": x, "y": y},
        "fieldConfig": {"defaults": defaults, "overrides": []},
        "options": {},
        "targets": [target],
    }


def build(dashboard: Dashboard) -> dict:
    panels = [
        {
            "id": 1,
            "type": "text",
            "title": "",
            "gridPos": {"h": 3, "w": 24, "x": 0, "y": 0},
            "options": {
                "mode": "markdown",
                "content": f"### {dashboard.question}\n\n"
                f"Rode `make lab-run LAB={dashboard.lab[-2:]}` para gerar dados. "
                "Em um gráfico, clique em um exemplar para abrir o trace; no trace, abra os logs do span. "
                "Para buscar traces por serviço, use a interface do Jaeger.",
            },
        }
    ]
    y, next_id = 3, 2
    specs = [*dashboard.panels, *common_panels()]
    for index, panel in enumerate(specs):
        panels.append(metric_panel(panel, next_id, 0 if index % 2 == 0 else 12, y, dashboard.lab))
        next_id += 1
        if index % 2 == 1:
            y += 8
    if len(specs) % 2 == 1:
        y += 8
    panels.append(
        {
            "id": next_id,
            "type": "nodegraph",
            "title": "Service dependencies",
            "description": "Grafana não busca traces no Jaeger 2.22; use exemplars, logs ou a interface do Jaeger.",
            "datasource": JAEGER,
            "gridPos": {"h": 9, "w": 12, "x": 0, "y": y},
            "targets": [{"datasource": JAEGER, "queryType": "dependencyGraph", "refId": "A"}],
        }
    )
    panels.append(
        {
            "id": next_id + 1,
            "type": "logs",
            "title": "Logs",
            "datasource": LOKI,
            "gridPos": {"h": 9, "w": 12, "x": 12, "y": y},
            "options": {"showTime": True, "wrapLogMessage": True, "enableLogDetails": True, "sortOrder": "Descending"},
            "targets": [
                {
                    "datasource": LOKI,
                    "expr": '{service_name=~"$service"}',
                    "queryType": "range",
                    "refId": "A",
                }
            ],
        }
    )
    return {
        "uid": dashboard.lab,
        "title": dashboard.title,
        "tags": ["lab", dashboard.lab],
        "schemaVersion": 42,
        "editable": True,
        "refresh": "10s",
        "time": {"from": "now-30m", "to": "now"},
        "timezone": "browser",
        "templating": {
            "list": [
                {
                    "name": "service",
                    "label": "Service",
                    "type": "query",
                    "datasource": PROM,
                    "query": {
                        "query": f'label_values(lab_operations_total{{lab_id="{dashboard.lab}"}}, service_name)',
                        "refId": "service",
                    },
                    "refresh": 2,
                    "includeAll": False,
                    "multi": False,
                    "sort": 1,
                }
            ]
        },
        "panels": panels,
    }


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for dashboard in DASHBOARDS:
        path = OUTPUT / f"{dashboard.lab}.json"
        path.write_text(json.dumps(build(dashboard), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"[ ok ] {path}")


if __name__ == "__main__":
    main()
