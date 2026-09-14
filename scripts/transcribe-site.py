"""Transcribe the original FAT Tech website into this project's stack, without redesigning it.

The design lives in the original stylesheets, so they are carried over byte for byte and the
transcription only moves structure: HTML body into JSX, <head> into Next metadata. Doing this by hand
across 49 pages would guarantee drift; doing it by rule makes the result reproducible and lets a
separate check compare the rendered output against the original.

Usage: python scripts/transcribe-site.py [--only path.html]
"""
import argparse
import html
import json
import pathlib
import re
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parents[1]
# The originals are the reference the transcription is checked against, not a second public copy:
# left under public/ they would be served in parallel with the site and duplicate every page.
SOURCE = ROOT / "apps/web/site-original"
PAGES = ROOT / "apps/web/app/(site)"

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "param", "source", "track", "wbr"}
# React renames a handful of HTML attributes and camelCases every hyphenated SVG one.
RENAMED = {"class": "className", "for": "htmlFor", "tabindex": "tabIndex", "readonly": "readOnly",
           "maxlength": "maxLength", "minlength": "minLength", "colspan": "colSpan",
           "rowspan": "rowSpan", "srcset": "srcSet", "autocomplete": "autoComplete",
           "autofocus": "autoFocus", "novalidate": "noValidate", "enctype": "encType",
           "datetime": "dateTime", "accesskey": "accessKey", "contenteditable": "contentEditable",
           "spellcheck": "spellCheck", "crossorigin": "crossOrigin", "usemap": "useMap",
           "frameborder": "frameBorder", "allowfullscreen": "allowFullScreen", "playsinline": "playsInline",
           "http-equiv": "httpEquiv", "charset": "charSet", "cellpadding": "cellPadding",
           "cellspacing": "cellSpacing", "marginwidth": "marginWidth", "marginheight": "marginHeight"}
# Attributes that are boolean in HTML and must become `{true}` rather than an empty string.
BOOLEAN = {"defer", "async", "checked", "disabled", "required", "readonly", "multiple", "selected",
           "hidden", "autofocus", "novalidate", "open", "controls", "loop", "muted", "playsinline",
           "allowfullscreen", "reversed", "ismap", "default", "itemscope"}
# React types these as numbers, so a quoted digit string is a type error rather than a detail.
NUMERIC = {"rows", "cols", "size", "span", "start", "tabindex", "colspan", "rowspan",
           "maxlength", "minlength"}
BLOCK = {"section", "div", "header", "footer", "nav", "main", "article", "aside", "ul", "ol", "li",
         "h1", "h2", "h3", "h4", "h5", "h6", "p", "form", "table", "tr", "figure", "script", "style", "svg"}


def attribute_name(name: str) -> str:
    if name in RENAMED:
        return RENAMED[name]
    if name.startswith(("aria-", "data-")):
        return name
    if name == "viewbox":
        return "viewBox"
    if name.startswith("xlink:"):
        return "xlinkHref" if name == "xlink:href" else name.replace(":", "")
    if name.startswith("xmlns"):
        return name.replace(":", "")
    if "-" in name:  # SVG presentation attributes: stroke-width -> strokeWidth
        head, *rest = name.split("-")
        return head + "".join(part.capitalize() for part in rest)
    return name


ABSOLUTE = ("http://", "https://", "//", "#", "mailto:", "tel:", "data:", "javascript:")
# /crm is the private workspace in this application, so the original page keeps its own URL instead of
# quietly taking a route that already belongs to something else.
KEEP_URL = {"crm.html": "/crm.html"}


def resolve_reference(value: str, page_dir: pathlib.PurePosixPath) -> str:
    """Turn a reference relative to the original page into one the new routing can serve."""
    if not value or value.startswith(ABSOLUTE):
        return value
    path, _, fragment = value.partition("#")
    suffix = f"#{fragment}" if fragment else ""
    if not path:
        return value
    resolved = pathlib.PurePosixPath(page_dir / path)
    parts: list[str] = []
    for part in resolved.parts:
        if part == "..":
            if parts:
                parts.pop()
        elif part not in (".", ""):
            parts.append(part)
    target = "/".join(parts)
    if target in KEEP_URL:
        return KEEP_URL[target] + suffix
    if target.endswith("/"):
        target = target.rstrip("/")
    if target.endswith(".html"):
        route = route_for(target)
        return (f"/{route}" if route else "/") + suffix
    if not pathlib.PurePosixPath(target).suffix:  # a directory link such as impulse-crm/
        return f"/{target}{suffix}"
    return f"/{target}{suffix}"


