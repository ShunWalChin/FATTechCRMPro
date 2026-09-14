"""Merge reviewed business knowledge after `graphify update .`, preserving AST identifiers.

Run with the Python interpreter where Graphify is installed. Unlike merge-graphs (a
multi-repository operation), build_merge replaces this artifact by source_file and
does not repeatedly namespace the entire local graph.
"""
import json
from pathlib import Path

from graphify.build import build_merge

root = Path(__file__).resolve().parents[1]
path = root / "graphify-out/graph.json"
knowledge = json.loads((root / "docs/knowledge/business-rules-0.4.json").read_text(encoding="utf-8"))
original = json.loads(path.read_text(encoding="utf-8"))
# Evidence is an explicit, reviewed file reference, so connect rules to actual AST file nodes.
for rule in knowledge["nodes"]:
    for evidence in rule.get("evidence", []):
        matches = [node for node in original["nodes"] if node.get("source_file") == evidence["path"]
                   and node.get("label") == Path(evidence["path"]).name]
        for node in matches:
            knowledge["edges"].append({"source": rule["id"], "target": node["id"], "relation": "evidence_in",
                "confidence": "EXTRACTED", "source_file": "docs/knowledge/business-rules-0.4.json",
                "source_location": evidence["path"]})
graph = build_merge([knowledge], graph_path=str(path), root=str(root), directed=bool(original.get("directed")))
nodes = [{**data, "id": key} for key, data in graph.nodes(data=True)]
edges = [{**{k: value for k, value in data.items() if k not in {"_src", "_tgt", "source", "target"}},
          "source": data.get("_src", source), "target": data.get("_tgt", target)}
         for source, target, data in graph.edges(data=True)]
result = {"nodes": nodes, "links": edges, "directed": graph.is_directed(),
          "hyperedges": list(graph.graph.get("hyperedges", []))}
path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
assert {n["id"] for n in knowledge["nodes"]} <= set(graph.nodes)
print(f"Knowledge merged: {len(nodes)} nodes, {len(edges)} edges; stable business IDs verified.")
