import { test } from "node:test";
import assert from "node:assert/strict";
import http from "node:http";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { InMemoryTransport } from "@modelcontextprotocol/sdk/inMemory.js";
import { createProbeServer, parseTargets, probe } from "../dist/probe-server.js";

test("parseTargets aceita lista fechada e recusa lixo", () => {
  assert.deepEqual(parseTargets("crm-api=http://api:8000/api/health,n8n=https://n8n.example/healthz").map((t) => t.name), ["crm-api", "n8n"]);
  assert.deepEqual(parseTargets(""), []);
  assert.throws(() => parseTargets("semigual"), /nome=url/);
  assert.throws(() => parseTargets("x=file:///etc/passwd"), /http\(s\)/);
  assert.throws(() => parseTargets("a=http://a,a=http://b"), /duplicado/);
  assert.throws(() => parseTargets("Nome Ruim=http://a"), /inválido/);
});

test("probe mede status e não segue redirecionamento", async () => {
  const server = http.createServer((req, res) => {
    if (req.url === "/ok") { res.writeHead(200); res.end('{"status":"ok"}'); return; }
    res.writeHead(302, { Location: "http://169.254.169.254/latest/meta-data" }); res.end();
  });
  await new Promise((r) => server.listen(0, "127.0.0.1", r));
  const base = `http://127.0.0.1:${server.address().port}`;
  const fetchImpl = globalThis.fetch.bind(globalThis);
  const good = await probe({ name: "ok", url: `${base}/ok` }, fetchImpl);
  const redirect = await probe({ name: "redir", url: `${base}/redir` }, fetchImpl);
  assert.equal(good.ok, true);
  assert.equal(good.status, 200);
  assert.equal(redirect.ok, false);
  assert.equal(redirect.status, 302, "redirecionamento não é seguido");
  const down = await probe({ name: "down", url: "http://127.0.0.1:9/" }, fetchImpl, 1500);
  assert.equal(down.ok, false);
  assert.ok(down.error);
  server.close();
});

test("servidor MCP da sonda recusa alvo fora da lista", async () => {
  const server = createProbeServer(parseTargets("crm-api=http://127.0.0.1:9/health"), globalThis.fetch.bind(globalThis));
  const [a, b] = InMemoryTransport.createLinkedPair();
  await server.connect(b);
  const client = new Client({ name: "t", version: "1" });
  await client.connect(a);
  const outside = await client.callTool({ name: "probe_verificar", arguments: { alvos: ["https://evil.example"] } });
  assert.equal(outside.isError, true);
  const listed = await client.callTool({ name: "probe_alvos", arguments: {} });
  assert.match(listed.content[0].text, /crm-api/);
  await client.close();
});