def style_object(value: str) -> str:
    entries = []
    for part in value.split(";"):
        if ":" not in part:
            continue
        prop, _, raw = part.partition(":")
        prop, raw = prop.strip(), raw.strip()
        if not prop:
            continue
        key = prop if prop.startswith("--") else re.sub(r"-(\w)", lambda m: m.group(1).upper(), prop)
        quoted = json.dumps(raw)
        entries.append(f"{json.dumps(key)}:{quoted}" if prop.startswith("--") else f"{key}:{quoted}")
    return "{{" + ",".join(entries) + "}}"


ESCAPES = {"{": "{'{'}", "}": "{'}'}", "<": "{'<'}", ">": "{'>'}"}


def jsx_text(text: str) -> str:
    """Braces open an expression in JSX and a bare angle bracket starts a tag, so text escapes both.

    One pass, not four: replacing `{` first produces a `}` that a later pass would rewrite again.
    """
    return re.sub(r"[{}<>]", lambda m: ESCAPES[m.group(0)], text)


class Transcriber(HTMLParser):
    def __init__(self, page_dir: pathlib.PurePosixPath):
        super().__init__(convert_charrefs=True)
        self.page_dir = page_dir
        self.out: list[str] = []
        self.depth = 0
        self.raw_tag: str | None = None
        self.raw_buffer: list[str] = []
        self.raw_attrs: list[tuple[str, str | None]] = []
        self.in_body = False
        self.body_depth = 0

    def emit(self, text: str):
        if self.in_body:
            self.out.append(text)

    def handle_starttag(self, tag, attrs):
        if tag == "body":
            self.in_body = True
            return
        if not self.in_body:
            return
        if tag in ("script", "style"):
            self.raw_tag, self.raw_buffer, self.raw_attrs = tag, [], attrs
            return
        self.emit(self.open_tag(tag, attrs, closed=tag in VOID))

    def handle_startendtag(self, tag, attrs):
        if self.in_body:
            self.emit(self.open_tag(tag, attrs, closed=True))

    def handle_endtag(self, tag):
        if tag == "body":
            self.in_body = False
            return
        if not self.in_body:
            return
        if self.raw_tag == tag:
            self.flush_raw()
            return
        if tag not in VOID:
            self.emit(f"</{tag}>")

    def handle_data(self, data):
        if self.raw_tag is not None:
            self.raw_buffer.append(data)
            return
        if not self.in_body or not data.strip():
            # Whitespace between elements still matters for inline layout; keep a single space.
            if self.in_body and data and data.strip() == "" and "\n" not in data:
                self.emit(" ")
            return
        self.emit(jsx_text(data))

    def handle_comment(self, data):
        if self.in_body and self.raw_tag is None:
            self.emit("{/*" + data.replace("*/", "*\\/") + "*/}")

    def open_tag(self, tag, attrs, closed: bool) -> str:
        rendered = []
        for name, value in attrs:
            lowered = name.lower()
            if re.fullmatch(r"on[a-z]+", lowered):
                # The original keeps its behaviour in external scripts. If that ever stops being true,
                # silently dropping a handler would remove behaviour nobody asked to remove.
                raise SystemExit(f"handler inline em <{tag} {lowered}>: porte-o antes de transcrever")
            react = attribute_name(lowered)
            if value is None or (lowered in BOOLEAN and value in ("", lowered)):
                rendered.append(f"{react}={{true}}")
            elif lowered == "style":
                rendered.append(f"style={style_object(value)}")
            elif lowered in NUMERIC and value.strip().lstrip("-").isdigit():
                rendered.append(f"{react}={{{int(value.strip())}}}")
            elif lowered in ("href", "src", "action", "poster"):
                rendered.append(f"{react}={json.dumps(resolve_reference(html.unescape(value), self.page_dir))}")
            else:
                rendered.append(f"{react}={json.dumps(html.unescape(value))}")
        if tag == "canvas":
            # global-particles.js sizes the canvas before hydration; the difference is the point.
            rendered.append("suppressHydrationWarning")
        joined = (" " + " ".join(rendered)) if rendered else ""
        # A single-line transcription of 100KB of markup is faithful and unreadable; break on blocks.
        lead = "\n" if tag in BLOCK else ""
        return f"{lead}<{tag}{joined}{' />' if closed else '>'}"

    def flush_raw(self):
        tag, attrs, body = self.raw_tag, self.raw_attrs, "".join(self.raw_buffer)
        self.raw_tag, self.raw_buffer, self.raw_attrs = None, [], []
        if tag == "script" and any(name == "src" for name, _ in attrs):
            self.emit(self.open_tag("script", attrs, closed=False) + "</script>")
            return
        if not body.strip():
            return
        self.emit(self.open_tag(tag, attrs, closed=False)[:-1]
                  + f" dangerouslySetInnerHTML={{{{__html:{json.dumps(body)}}}}} />")


