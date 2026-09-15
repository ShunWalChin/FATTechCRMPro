"""Audit the published site against the original, across every dimension a page can lose.

Written after two silent losses got past a narrower check: the site's images were never committed,
and 48 pages shipped without the CSS their <head> carried. Both were invisible to a check that looked
only at what it already knew to look at. This one enumerates what each page references and proves each
of those things arrives, byte for byte where bytes are comparable.

Usage: python scripts/audit-site.py [--base https://...]
"""
import argparse
import collections
import hashlib
import pathlib
import re
import sys
from html.parser import HTMLParser

import httpx

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = ROOT / "apps/web/site-original"
ABSOLUTE = ("http://", "https://", "//", "#", "mailto:", "tel:", "data:", "javascript:")


def resolve(value: str, page_dir: pathlib.PurePosixPath) -> str:
    parts: list[str] = []
    for part in pathlib.PurePosixPath(page_dir / value).parts:
        if part == "..":
            if parts:
                parts.pop()
        elif part not in (".", ""):
            parts.append(part)
    return "/".join(parts)


def route_for(relative: str) -> str:
    if relative == "crm.html":
        return "/crm.html"
    if relative == "index.html":
        return "/"
    if relative.endswith("/index.html"):
        return "/" + relative[: -len("/index.html")]
    return "/" + relative[: -len(".html")]


class References(HTMLParser):
    """Everything a page points at, split into pages, assets and inline payloads."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.assets: list[str] = []
        self.pages: list[str] = []
        self.images = 0
        self.raw: str | None = None
        self.styles: list[str] = []
        self.scripts: list[str] = []
        self.buffer: list[str] = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag in ("style", "script") and "src" not in values:
            self.raw, self.buffer = tag, []
        if tag == "img":
            self.images += 1
        for key in ("href", "src"):
            value = values.get(key)
            if not value or value.startswith(ABSOLUTE):
                continue
            if tag == "link" and (values.get("rel") or "").lower() not in (
                    "stylesheet", "icon", "apple-touch-icon", "preload"):
                continue
            (self.pages if value.split("#")[0].endswith(".html") else self.assets).append(value.split("#")[0])

    def handle_data(self, data):
        if self.raw:
            self.buffer.append(data)

    def handle_endtag(self, tag):
        if self.raw == tag:
            body = "".join(self.buffer).strip()
            if body:
                (self.styles if tag == "style" else self.scripts).append(" ".join(body.split()))
            self.raw, self.buffer = None, []


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="https://fattechcrmpro.64.181.178.125.nip.io")
    args = parser.parse_args()
    pages = sorted(SOURCE.rglob("*.html"))
    problems: list[str] = []
    assets_needed: dict[str, set[str]] = collections.defaultdict(set)
    pages_linked: dict[str, set[str]] = collections.defaultdict(set)
    totals = collections.Counter()

    print(f"Auditando {len(pages)} paginas do original contra {args.base}\n")
    with httpx.Client(base_url=args.base, timeout=90, follow_redirects=True) as client:
        for path in pages:
            relative = path.relative_to(SOURCE).as_posix()
            original = path.read_text(encoding="utf-8")
            page_dir = pathlib.PurePosixPath(relative).parent
            reader = References()
            reader.feed(original)
            reader.close()
            for value in reader.assets:
                assets_needed[resolve(value, page_dir)].add(relative)
            for value in reader.pages:
                pages_linked[resolve(value, page_dir)].add(relative)
            if re.search(r'http-equiv="refresh"', original, re.I):
                totals["redirecionamentos"] += 1
                continue
            totals["paginas"] += 1
            response = client.get(route_for(relative))
            if response.status_code != 200:
                problems.append(f"{relative}: HTTP {response.status_code}")
                continue
            served = References()
            served.feed(response.text)
            served.close()
            if served.images < reader.images:
                problems.append(f"{relative}: {reader.images - served.images} imagem(ns) a menos no HTML")
            totals["imagens"] += reader.images
            for block in reader.styles:
                totals["blocos_css"] += 1
                totals["bytes_css"] += len(block)
                if block not in served.styles:
                    problems.append(f"{relative}: bloco de CSS embutido ausente ({len(block)} bytes)")
            for block in reader.scripts:
                totals["blocos_js"] += 1
                totals["bytes_js"] += len(block)
                if block in served.scripts:
                    continue
                tokens = {t for t in re.findall(r"[A-Za-z_][A-Za-z0-9_]{4,}", block)}
                if tokens and len([t for t in tokens if t not in response.text]) > len(tokens) * 0.2:
                    problems.append(f"{relative}: script embutido ausente ({len(block)} bytes)")

        print(f"1. Paginas          : {totals['paginas']} servidas, "
              f"{totals['redirecionamentos']} redirecionamento(s)")
        # Um verificador que compara zero coisas tambem diz "nenhum problema"; o denominador e a prova.
        print(f"   CSS embutido comparado : {totals['blocos_css']} blocos, {totals['bytes_css']:,} bytes")
        print(f"   JS embutido comparado  : {totals['blocos_js']} blocos, {totals['bytes_js']:,} bytes")
        print(f"   Imagens no HTML        : {totals['imagens']} referencias conferidas")

        print(f"\n2. Assets referenciados: {len(assets_needed)} distintos, conferidos byte a byte")
        faltando, diferentes = [], []
        for asset, usado_por in sorted(assets_needed.items()):
            local = SOURCE / asset
            served = client.get("/" + asset)
            if served.status_code != 200:
                faltando.append(f"{asset} -> HTTP {served.status_code} (usado por {len(usado_por)} pagina(s))")
                continue
            if local.is_file():
                origem, publicado = local.read_bytes(), served.content
                if hashlib.sha256(origem).hexdigest() != hashlib.sha256(publicado).hexdigest():
                    diferentes.append(f"{asset}: {len(origem)} bytes no original, {len(publicado)} publicados")
        print(f"   ausentes  : {len(faltando)}")
        for item in faltando:
            print(f"      {item}")
        print(f"   divergentes: {len(diferentes)}")
        for item in diferentes:
            print(f"      {item}")
        problems.extend(faltando + diferentes)

        print(f"\n3. Links internos entre paginas: {len(pages_linked)} alvos distintos")
        quebrados = []
        for alvo, origem in sorted(pages_linked.items()):
            destino = route_for(alvo) if (SOURCE / alvo).exists() else "/" + alvo
            resposta = client.get(destino)
            if resposta.status_code != 200:
                quebrados.append(f"{destino} -> HTTP {resposta.status_code} (citado em {sorted(origem)[:2]})")
        print(f"   quebrados: {len(quebrados)}")
        for item in quebrados:
            print(f"      {item}")
        problems.extend(quebrados)

        print("\n4. Enderecos antigos .html")
        redirecionados = 0
        for path in pages:
            relative = path.relative_to(SOURCE).as_posix()
            antiga = client.get("/" + relative)
            if antiga.status_code != 200:
                problems.append(f"/{relative} -> HTTP {antiga.status_code}")
            else:
                redirecionados += 1
        print(f"   {redirecionados} de {len(pages)} respondem")

    print(f"\n{'=' * 64}")
    if problems:
        print(f"{len(problems)} problema(s) encontrado(s)")
        return 1
    print("Nenhum problema: toda pagina, asset, link e endereco antigo conferem.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
