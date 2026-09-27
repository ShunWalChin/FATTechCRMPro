#!/usr/bin/env node
/**
 * fattech-crm-mcp — servidor MCP (stdio) que o OpenClaw sobe uma vez por agente.
 * Cada instância carrega a chave e o agent_id de UM agente (ver openclaw.json5).
 *
 * Logs vão para stderr (stdout é o canal do protocolo MCP) e passam por
 * redactForLog antes de sair.
 */
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { loadCrmConfig } from "./config.js";
import { CrmClient } from "./crm-client.js";
import { RateLimiter, redactForLog } from "./guard.js";
import { createCrmServer } from "./tools.js";

async function main(): Promise<void> {
  const config = loadCrmConfig();
  const client = new CrmClient(config);
  const limiter = new RateLimiter(config.maxActsPerMinute);
  const log = (line: string) => process.stderr.write(`[fattech-crm-mcp] ${redactForLog(line)}\n`);
  const server = createCrmServer({ client, limiter, log });
  await server.connect(new StdioServerTransport());
  log(`pronto agent=${config.agentId} crm=${config.baseUrl}`);
}

main().catch((error: unknown) => {
  process.stderr.write(`[fattech-crm-mcp] falha na partida: ${redactForLog(String(error))}\n`);
  process.exit(1);
});
