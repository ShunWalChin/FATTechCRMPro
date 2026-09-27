// Integração: cliente MCP real ↔ servidor MCP real ↔ dublê HTTP do CRM.
import { test, before, after } from "node:test";
import assert from "node:assert/strict";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { InMemoryTransport } from "@modelcontextprotocol/sdk/inMemory.js";
import { CrmClient } from "../dist/crm-client.js";
import { RateLimiter } from "../dist/guard.js";
import { createCrmServer } from "../dist/tools.js";
import { loadCrmConfig } from "../dist/config.js";
import { startFakeCrm } from "./fake-crm.mjs";

let crm;
let mcp;

async function connect(env, perMinute = 30) {
  const config = loadCrmConfig(env);
  const server = createCrmServer({ client: new CrmClient(config), limiter: new RateLimiter(perMinute) });
  const [clientSide, serverSide] = InMemoryTransport.createLinkedPair();
  await server.connect(serverSide);
  const client = new Client({ name: "teste", version: "1.0.0" });
  await client.connect(clientSide);
  return client;
}

const text = (result) => result.content.map((c) => c.text).join("\n");

before(async () => {
  crm = await startFakeCrm();
  mcp = await connect({ FATTECH_CRM_BASE_URL: crm.url, FATTECH_CRM_API_KEY: "chave-sdr", FATTECH_CRM_AGENT_ID: "agente-sdr" });
});

after(async () => {
  await mcp?.close();
  await crm?.close();
});

test("expõe as oito ferramentas com anotações coerentes", async () => {
  const { tools } = await mcp.listTools();
  const names = tools.map((t) => t.name).sort();
  assert.deepEqual(names, [
    "crm_abrir_corrida", "crm_agir", "crm_catalogo", "crm_corrida",
    "crm_encerrar_corrida", "crm_fila", "crm_orcamento", "crm_reclamar_corridas",
  ]);
  const agir = tools.find((t) => t.name === "crm_agir");
  assert.equal(agir.annotations.destructiveHint, true);
  assert.equal(tools.find((t) => t.name === "crm_catalogo").annotations.readOnlyHint, true);
  assert.ok(!("agent_id" in (tools.find((t) => t.name === "crm_reclamar_corridas").inputSchema.properties ?? {})),
    "agent_id nunca pode ser argumento");
});

test("ciclo completo: reclamar → agir → encerrar", async () => {
  const claimed = await mcp.callTool({ name: "crm_reclamar_corridas", arguments: { limite: 1 } });
  assert.ok(!claimed.isError, text(claimed));
  assert.match(text(claimed), /run-1/);
  assert.equal(crm.state.calls.at(-1).body.agent_id, "agente-sdr", "agent_id vem do ambiente");

  const read = await mcp.callTool({ name: "crm_agir", arguments: { run_id: "run-1", ferramenta: "contacts.read", argumentos: { q: "Lead" } } });
  assert.ok(!read.isError);
  assert.match(text(read), /^ATENÇÃO: \d+ padrão/, "conteúdo do lead com injeção é sinalizado");
  assert.match(text(read), /<<DADO_EXTERNO_CRM>>/);

  const draft = await mcp.callTool({ name: "crm_agir", arguments: { run_id: "run-1", ferramenta: "contacts.write", argumentos: { id: "c1", version: 3, stage: "qualificado" } } });
  assert.match(text(draft), /"decision": "suggested"/);

  const send = await mcp.callTool({ name: "crm_agir", arguments: { run_id: "run-1", ferramenta: "messages.write", argumentos: { body: "Olá!" } } });
  assert.match(text(send), /"decision": "approval_required"/);

  const done = await mcp.callTool({ name: "crm_encerrar_corrida", arguments: { run_id: "run-1", status: "done", tokens_in: 1200, tokens_out: 300, custo_centavos: 1 } });
  assert.ok(!done.isError, text(done));
  assert.equal(crm.state.calls.at(-1).body.cost_cents, 1);

  const again = await mcp.callTool({ name: "crm_encerrar_corrida", arguments: { run_id: "run-1", status: "done" } });
  assert.equal(again.isError, true);
  assert.match(text(again), /409/);
});

