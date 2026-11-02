// Registra o SDK do OpenTelemetry antes da aplicação. Sem isto, os spans do MCP não têm destino.
import { NodeSDK } from "@opentelemetry/sdk-node";
import { BatchLogRecordProcessor } from "@opentelemetry/sdk-logs";
import { PeriodicExportingMetricReader } from "@opentelemetry/sdk-metrics";
import { BatchSpanProcessor } from "@opentelemetry/sdk-trace";
import { OTLPLogExporter } from "@opentelemetry/exporter-logs-otlp-http";
import { OTLPMetricExporter } from "@opentelemetry/exporter-metrics-otlp-http";
import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-http";

const sdk = new NodeSDK({
  spanProcessors: [new BatchSpanProcessor({ exporter: new OTLPTraceExporter() })],
  metricReaders: [
    new PeriodicExportingMetricReader({
      exporter: new OTLPMetricExporter(),
      exportIntervalMillis: 5000,
    }),
  ],
  logRecordProcessors: [new BatchLogRecordProcessor({ exporter: new OTLPLogExporter() })],
});
sdk.start();
process.on("SIGTERM", () => void sdk.shutdown().finally(() => process.exit(0)));
