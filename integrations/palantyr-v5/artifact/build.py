#!/usr/bin/env python3
"""Gera palantyr-v5.html a partir de template.html + ../graph/graph.json."""
import json, pathlib
here = pathlib.Path(__file__).parent
graph = json.loads((here.parent / "graph" / "graph.json").read_text(encoding="utf-8"))
html = (here / "template.html").read_text(encoding="utf-8").replace("__GRAPH__", json.dumps(graph, ensure_ascii=False))
(here / "palantyr-v5.html").write_text(html, encoding="utf-8")
print("ok", len(html), "bytes")