test("fila própria por padrão e outra somente pela permissão do CRM", async () => {
  const own = await mcp.callTool({ name: "crm_fila", arguments: {} });
  assert.match(text(own), /agente-sdr/);
  const other = await mcp.callTool({ name: "crm_fila", arguments: { agente: "agente-outro" } });
  assert.equal(other.isError, true, "o dublê não concede observação cruzada");
  assert.equal(crm.state.calls.at(-1).url, "/api/v1/agent/agente-outro/queue");
  assert.equal(crm.state.calls.at(-1).method, "GET");
});

test("abrir corrida para evento repetido devolve replay em vez de duplicar", async () => {
  const first = await mcp.callTool({ name: "crm_abrir_corrida", arguments: { trigger_event_id: "evt-9", trigger_type: "manual.marvin", justificativa: "Wal pediu revisão da conta Silva & Rocha" } });
  const second = await mcp.callTool({ name: "crm_abrir_corrida", arguments: { trigger_event_id: "evt-9", trigger_type: "manual.marvin", justificativa: "Wal pediu revisão da conta Silva & Rocha" } });
  assert.match(text(first), /"replay": false/);
  assert.match(text(second), /"replay": true/);
});

test("nome de ferramenta malformado é recusado antes de chegar ao CRM", async () => {
  const before = crm.state.calls.length;
  const result = await mcp.callTool({ name: "crm_agir", arguments: { run_id: "run-1", ferramenta: "contacts.read; DROP TABLE", argumentos: {} } });
  assert.equal(result.isError, true);
  assert.equal(crm.state.calls.length, before);
});

test("argumento acima do limite é recusado localmente", async () => {
  const before = crm.state.calls.length;
  const result = await mcp.callTool({ name: "crm_agir", arguments: { run_id: "run-1", ferramenta: "contacts.write", argumentos: { notes: "x".repeat(40_000) } } });
  assert.equal(result.isError, true);
  assert.match(text(result), /32768 bytes/);
  assert.equal(crm.state.calls.length, before);
});

test("chave errada vira erro explicado, sem retentativa em POST", async () => {
  const wrong = await connect({ FATTECH_CRM_BASE_URL: crm.url, FATTECH_CRM_API_KEY: "chave-errada", FATTECH_CRM_AGENT_ID: "agente-sdr" });
  const before = crm.state.calls.length;
  const result = await wrong.callTool({ name: "crm_reclamar_corridas", arguments: { limite: 1 } });
  assert.equal(result.isError, true);
  assert.match(text(result), /401/);
  assert.match(text(result), /reemitida/);
  assert.equal(crm.state.calls.length - before, 1, "POST não pode ser repetido automaticamente");
  await wrong.close();
});

test("teto local por minuto segura rajada de tentativas", async () => {
  crm.state.runs.set("run-2", { id: "run-2", agent_id: "agente-sdr", status: "planning", trigger_event_id: "evt-2" });
  const limited = await connect({ FATTECH_CRM_BASE_URL: crm.url, FATTECH_CRM_API_KEY: "chave-sdr", FATTECH_CRM_AGENT_ID: "agente-sdr" }, 2);
  const call = () => limited.callTool({ name: "crm_agir", arguments: { run_id: "run-2", ferramenta: "contacts.read", argumentos: {} } });
  assert.ok(!(await call()).isError);
  assert.ok(!(await call()).isError);
  const third = await call();
  assert.equal(third.isError, true);
  assert.match(text(third), /Teto local/);
  await limited.close();
});

test("configuração ausente falha na partida com o nome da variável", () => {
  assert.throws(() => loadCrmConfig({ FATTECH_CRM_BASE_URL: "http://x", FATTECH_CRM_AGENT_ID: "a" }), /FATTECH_CRM_API_KEY/);
  assert.throws(() => loadCrmConfig({ FATTECH_CRM_BASE_URL: "ftp://x", FATTECH_CRM_API_KEY: "k", FATTECH_CRM_AGENT_ID: "a" }), /http\(s\)/);
});
