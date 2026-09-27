#!/usr/bin/env node
/** Entrada stdio da sonda. A lógica testável está em probe-server.ts. */
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { createProbeServer, parseTargets } from "./probe-server.js";

async function main(): Promise<void> {
  const targets = parseTargets(process.env.PROBE_TARGETS);
  const server = createProbeServer(targets, globalThis.fetch.bind(globalThis));
  await server.connect(new StdioServerTransport());
  process.stderr.write(`[palantyr-probe] pronto com ${targets.length} alvo(s)\n`);
}

main().catch((error: unknown) => {
  process.stderr.write(`[palantyr-probe] falha na partida: ${String(error)}\n`);
  process.exit(1);
});
