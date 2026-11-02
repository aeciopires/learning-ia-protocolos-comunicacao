"""Configura traces, métricas e logs por OTLP, em um único ponto.

Os três sinais compartilham o mesmo `service.name` e, nos logs, o mesmo `trace_id`.
É isso que permite ao Grafana navegar entre métricas, traces e logs.
"""

import json
import logging
import sys
import time
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime

from opentelemetry import metrics, trace
from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.logging.handler import LoggingHandler
from opentelemetry.metrics import Meter
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import Status, StatusCode, Tracer

from labs_common.settings import LabSettings

METRIC_EXPORT_INTERVAL_MS = 5_000
# Buckets em segundos: os padrões do OpenTelemetry assumem milissegundos.
DURATION_BUCKETS = [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30]


class JsonFormatter(logging.Formatter):
    """Escreve uma linha JSON por evento, com o trace atual para correlação."""

    def format(self, record: logging.LogRecord) -> str:
        span_context = trace.get_current_span().get_span_context()
        entry = {
            "time": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if span_context.is_valid:
            entry["trace_id"] = format(span_context.trace_id, "032x")
            entry["span_id"] = format(span_context.span_id, "016x")
        if record.exc_info:
            entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(entry)


def _configure_stderr_logging(level: str) -> None:
    # Em stdio, stdout é o canal do protocolo: os logs precisam ir para stderr.
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(level)
    # O cliente HTTP registra cada exportação OTLP, o que só geraria ruído nos logs do lab.
    for noisy in ("httpx", "httpx2", "httpcore"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def setup_telemetry(service_name: str, settings: LabSettings | None = None) -> None:
    """Ativa os três sinais. Com OTEL_SDK_DISABLED=true, restam só os logs em stderr.

    Os providers registram o próprio flush na saída do processo, o que preserva a última
    exportação de processos curtos, como os cenários.
    """
    config = settings or LabSettings()
    _configure_stderr_logging(config.log_level)
    if config.otel_sdk_disabled:
        return

    endpoint = config.otel_exporter_otlp_endpoint.rstrip("/")
    resource = Resource.create({"service.name": service_name, "lab.id": config.lab_id})

    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=f"{endpoint}/v1/traces")))
    trace.set_tracer_provider(tracer_provider)

    meter_provider = MeterProvider(
        resource=resource,
        metric_readers=[
            PeriodicExportingMetricReader(
                OTLPMetricExporter(endpoint=f"{endpoint}/v1/metrics"),
                export_interval_millis=METRIC_EXPORT_INTERVAL_MS,
            )
        ],
    )
    metrics.set_meter_provider(meter_provider)

    logger_provider = LoggerProvider(resource=resource)
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(OTLPLogExporter(endpoint=f"{endpoint}/v1/logs")))
    set_logger_provider(logger_provider)
    logging.getLogger().addHandler(LoggingHandler(logger_provider=logger_provider))


def tracer(name: str = "labs") -> Tracer:
    return trace.get_tracer(name)


def meter(name: str = "labs") -> Meter:
    return metrics.get_meter(name)


class OperationMetrics:
    """Mede operações de um lab: total por resultado e duração, com exemplars do trace atual."""

    def __init__(self) -> None:
        current = meter()
        self._total = current.create_counter("lab.operations", description="Operations by name and outcome")
        self._duration = current.create_histogram(
            "lab.operation.duration",
            unit="s",
            description="Operation duration",
            explicit_bucket_boundaries_advisory=DURATION_BUCKETS,
        )

    @contextmanager
    def observe(self, operation: str, **attributes: str) -> Iterator[None]:
        """Registra uma operação. O histograma é gravado dentro do span, o que gera o exemplar."""
        started = time.perf_counter()
        outcome = "success"
        try:
            yield
        except Exception:
            outcome = "error"
            raise
        finally:
            labels = {"operation": operation, "outcome": outcome, **attributes}
            self._total.add(1, labels)
            self._duration.record(time.perf_counter() - started, labels)


@contextmanager
def scenario_span(name: str) -> Iterator[None]:
    """Agrupa um passo do cenário em um span e imprime o trace_id para consulta no Jaeger."""
    with tracer("scenario").start_as_current_span(name) as span:
        trace_id = format(span.get_span_context().trace_id, "032x")
        print(f"\n== {name}\n   trace_id={trace_id}", flush=True)
        try:
            yield
        except Exception as error:
            span.set_status(Status(StatusCode.ERROR, str(error)))
            raise
