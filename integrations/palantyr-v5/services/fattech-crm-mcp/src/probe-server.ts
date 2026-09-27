/**
 * palantyr-probe — sonda de saúde SEM shell para o agente Sentinela.
 *
 * Por que não `exec`: um agente com shell no host do CRM pode escrever onde o
 * processo puder, ler variáveis de ambiente (chaves) e ser induzido por conteúdo
 * externo. A sonda troca poder por previsibilidade: lista FECHADA de alvos
 * (PROBE_TARGETS), só GET, sem seguir redirecionamento, corpo truncado.
 *
 * PROBE_TARGETS="crm-api=http://api:8000/api/v1/health,n8n=https://n8n.pltr.fattech.com.br/healthz"
 */
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import type { FetchLike } from "./crm-client.js";

export interface ProbeTarget {
  name: string;
  url: string;
}

export function parseTargets(raw: string | undefined): ProbeTarget[] {
  if (!raw?.trim()) return [];
  const seen = new Set<string>();
  const targets: ProbeTarget[] = [];
  for (const entry of raw.split(",")) {
    const index = entry.indexOf("=");
    if (index <= 0) throw new Error(`Alvo mal formado (esperado nome=url): ${entry}`);
    const name = entry.slice(0, index).trim();
    const url = entry.slice(index + 1).trim();
    if (!/^[a-z0-9][a-z0-9_-]{0,40}$/.test(name)) throw new Error(`Nome de alvo inválido: ${name}`);
    const protocol = new URL(url).protocol;
    if (protocol !== "http:" && protocol !== "https:") throw new Error(`Alvo precisa ser http(s): ${url}`);
    if (seen.has(name)) throw new Error(`Alvo duplicado: ${name}`);
    seen.add(name);
    targets.push({ name, url });
  }
  return targets;
}

export interface ProbeResult {
  name: string;
  ok: boolean;
  status: number | null;
  latency_ms: number;
  checked_at: string;
  body_excerpt?: string;
  error?: string;
}

export async function probe(target: ProbeTarget, fetchImpl: FetchLike, timeoutMs = 8000): Promise<ProbeResult> {
  const started = Date.now();
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetchImpl(target.url, { method: "GET", redirect: "manual", signal: controller.signal });
    const text = (await response.text()).slice(0, 2000);
    return {
      name: target.name,
      ok: response.status >= 200 && response.status < 300,
      status: response.status,
      latency_ms: Date.now() - started,
      checked_at: new Date().toISOString(),
      body_excerpt: text.slice(0, 300),
    };
  } catch (error) {
    return {
      name: target.name,
      ok: false,
      status: null,
      latency_ms: Date.now() - started,
      checked_at: new Date().toISOString(),
      error: error instanceof Error ? error.message : String(error),
    };
  } finally {
    clearTimeout(timer);
  }
}

export function createProbeServer(targets: ProbeTarget[], fetchImpl: FetchLike): McpServer {
  const server = new McpServer({ name: "palantyr-probe", version: "1.0.0" });
  const byName = new Map(targets.map((t) => [t.name, t]));

  server.registerTool(
    "probe_alvos",
    {
      title: "Alvos monitorados",
      description: "Lista fechada de alvos que a sonda pode verificar. Não aceita URL livre.",
      annotations: { readOnlyHint: true, openWorldHint: false },
    },
    async () => ({ content: [{ type: "text", text: JSON.stringify(targets, null, 2) }] }),
  );

  server.registerTool(
    "probe_verificar",
    {
      title: "Verificar saúde",
      description: "Faz GET nos alvos pedidos (ou em todos) e devolve status, latência e trecho do corpo.",
      inputSchema: { alvos: z.array(z.string().max(41)).max(50).optional() },
      annotations: { readOnlyHint: true, openWorldHint: true },
    },
    async ({ alvos }) => {
      const selected = alvos?.length ? alvos : [...byName.keys()];
      const unknown = selected.filter((name) => !byName.has(name));
      if (unknown.length) {
        return { content: [{ type: "text", text: `Alvos fora da lista: ${unknown.join(", ")}` }], isError: true };
      }
      const results = await Promise.all(selected.map((name) => probe(byName.get(name)!, fetchImpl)));
      const summary = {
        total: results.length,
        falhas: results.filter((r) => !r.ok).map((r) => r.name),
        resultados: results,
      };
      return { content: [{ type: "text", text: JSON.stringify(summary, null, 2) }] };
    },
  );

  return server;
}
