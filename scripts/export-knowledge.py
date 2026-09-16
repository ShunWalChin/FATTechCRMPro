"""Build the knowledge graph the CRM serves as its own knowledge base.

Graphify's AST graph answers who calls whom. It does not answer why a rule exists, what a release
changed, or which service runs beside us on the host. This assembles the curated layer -- business
rules, the domain model the CRM actually declares, the release history and the infrastructure
inventory -- into one graph the application can serve and a person can walk.

The output is versioned in Git, not regenerated at runtime: the knowledge base must answer the same
thing in production as it does here, and a graph rebuilt from a machine's local paths would not.

Usage: python scripts/export-knowledge.py
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
KNOWLEDGE = ROOT / "docs/knowledge"
# O grafo vive no pacote da API, que e o que a imagem publica: docs/ nao entra no contêiner.
# Fonte unica, nao duas copias — as fontes escritas a mao continuam em docs/knowledge/.
TARGET = ROOT / "apps/api/fattech/knowledge_graph.json"

# Cada família tem cor própria na tela; o mapa vive aqui para que dado e desenho não divirjam.
FAMILIES = {
    "business_rule": {"label": "Regra de negócio", "tone": "#00b8cc"},
    "engineering_pattern": {"label": "Padrão de engenharia", "tone": "#a855f7"},
    "licao": {"label": "Lição", "tone": "#f5c518"},
    "licao_de_debito": {"label": "Lição", "tone": "#f5c518"},
    "domain": {"label": "Domínio do CRM", "tone": "#00ff88"},
    "release": {"label": "Publicação", "tone": "#ff2d78"},
    "service": {"label": "Serviço no servidor", "tone": "#7c8f9c"},
    "guarantee": {"label": "Garantia verificada", "tone": "#00f0ff"},
}


def curated_nodes() -> tuple[list[dict], list[dict]]:
    """The business knowledge artifacts, which are hand-written and reviewed."""
    nodes, edges = [], []
    for path in sorted(KNOWLEDGE.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        for node in data.get("nodes", []):
            nodes.append({
                "id": node["id"],
                "label": node["label"],
                "family": node.get("type", "business_rule"),
                "summary": node.get("rule", ""),
                "why": node.get("por_que_importa", ""),
                "status": node.get("status", ""),
                "where": node.get("onde_no_fattech") or node.get("onde_caberia", ""),
                "source": path.name,
            })
        for edge in data.get("edges", []):
            edges.append({"source": edge["source"], "target": edge["target"],
                          "relation": edge.get("relation", "relaciona"),
                          "note": edge.get("action", "")})
    return nodes, edges


def domain_nodes() -> tuple[list[dict], list[dict]]:
    """The domain model the API actually declares, read from the schema rather than described."""
    sys.path.insert(0, str(ROOT / "apps/api"))
    from fattech.schemas import RESOURCES

    nodes, edges = [], []
    relationships = {"contact_id": "contacts", "company_id": "companies", "deal_id": "deals",
                     "project_id": "projects", "conversation_id": "conversations",
                     "pipeline_id": "pipelines", "product_id": "products"}
    for kind, model in sorted(RESOURCES.items()):
        campos = list(getattr(model, "model_fields", {}))
        nodes.append({
            "id": f"fattech:domain:{kind}",
            "label": kind,
            "family": "domain",
            "summary": f"{len(campos)} campos declarados no schema.",
            "why": "",
            "status": "implementado",
            "where": "apps/api/fattech/schemas.py",
            "source": "schema",
        })
        for campo in campos:
            alvo = relationships.get(campo)
            if alvo and alvo in RESOURCES and alvo != kind:
                edges.append({"source": f"fattech:domain:{kind}", "target": f"fattech:domain:{alvo}",
                              "relation": "referencia", "note": campo})
    return nodes, edges


def release_nodes() -> tuple[list[dict], list[dict]]:
    """Each release, and the rules it touched, so a decision can be traced to when it was made."""
    nodes, edges = [], []
    anteriores = None
    for path in sorted((ROOT / "docs/releases").glob("*.md")):
        texto = path.read_text(encoding="utf-8")
        titulo = texto.splitlines()[0].lstrip("# ").strip()
        primeiro = next((linha.strip() for linha in texto.splitlines()[1:]
                         if linha.strip() and not linha.startswith("#")), "")
        node_id = f"fattech:release:{path.stem}"
        nodes.append({
            "id": node_id, "label": titulo, "family": "release",
            "summary": primeiro[:240], "why": "", "status": "publicado",
            "where": f"docs/releases/{path.name}", "source": "releases",
        })
        if anteriores:
            edges.append({"source": anteriores, "target": node_id,
                          "relation": "precede", "note": "publicação seguinte"})
        anteriores = node_id
    return nodes, edges


def service_nodes() -> tuple[list[dict], list[dict]]:
    """What else runs on the host. Knowing the neighbours is part of knowing the system."""
    inventario = KNOWLEDGE / "server-inventory.json"
    if not inventario.exists():
        return [], []
    data = json.loads(inventario.read_text(encoding="utf-8"))
    nodes, edges = [], []
    host = {"id": "fattech:infra:host", "label": data["host"]["label"], "family": "service",
            "summary": data["host"]["summary"], "why": "", "status": "ativo",
            "where": data["host"].get("where", ""), "source": "server-inventory"}
    nodes.append(host)
    for servico in data["services"]:
        node_id = f"fattech:infra:{servico['slug']}"
        nodes.append({"id": node_id, "label": servico["label"], "family": "service",
                      "summary": servico["summary"], "why": servico.get("why", ""),
                      "status": servico.get("status", "ativo"),
                      "where": servico.get("where", ""), "source": "server-inventory"})
        edges.append({"source": host["id"], "target": node_id,
                      "relation": "hospeda", "note": f"{servico['containers']} contêineres"})
    return nodes, edges


def main() -> int:
    nodes: list[dict] = []
    edges: list[dict] = []
    for produtor in (curated_nodes, domain_nodes, release_nodes, service_nodes):
        n, e = produtor()
        nodes.extend(n)
        edges.extend(e)

    conhecidos = {node["id"] for node in nodes}
    # Uma aresta órfã desenha uma linha para lugar nenhum: some antes de chegar à tela.
    orfas = [edge for edge in edges if edge["source"] not in conhecidos or edge["target"] not in conhecidos]
    edges = [edge for edge in edges if edge not in orfas]

    for node in nodes:
        familia = FAMILIES.get(node["family"], FAMILIES["business_rule"])
        node["familyLabel"] = familia["label"]
        node["tone"] = familia["tone"]
        node["degree"] = sum(1 for e in edges if node["id"] in (e["source"], e["target"]))

    grafo = {
        "generated_from": "docs/knowledge/*.json, apps/api schemas, docs/releases",
        "families": [{"key": k, **v} for k, v in FAMILIES.items()],
        "nodes": sorted(nodes, key=lambda n: (n["family"], n["label"])),
        "edges": edges,
        "counts": {"nodes": len(nodes), "edges": len(edges),
                   "por_familia": {k: sum(1 for n in nodes if n["family"] == k) for k in FAMILIES}},
    }
    TARGET.write_text(json.dumps(grafo, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(nodes)} nós, {len(edges)} arestas -> {TARGET.relative_to(ROOT).as_posix()}")
    if orfas:
        print(f"{len(orfas)} aresta(s) órfã(s) descartada(s): {[e['target'] for e in orfas][:4]}")
    for familia, quantos in grafo["counts"]["por_familia"].items():
        if quantos:
            print(f"   {FAMILIES[familia]['label']:24} {quantos}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
