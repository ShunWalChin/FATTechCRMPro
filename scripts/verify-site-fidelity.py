"""Compare every transcribed page against the original HTML it came from.

Fidelity is a claim until something checks it. This renders each route from the running application and
compares two things against the original file: the visible text, and the sequence of elements with
their classes. The first catches lost or altered content; the second catches markup that drifted.

Usage: python scripts/verify-site-fidelity.py [--base http://127.0.0.1:3100]
"""
import argparse
import difflib
import pathlib
import re
import sys
from html.parser import HTMLParser

import httpx

ABSOLUTE = ("http://", "https://", "//", "#", "mailto:", "tel:", "data:", "javascript:")


def resolve_reference(value: str, page_dir: pathlib.PurePosixPath) -> str:
    """Same resolution the transcription applied, restated here so the check does not trust it."""
    if not value or value.startswith(ABSOLUTE):
        return value
    parts: list[str] = []
    for part in pathlib.PurePosixPath(page_dir / value).parts:
        if part == "..":
            if parts:
                parts.pop()
        elif part not in (".", ""):
            parts.append(part)
    return "/" + "/".join(parts)

ROOT = pathlib.Path(__file__).resolve().parents[1]
# The originals are the reference the transcription is checked against, not a second public copy:
# left under public/ they would be served in parallel with the site and duplicate every page.
SOURCE = ROOT / "apps/web/site-original"
SKIP_TAGS = {"script", "style", "noscript", "template"}


class Reader(HTMLParser):
    """Collect visible text and an element/class outline from a document body."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.text: list[str] = []
        self.outline: list[str] = []
        self.sheets: list[str] = []
        self.in_body = False
        self.muted = 0

    def handle_starttag(self, tag, attrs):
        if tag == "body":
            self.in_body = True
            return
        if not self.in_body:
            return
        if tag in SKIP_TAGS:
            self.muted += 1
            return
        attributes = dict(attrs)
        if tag == "link":
            # The original declares stylesheets in <head>; React hoists the same links from the tree.
            # Where they sit in the markup is the framework's business, so the set is compared apart.
            if (attributes.get("rel") or "").lower() == "stylesheet" and attributes.get("href"):
                self.sheets.append(attributes["href"])
            return
        if tag == "div" and "hidden" in attributes and not attributes.get("class"):
            return  # Next's streaming placeholder: framework plumbing, not content.
        classes = " ".join(sorted((attributes.get("class") or "").split()))
        self.outline.append(f"{tag}.{classes}" if classes else tag)

    def handle_endtag(self, tag):
        if tag == "body":
            self.in_body = False
        elif tag in SKIP_TAGS and self.muted:
            self.muted -= 1

    def handle_data(self, data):
        if self.in_body and not self.muted and data.strip():
            self.text.append(" ".join(data.split()))


def read(markup: str, whole_document: bool = False) -> tuple[list[str], list[str], list[str]]:
    reader = Reader()
    if whole_document:
        reader.in_body = True  # the original keeps its stylesheets in <head>
    reader.feed(markup)
    reader.close()
    return reader.text, reader.outline, reader.sheets


def declared_meta(markup: str) -> dict[str, str]:
    """Every meta the original states, by name. Losing or changing one is a failure; the framework
    mirroring Open Graph into extra Twitter tags adds nothing the original denied."""
    found = {}
    head = markup[: markup.index("</head>")] if "</head>" in markup else markup
    for tag in re.findall(r"<meta[^>]*>", head, re.I):
        key = re.search(r'(?:name|property)="([^"]+)"', tag, re.I)
        value = re.search(r'content="([^"]*)"', tag, re.I)
        if key and value and key.group(1).lower() not in ("viewport", "theme-color"):
            found[key.group(1).lower()] = " ".join(value.group(1).split())
    return found


def rendered_meta(markup: str) -> dict[str, str]:
    return declared_meta(markup)


def route_for(relative: str) -> str:
    if relative == "crm.html":
        return "/crm.html"
    if relative == "index.html":
        return "/"
    if relative.endswith("/index.html"):
        return "/" + relative[: -len("/index.html")]
    return "/" + relative[: -len(".html")]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:3100")
    parser.add_argument("--show", type=int, default=6, help="linhas de diferenca por pagina")
    args = parser.parse_args()

    pages = sorted(p for p in SOURCE.rglob("*.html"))
    failures = 0
    with httpx.Client(base_url=args.base, timeout=60, follow_redirects=True) as client:
        for path in pages:
            relative = path.relative_to(SOURCE).as_posix()
            original = path.read_text(encoding="utf-8")
            if re.search(r'http-equiv="refresh"', original, re.I):
                route = "/" + relative
                response = client.get(route)
                ok = response.status_code == 200 and str(response.url).rstrip("/") != args.base + route
                print(f"{'OK   ' if ok else 'FALHA'} {relative:46} redireciona -> {response.url}")
                failures += 0 if ok else 1
                continue
            route = route_for(relative)
            response = client.get(route)
            if response.status_code != 200:
                print(f"FALHA {relative:46} HTTP {response.status_code} em {route}")
                failures += 1
                continue
            want_text, want_outline, want_sheets = read(original, whole_document=True)
            got_text, got_outline, got_sheets = read(response.text, whole_document=True)
            problems = []
            page_dir = pathlib.PurePosixPath(relative).parent
            # Escaping a literal "<" splits one text run into three nodes. The characters a reader sees
            # are what fidelity means, so the comparison is on the continuous text, not its segmentation.
            if " ".join(want_text).split() != " ".join(got_text).split():
                diff = [line for line in difflib.unified_diff(want_text, got_text, "original", "transcrito", n=0)
                        if line.startswith(("+", "-")) and not line.startswith(("+++", "---"))]
                problems.append(("texto", diff))
            missing = [f"{k}={v}" for k, v in declared_meta(original).items()
                       if rendered_meta(response.text).get(k) != v]
            if missing:
                problems.append(("meta perdido", missing))
            expected_sheets = [resolve_reference(href, page_dir) for href in want_sheets]
            if expected_sheets != got_sheets:
                problems.append(("folhas", [f"-{h}" for h in expected_sheets] + [f"+{h}" for h in got_sheets]))
            want_shape = [e for e in want_outline if e != "meta"]
            got_shape = [e for e in got_outline if e != "meta"]
            if want_shape != got_shape:
                diff = [line for line in difflib.unified_diff(want_shape, got_shape, "original", "transcrito", n=0)
                        if line.startswith(("+", "-")) and not line.startswith(("+++", "---"))]
                problems.append(("estrutura", diff))
            if not problems:
                print(f"OK    {relative:46} {len(want_text)} blocos de texto, {len(want_outline)} elementos")
                continue
            failures += 1
            print(f"FALHA {relative:46} {', '.join(f'{name}: {len(d)} linhas' for name, d in problems)}")
            for name, diff in problems:
                for line in diff[: args.show]:
                    print(f"        {name[:4]} {line[:150]}")
    print(f"\n{len(pages) - failures} de {len(pages)} paginas fieis")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