def head_metadata(head: str, route: str) -> str:
    def meta(pattern: str) -> str | None:
        found = re.search(pattern, head, re.I)
        return html.unescape(found.group(1)) if found else None

    title = meta(r"<title>(.*?)</title>") or "FAT Tech"
    description = meta(r'<meta\s+name="description"\s+content="([^"]*)"') or ""
    canonical = meta(r'<link\s+rel="canonical"\s+href="([^"]*)"')
    og_title = meta(r'<meta\s+property="og:title"\s+content="([^"]*)"') or title
    og_desc = meta(r'<meta\s+property="og:description"\s+content="([^"]*)"') or description
    og_image = meta(r'<meta\s+property="og:image"\s+content="([^"]*)"')
    keywords = meta(r'<meta\s+name="keywords"\s+content="([^"]*)"')
    parts = [f"title:{json.dumps(title)}", f"description:{json.dumps(description)}"]
    if keywords:
        parts.append("keywords:" + json.dumps([k.strip() for k in keywords.split(",") if k.strip()]))
    if canonical:
        parts.append(f"alternates:{{canonical:{json.dumps(canonical)}}}")
    og = [f"title:{json.dumps(og_title)}", f"description:{json.dumps(og_desc)}", 'type:"website"',
          'locale:"pt_BR"', 'siteName:"FAT Tech"']
    if og_image:
        og.append(f"images:[{json.dumps(og_image)}]")
    og_url = meta(r'<meta\s+property="og:url"\s+content="([^"]*)"')
    if og_url:
        og.append(f"url:{json.dumps(og_url)}")
    author = meta(r'<meta\s+name="author"\s+content="([^"]*)"')
    if author:
        parts.append("authors:[{name:" + json.dumps(author) + "}]")
    robots = meta(r'<meta\s+name="robots"\s+content="([^"]*)"')
    if robots:
        directives = {d.strip().lower() for d in robots.split(",")}
        parts.append("robots:{index:" + ("true" if "index" in directives else "false")
                     + ",follow:" + ("true" if "follow" in directives else "false") + "}")
    twitter = {key: meta(rf'<meta\s+name="twitter:{key}"\s+content="([^"]*)"')
               for key in ("card", "title", "description", "image")}
    declared = {key: value for key, value in twitter.items() if value}
    if declared:
        fields = {("images" if key == "image" else key): ([value] if key == "image" else value)
                  for key, value in declared.items()}
        parts.append("twitter:{" + ",".join(f"{k}:{json.dumps(v)}" for k, v in fields.items()) + "}")
    parts.append("openGraph:{" + ",".join(og) + "}")
    metadata = "export const metadata:Metadata={" + ",".join(parts) + "};"
    # Next moved the viewport tag and theme colour out of metadata; the original values travel with them.
    content = meta(r'<meta\s+name="viewport"\s+content="([^"]*)"') or "width=device-width, initial-scale=1"
    theme = meta(r'<meta\s+name="theme-color"\s+content="([^"]*)"')
    viewport = ["width:\"device-width\"", "initialScale:1"]
    if "viewport-fit=cover" in content:
        viewport.append('viewportFit:"cover"')
    if theme:
        viewport.append(f"themeColor:{json.dumps(theme)}")
    return metadata + "\nexport const viewport:Viewport={" + ",".join(viewport) + "};"


