"""Deterministically migrate the owned website into static React content.

No original scripts or event handlers are retained. Original articles are sanitized
at import-time; landing-page copy stays structured JSON. Run from apps/web.
"""
from pathlib import Path
from html.parser import HTMLParser
from html import escape, unescape
import re, json

root = Path(__file__).resolve().parents[3]
source = root / '.local/references/website'
output = Path(__file__).resolve().parents[1] / 'content'
output.mkdir(exist_ok=True)

class Clean(HTMLParser):
    allowed = {'p','h2','h3','h4','ul','ol','li','strong','em','blockquote','br','a','table','thead','tbody','tr','td','th','code','pre'}
    def __init__(self):
        super().__init__(); self.parts=[]; self.blocked=0
    def handle_starttag(self,tag,attrs):
        if tag in ('script','style','iframe'): self.blocked += 1
        if self.blocked or tag not in self.allowed: return
        attr=''
        if tag=='a':
            href=dict(attrs).get('href','')
            if href.startswith(('https://','http://','mailto:','/','#','../')):
                href=href.replace('../../index.html','/').replace('../../','/').replace('../artigos/','/blog/artigos/')
                href=re.sub(r'\.html(?=#|$)','',href)
                attr=' href="'+escape(href,quote=True)+'"'
        self.parts.append('<'+tag+attr+'>')
    def handle_endtag(self,tag):
        if tag in ('script','style','iframe'): self.blocked=max(0,self.blocked-1); return
        if not self.blocked and tag in self.allowed and tag!='br': self.parts.append('</'+tag+'>')
    def handle_data(self,data):
        if not self.blocked: self.parts.append(escape(data))

def plaintext(s): return unescape(re.sub('<[^>]+>','',s)).strip()
articles=[]
for path in sorted((source/'blog/artigos').glob('*.html')):
    raw=path.read_text(encoding='utf-8-sig')
    body=re.search(r'<article[^>]*>(.*?)</article>',raw,re.S)
    if not body: raise ValueError(f'Article not found: {path}')
    parser=Clean(); parser.feed(body.group(1))
    title=re.search(r'<h1[^>]*>(.*?)</h1>',raw,re.S)
    description=re.search(r'<meta name="description" content="([^"]*)"',raw)
    date=re.search(r'<time datetime="([^"]*)"',raw)
    articles.append({'slug':path.stem,'title':plaintext(title.group(1)),'description':unescape(description.group(1)) if description else '', 'published':date.group(1) if date else '2026-03-24','html':''.join(parser.parts),'source':str(path.relative_to(source)).replace('\\','/')})
raw=(source/'lp/data.js').read_text(encoding='utf-8-sig')
lp=json.loads(raw[raw.index('{',raw.index('window.__fatShowcaseConfigs')):raw.rindex('};')+1])
(output/'articles.json').write_text(json.dumps(articles,ensure_ascii=False,indent=2),encoding='utf-8')
(output/'landing-pages.json').write_text(json.dumps(lp,ensure_ascii=False,indent=2),encoding='utf-8')
print(f'Migrated {len(articles)} articles and {len(lp)} landing pages.')
