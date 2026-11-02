// Server MCP com o SDK v2 em TypeScript: as peças são server, schema e transport.
import { createServer } from "node:http";
import { toNodeHandler } from "@modelcontextprotocol/node";
import { createMcpHandler, McpServer } from "@modelcontextprotocol/server";
import { context, logs, metrics, propagation, SeverityNumber, SpanKind, SpanStatusCode, trace } from "@opentelemetry/api";
import pg from "pg";
import * as z from "zod/v4";

const pool = new pg.Pool({
  host: process.env.POSTGRES_HOST ?? "postgres",
  database: "lab",
  user: "lab",
  password: process.env.POSTGRES_PASSWORD,
});

const meter = metrics.getMeter("lab-08");
const operations = meter.createCounter("lab.operations", { description: "Operations by name and outcome" });
const cancellations = meter.createCounter("lab.cancellations", { description: "Operations canceled by the client" });
const duration = meter.createHistogram("lab.operation.duration", {
  unit: "s",
  description: "Operation duration",
  advice: { explicitBucketBoundaries: [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30] },
});
const logger = logs.getLogger("lab-08");

function log(severityNumber: SeverityNumber, body: string): void {
  logger.emit({ severityNumber, body });
  // Em stdio, stdout seria o canal do protocolo; por isso os logs locais vão para stderr.
  console.error(body);
}

// O client envia o traceparent em params._meta. A release 2.4.0 do SDK não cria estes spans, então
// o server abre o seu e continua o trace do client, o que junta Python e TypeScript no Jaeger.
async function observe<T>(operation: string, meta: Record<string, unknown> | undefined, run: () => Promise<T>): Promise<T> {
  const parent = propagation.extract(context.active(), meta ?? {});
  return trace.getTracer("lab-08").startActiveSpan(
    `tools/call ${operation}`,
    { kind: SpanKind.SERVER },
    parent,
    async (span) => {
      const started = performance.now();
      let outcome = "success";
      try {
        return await run();
      } catch (error) {
        outcome = "error";
        span.setStatus({ code: SpanStatusCode.ERROR, message: String(error) });
        throw error;
      } finally {
        operations.add(1, { operation, outcome });
        duration.record((performance.now() - started) / 1000, { operation, outcome });
        span.end();
      }
    },
  );
}

const PAGE_SIZE = 2;

function encodeCursor(offset: number): string {
  return Buffer.from(JSON.stringify({ offset })).toString("base64url");
}

function decodeCursor(cursor: string): number | undefined {
  try {
    const value: unknown = JSON.parse(Buffer.from(cursor, "base64url").toString());
    const offset = (value as { offset?: unknown }).offset;
    return typeof offset === "number" && offset >= 0 ? offset : undefined;
  } catch {
    return undefined;
  }
}

function toolError(text: string) {
  // A falha volta como resultado com isError: o modelo lê o motivo e pode corrigir a chamada.
  return { content: [{ type: "text" as const, text }], isError: true };
}

function buildServer(): McpServer {
  const server = new McpServer({ name: "orders", version: "1.0.0" });

  server.registerTool(
    "getOrderStatus",
    {
      description: "Get the status of an order",
      inputSchema: z.object({
        orderId: z.string().min(1).describe("Order identifier"),
        urgency: z.enum(["low", "high"]).default("low"),
      }),
    },
    async ({ orderId, urgency }, ctx) =>
      observe("getOrderStatus", ctx.mcpReq._meta, async () => {
        // A consulta entra depois da validação, e os parâmetros nunca são concatenados no SQL.
        const { rows } = await pool.query("SELECT status FROM orders WHERE id = $1", [orderId]);
        if (rows.length === 0) {
          log(SeverityNumber.WARN, `order ${orderId} not found`);
          return toolError(`Order ${orderId} does not exist`);
        }
        return { content: [{ type: "text" as const, text: `Order ${orderId} is ${rows[0].status} (${urgency})` }] };
      }),
  );

  server.registerTool(
    "listOrders",
    {
      description: "List orders, one page at a time. Send back nextCursor to read the next page.",
      inputSchema: z.object({ cursor: z.string().optional() }),
    },
    async ({ cursor }, ctx) =>
      observe("listOrders", ctx.mcpReq._meta, async () => {
        const offset = cursor === undefined ? 0 : decodeCursor(cursor);
        if (offset === undefined) {
          return toolError("Invalid cursor");
        }
        const { rows } = await pool.query("SELECT id, status FROM orders ORDER BY id LIMIT $1 OFFSET $2", [
          PAGE_SIZE + 1,
          offset,
        ]);
        const page = rows.slice(0, PAGE_SIZE);
        // O cursor é opaco: o client devolve o valor sem conhecer a paginação interna.
        const nextCursor = rows.length > PAGE_SIZE ? encodeCursor(offset + PAGE_SIZE) : undefined;
        return { content: [{ type: "text" as const, text: JSON.stringify({ orders: page, nextCursor }) }] };
      }),
  );

  server.registerTool(
    "runDiagnostic",
    {
      description: "Run a long diagnostic. It stops when the client cancels.",
      inputSchema: z.object({ seconds: z.number().positive().max(60) }),
    },
    async ({ seconds }, ctx) =>
      observe("runDiagnostic", ctx.mcpReq._meta, async () => {
        const signal = ctx.mcpReq.signal;
        try {
          await new Promise<void>((resolve, reject) => {
            const timer = setTimeout(resolve, seconds * 1000);
            signal.addEventListener(
              "abort",
              () => {
                // Cancelar é limpar o recurso pendente, não apenas parar de esperar.
                clearTimeout(timer);
                reject(new Error("canceled"));
              },
              { once: true },
            );
          });
        } catch (error) {
          cancellations.add(1, { operation: "runDiagnostic" });
          log(SeverityNumber.INFO, "diagnostic canceled; timer cleared");
          throw error;
        }
        return { content: [{ type: "text" as const, text: "Diagnostic finished" }] };
      }),
  );

  return server;
}

// A fábrica roda a cada request: nenhuma conexão guarda estado, como pede a revisão 2026-07-28.
const nodeHandler = toNodeHandler(createMcpHandler(() => buildServer()));

createServer((request, response) => {
  if (request.url === "/healthz") {
    response.writeHead(200, { "content-type": "application/json" }).end('{"status":"ok"}');
    return;
  }
  void nodeHandler(request, response);
}).listen(8000, "0.0.0.0", () => log(SeverityNumber.INFO, "orders server listening on port 8000"));
