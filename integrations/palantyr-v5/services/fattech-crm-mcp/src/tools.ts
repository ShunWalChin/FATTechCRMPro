/**
 * Ferramentas MCP expostas ao agente do OpenClaw.
 *
 * O desenho segue o ciclo de uma corrida no CRM (docs/OPENCLAW_BLUEPRINT.md, E1–E5):
 *
 *   crm_reclamar_corridas → crm_agir (N vezes) → crm_encerrar_corrida
 *
 * Três decisões que protegem a operação:
 *   1. O `agent_id` NÃO é argumento: vem do ambiente do processo. Um agente
 *      manipulado não consegue operar em nome de outro agente.
 *   2. Toda resposta com conteúdo do CRM volta embrulhada como DADO EXTERNO,
 *      com os achados de injeção à frente (ver guard.ts).
 *   3. Erro de protocolo volta como `isError`, com status e detalhe; recusa de
 *      negócio volta como resultado normal, porque é resultado — não falha.
 */
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { CrmClient, CrmHttpError } from "./crm-client.js";
import { MAX_ARGUMENT_BYTES, RateLimiter, TOOL_NAME, argumentSize, redactForLog, wrapExternal } from "./guard.js";

type ToolResult = { content: Array<{ type: "text"; text: string }>; isError?: boolean };

export interface ServerDeps {
  client: CrmClient;
  limiter: RateLimiter;
  log?: (line: string) => void;
}

function ok(payload: unknown, external = true): ToolResult {
  if (!external) return { content: [{ type: "text", text: JSON.stringify(payload, null, 2) }] };
  return { content: [{ type: "text", text: wrapExternal(payload).text }] };
}

function fail(message: string, detail?: unknown): ToolResult {
  const body = detail === undefined ? message : `${message}\n${JSON.stringify(detail, null, 2)}`;
  return { content: [{ type: "text", text: body }], isError: true };
}

function explain(error: unknown): ToolResult {
  if (error instanceof CrmHttpError) {
    const hints: Record<number, string> = {
      401: "Chave inválida, revogada ou vencida. Pare e avise o Marvin: a identidade do agente precisa ser reemitida.",
      403: "Escopo insuficiente. Não tente contornar: a ferramenta não pertence a este agente.",
      404: "Registro ou corrida inexistente. Confira o id lido antes de agir.",
      409: "Conflito: corrida encerrada, agente pausado ou versão desatualizada. Releia o registro antes de tentar de novo.",
      422: "Argumentos inválidos para o CRM. Corrija o formato; não repita igual.",
      429: "Teto atingido no CRM. Encerre a corrida como 'refused' e registre o motivo.",
    };
    return fail(`CRM respondeu ${error.status}. ${hints[error.status] ?? "Falha do CRM; encerre a corrida como 'degraded' se persistir."}`,
      { status: error.status, detail: error.detail });
  }
  const message = error instanceof Error ? error.message : String(error);
  if (/abort/i.test(message)) {
    return fail("Tempo esgotado falando com o CRM. Encerre a corrida como 'degraded'; o evento continua na fila e será retomado.");
  }
  return fail(`Falha de rede com o CRM: ${message}`);
}