def head_links(head: str, page_dir: pathlib.PurePosixPath) -> str:
    """The design is in the stylesheets, and which ones a page loads differs page by page.

    React hoists a <link> rendered anywhere in the tree into the document head, so each page carries
    exactly the sheets the original carried, in the original order.
    """
    rendered = []
    for tag in re.findall(r"<link\b[^>]*>", head, re.I):
        rel = re.search(r'rel="([^"]+)"', tag, re.I)
        href = re.search(r'href="([^"]+)"', tag, re.I)
        if not rel or not href or rel.group(1).lower() not in ("stylesheet", "preconnect"):
            continue
        attrs = [f'rel={json.dumps(rel.group(1))}',
                 f'href={json.dumps(resolve_reference(html.unescape(href.group(1)), page_dir))}']
        if re.search(r'\bcrossorigin\b', tag, re.I):
            attrs.append('crossOrigin="anonymous"')
        rendered.append("<link " + " ".join(attrs) + " />")
    return "\n".join(rendered)


def route_for(relative: str) -> str:
    if relative == "index.html":
        return ""
    if relative.endswith("/index.html"):
        return relative[: -len("/index.html")]
    return relative[: -len(".html")]


def transcribe(path: pathlib.Path) -> tuple[str, str]:
    source = path.read_text(encoding="utf-8")
    head = source[source.index("<head"): source.index("</head>")]
    relative_dir = pathlib.PurePosixPath(path.relative_to(SOURCE).as_posix()).parent
    parser = Transcriber(relative_dir)
    parser.feed(source)
    parser.close()
    relative = path.relative_to(SOURCE).as_posix()
    route = KEEP_URL.get(relative, '').lstrip('/') or route_for(relative)
    component = "".join(parser.out)
    page = (
        "import type {Metadata, Viewport} from 'next';\n"
        f"// Transcrita do site original ({relative}) por scripts/transcribe-site.py.\n"
        "// Conteudo e marcacao sao os do original; o que mudou foi apenas a stack em volta.\n"
        f"{head_metadata(head, route)}\n"
        "export default function Page(){\n  return <>\n"
        f"{head_links(head, relative_dir)}"
        f"{component}\n"
        "  </>;\n}\n"
    )
    return route, page


def redirect_target(source: str, page_dir: pathlib.PurePosixPath) -> str | None:
    """A meta-refresh page is a redirect wearing a page's clothes; the stack has a redirect for that."""
    found = re.search(r'<meta[^>]+http-equiv="refresh"[^>]+content="[^"]*url=([^"\s]+)"', source, re.I)
    return resolve_reference(found.group(1), page_dir) if found else None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--only")
    args = parser.parse_args()
    targets = ([SOURCE / args.only] if args.only
               else sorted(p for p in SOURCE.rglob("*.html")))
    redirects: list[tuple[str, str]] = []
    for path in targets:
        relative = path.relative_to(SOURCE).as_posix()
        source = path.read_text(encoding="utf-8")
        destination = redirect_target(source, pathlib.PurePosixPath(relative).parent)
        if destination:
            # The stub's own URL is what someone may have bookmarked, so that is what redirects.
            redirects.append((f"/{relative}", destination))
            print(f"{relative:48} -> redirect {destination}")
            continue
        route, page = transcribe(path)
        target = PAGES / route / "page.tsx" if route else PAGES / "page.tsx"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(page, encoding="utf-8")
        print(f"{path.relative_to(SOURCE).as_posix():48} -> {target.relative_to(ROOT).as_posix()}")
    if redirects and not args.only:
        # Written as data so next.config.ts states the same redirects the original site stated.
        (PAGES / "redirects.json").write_text(
            json.dumps([{"source": s, "destination": d, "permanent": True} for s, d in redirects],
                       ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"\n{len(redirects)} redirecionamento(s) em app/(site)/redirects.json")


if __name__ == "__main__":
    main()
