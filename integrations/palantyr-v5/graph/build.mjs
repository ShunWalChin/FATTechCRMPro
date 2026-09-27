#!/usr/bin/env node
/**
 * Lê graph.json e gera:
 *   - metricas.md : grau, centralidade de intermediação (Brandes) e pontos de articulação —
 *                   os nós cuja queda desconecta o ecossistema (candidatos a redundância)
 *   - grafo.mmd   : Mermaid do núcleo (sem clientes, para caber na tela)
 * Sem dependências. `node graph/build.mjs`
 */
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const { nos, arestas } = JSON.parse(readFileSync(join(here, "graph.json"), "utf8"));
const ids = nos.map((n) => n.id);
const byId = new Map(nos.map((n) => [n.id, n]));
const adj = new Map(ids.map((id) => [id, new Set()]));
for (const { de, para } of arestas) { adj.get(de).add(para); adj.get(para).add(de); }

// Centralidade de intermediação (Brandes, grafo não dirigido, sem pesos)
const bc = new Map(ids.map((id) => [id, 0]));
for (const s of ids) {
  const stack = [], pred = new Map(ids.map((i) => [i, []])), sigma = new Map(ids.map((i) => [i, 0])), dist = new Map(ids.map((i) => [i, -1]));
  sigma.set(s, 1); dist.set(s, 0);
  const queue = [s];
  while (queue.length) {
    const v = queue.shift(); stack.push(v);
    for (const w of adj.get(v)) {
      if (dist.get(w) < 0) { dist.set(w, dist.get(v) + 1); queue.push(w); }
      if (dist.get(w) === dist.get(v) + 1) { sigma.set(w, sigma.get(w) + sigma.get(v)); pred.get(w).push(v); }
    }
  }
  const delta = new Map(ids.map((i) => [i, 0]));
  while (stack.length) {
    const w = stack.pop();
    for (const v of pred.get(w)) delta.set(v, delta.get(v) + (sigma.get(v) / sigma.get(w)) * (1 + delta.get(w)));
    if (w !== s) bc.set(w, bc.get(w) + delta.get(w));
  }
}
const n = ids.length;
const norm = (x) => x / 2 / (((n - 1) * (n - 2)) / 2);

// Pontos de articulação (Tarjan)
const disc = new Map(), low = new Map(), cut = new Set();
let time = 0;
function dfs(u, parent) {
  disc.set(u, ++time); low.set(u, time);
  let children = 0;
  for (const v of adj.get(u)) {
    if (!disc.has(v)) {
      children++; dfs(v, u);
      low.set(u, Math.min(low.get(u), low.get(v)));
      if (parent !== null && low.get(v) >= disc.get(u)) cut.add(u);
    } else if (v !== parent) low.set(u, Math.min(low.get(u), disc.get(v)));
  }
  if (parent === null && children > 1) cut.add(u);
}
for (const id of ids) if (!disc.has(id)) dfs(id, null);

const rows = ids.map((id) => ({ id, label: byId.get(id).label, tipo: byId.get(id).tipo, grau: adj.get(id).size, bc: norm(bc.get(id)) }))
  .sort((a, b) => b.bc - a.bc);

const md = [
  "# Métricas do grafo do ecossistema", "",
  `${n} nós · ${arestas.length} arestas · gerado em ${new Date().toISOString().slice(0, 10)}`, "",
  "## Os 15 nós mais centrais (intermediação)", "",
  "Quanto maior, mais caminhos do ecossistema passam por ele — é onde uma falha espalha.", "",
  "| # | Nó | Tipo | Grau | Intermediação |", "|---|---|---|---|---|",
  ...rows.slice(0, 15).map((r, i) => `| ${i + 1} | ${r.label} | ${r.tipo} | ${r.grau} | ${r.bc.toFixed(3)} |`),
  "", "## Pontos de articulação", "",
  "Nós cuja remoção **desconecta** parte do grafo. Cada um precisa de redundância, runbook ou aceite explícito do risco.", "",
  ...[...cut].map((id) => `- **${byId.get(id).label}** (${byId.get(id).tipo}) — ${byId.get(id).desc || ""}`), "",
];
writeFileSync(join(here, "metricas.md"), md.join("\n"));

const core = new Set(nos.filter((x) => !["cliente", "risco", "divida", "demanda"].includes(x.tipo)).map((x) => x.id));
const safe = (id) => id.replace(/[^a-zA-Z0-9_]/g, "_");
const mmd = ["flowchart LR",
  ...nos.filter((x) => core.has(x.id)).map((x) => `  ${safe(x.id)}["${x.label.replace(/"/g, "'")}"]`),
  ...arestas.filter((a) => core.has(a.de) && core.has(a.para)).map((a) => `  ${safe(a.de)} -- ${a.tipo} --> ${safe(a.para)}`)];
writeFileSync(join(here, "grafo.mmd"), mmd.join("\n") + "\n");
console.log(`ok · ${rows.length} nós · top: ${rows.slice(0, 5).map((r) => r.label).join(", ")} · articulação: ${[...cut].length}`);