export function createCrmServer({ client, limiter, log = () => {} }: ServerDeps): McpServer {
  const server = new McpServer({ name: "fattech-crm", version: "1.0.0" });

  const guarded = async (name: string, fn: () => Promise<ToolResult>): Promise<ToolResult> => {
    const started = Date.now();
    try {
      const result = await fn();
      log(`tool=${name} agent=${client.agentId} ok=${!result.isError} ms=${Date.now() - started}`);
      return result;
    } catch (error) {
      log(`tool=${name} agent=${client.agentId} erro=${redactForLog(String(error))}`);
      return explain(error);
    }
  };

  server.registerTool(
    "crm_catalogo",
    {
      title: "Catálogo de ferramentas do CRM",
      description:
        "Lista as ferramentas que o portão do CRM conhece, com escopo, classe (interna/externa), " +
        "se é reversível e se já é executável. Use antes de planejar uma corrida.",
      annotations: { readOnlyHint: true, openWorldHint: false },
    },
    () => guarded("crm_catalogo", async () => ok(await client.catalog(), false)),
  );

  server.registerTool(
    "crm_fila",
    {
      title: "Fila de um agente",
      description:
        "Mostra corridas pendentes, idade da mais antiga e corridas reclamadas sem retorno da própria identidade. Não reclama nada.",
      annotations: { readOnlyHint: true, openWorldHint: false },
    },
    () => guarded("crm_fila", async () => ok(await client.queue(), false)),
  );

  server.registerTool(
    "crm_orcamento",
    {
      title: "Orçamento e teto deste agente",
      description: "Gasto do mês (derivado das corridas), orçamento declarado e teto de ações por hora.",
      annotations: { readOnlyHint: true, openWorldHint: false },
    },
    () => guarded("crm_orcamento", async () => ok(await client.budget(), false)),
  );

  server.registerTool(
    "crm_corrida",
    {
      title: "Detalhe de uma corrida",
      description: "Evento que disparou → justificativa → passos tentados → recusas e motivos.",
      inputSchema: { run_id: z.string().min(1).max(36) },
      annotations: { readOnlyHint: true, openWorldHint: false },
    },
    ({ run_id }) => guarded("crm_corrida", async () => ok(await client.run(run_id))),
  );

  server.registerTool(
    "crm_reclamar_corridas",
    {
      title: "Reclamar corridas pendentes",
      description:
        "Pega até `limite` corridas que eventos do CRM criaram para este agente e as move para 'planning'. " +
        "Reclame só o que vai processar agora: corrida reclamada e abandonada fica presa e aparece na tela.",
      inputSchema: { limite: z.number().int().min(1).max(25).default(3) },
      annotations: { readOnlyHint: false, destructiveHint: false, idempotentHint: false, openWorldHint: false },
    },
    ({ limite }) => guarded("crm_reclamar_corridas", async () => ok(await client.claim(limite))),
  );

  server.registerTool(
    "crm_abrir_corrida",
    {
      title: "Abrir corrida para um evento",
      description:
        "Abre uma corrida manual ligada a um evento. O mesmo evento nunca abre duas corridas: " +
        "replay devolve a existente com replay=true. A justificativa é obrigatória e fica na trilha selada.",
      inputSchema: {
        trigger_event_id: z.string().min(1).max(36),
        trigger_type: z.string().min(1).max(100),
        justificativa: z.string().min(10).max(20000),
        modelo: z.string().max(120).optional(),
      },
      annotations: { readOnlyHint: false, destructiveHint: false, idempotentHint: true, openWorldHint: false },
    },
    ({ trigger_event_id, trigger_type, justificativa, modelo }) =>
      guarded("crm_abrir_corrida", async () =>
        ok(await client.openRun({ trigger_event_id, trigger_type, rationale: justificativa, model: modelo ?? "" }))),
  );

  server.registerTool(
    "crm_agir",
    {
      title: "Tentar uma ação no CRM",
      description:
        "Uma tentativa pelo portão do CRM. Sempre grava um passo. Decisões possíveis: " +
        "allowed (executou), suggested (virou rascunho para uma pessoa aplicar), " +
        "approval_required (virou solicitação; você NÃO decide), refused (motivo gravado). " +
        "Escrita em registro existente exige `id` e `version` atuais nos argumentos.",
      inputSchema: {
        run_id: z.string().min(1).max(36),
        ferramenta: z.string().regex(TOOL_NAME, "formato esperado: kind.operacao"),
        argumentos: z.record(z.string(), z.unknown()).default({}),
      },
      annotations: { readOnlyHint: false, destructiveHint: true, idempotentHint: false, openWorldHint: true },
    },
    ({ run_id, ferramenta, argumentos }) =>
      guarded("crm_agir", async () => {
        if (argumentSize(argumentos) > MAX_ARGUMENT_BYTES) {
          return fail(`Argumentos acima de ${MAX_ARGUMENT_BYTES} bytes. Divida a ação ou resuma o conteúdo.`);
        }
        if (!limiter.tryTake()) {
          return fail("Teto local de tentativas por minuto atingido. Pare, encerre a corrida e deixe o restante para o próximo ciclo.");
        }
        const result = await client.act({ run_id, tool: ferramenta, arguments: argumentos });
        return ok(result);
      }),
  );

  server.registerTool(
    "crm_encerrar_corrida",
    {
      title: "Encerrar corrida",
      description:
        "Fecha a corrida com status e custo. done = objetivo cumprido; refused = portão recusou o essencial; " +
        "degraded = modelo/CRM indisponível, retomar depois; failed = erro que exige pessoa. " +
        "O gasto do mês é somado destas corridas — declare tokens e custo reais.",
      inputSchema: {
        run_id: z.string().min(1).max(36),
        status: z.enum(["done", "failed", "degraded", "refused"]),
        tokens_in: z.number().int().min(0).max(100_000_000).default(0),
        tokens_out: z.number().int().min(0).max(100_000_000).default(0),
        custo_centavos: z.number().int().min(0).max(100_000_000).default(0),
        erro: z.string().max(20000).optional(),
      },
      annotations: { readOnlyHint: false, destructiveHint: false, idempotentHint: false, openWorldHint: false },
    },
    ({ run_id, status, tokens_in, tokens_out, custo_centavos, erro }) =>
      guarded("crm_encerrar_corrida", async () =>
        ok(await client.finish(run_id, { status, tokens_in, tokens_out, cost_cents: custo_centavos, error: erro ?? "" }), false)),
  );

  return server;
}
