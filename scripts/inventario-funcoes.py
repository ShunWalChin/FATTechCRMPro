"""Levanta toda funcao publica do sistema e mede o uso que cada uma tem.

As outras matrizes deste projeto perguntam "o sistema faz o que promete?". Esta pergunta outra
coisa: **o que foi construido esta sendo usado?**. Sao perguntas diferentes e a segunda quase nunca
e feita, porque a resposta incomoda: toda base carrega rota que nenhuma tela chama, endpoint que
nenhum teste toca e tabela que so o migrador conhece.

Uso aqui nao e opiniao. Cada rota e cruzada com tres fontes independentes, e cada uma responde uma
pergunta diferente:

  TELA    -- alguma coisa em apps/web chama este caminho? Sem isso a funcao existe so para quem
             sabe montar a requisicao na mao.
  TESTE   -- algum teste de API ou de navegador exerce este caminho? Sem isso ninguem descobre
             quando ela quebra, e ela quebra em silencio na proxima refatoracao.
  DOC     -- apps/api/API.md descreve? Sem isso ninguem de fora do time a encontra.

Uma rota sem nenhuma das tres nao e necessariamente lixo: pode ser integracao legitima consumida
por chave de API. Mas ela precisa ser *declarada* como tal, e nao descoberta por acaso um ano
depois. ORFA aqui significa "ninguem explicou", nao "pode apagar".

O denominador aparece em toda linha do relatorio. Saber que ha 3 rotas orfas nao vale nada sem
saber que foram 117 conferidas: um inventario que enxerga pouco tambem termina sem achar orfa.

Uso: python scripts/inventario-funcoes.py [--orfas]
"""
import pathlib
import re
import sys
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps/api"))

from fattech.config import Settings      # noqa: E402
from fattech.db import Base              # noqa: E402
from fattech.main import create_app      # noqa: E402
from fattech.schemas import RESOURCES    # noqa: E402
from fattech import models               # noqa: F401,E402

WEB = ROOT / "apps/web"
API_TESTS = ROOT / "apps/api/tests"
E2E = ROOT / "tests/e2e"
API_DOC = ROOT / "apps/api/API.md"
# Rotas que a infraestrutura chama, nunca uma tela. Declaradas para nao poluirem o relatorio de
# orfas com falso positivo -- e declaradas *aqui*, visiveis, em vez de filtradas em silencio.
INFRAESTRUTURA = {
    "/api/health": "sonda de saude do contêiner e do balanceador",
    "/api/v1/health": "sonda de saude autenticada",
    "/api/v1/webhooks/n8n": "entrada HMAC do n8n; nao ha tela que a chame",
    "/api/public/webhooks/instagram": "verificacao e entrega da Meta; assinada, sem tela",
    "/api/openapi.json": "esquema gerado pelo FastAPI",
    "/docs/oauth2-redirect": "interface do FastAPI",
}


def fontes(diretorio: pathlib.Path, *sufixos: str) -> str:
    return "\n".join(arquivo.read_text(encoding="utf-8", errors="replace")
                     for sufixo in sufixos for arquivo in diretorio.rglob(f"*{sufixo}")
                     if "node_modules" not in arquivo.parts and ".next" not in arquivo.parts)


def segmentos(caminho: str) -> list[str]:
    """Pedacos literais do caminho, sem os parametros.

    `/api/v1/contracts/{contract_id}/revisions` e escrito no cliente como
    `/contracts/${c.id}/revisions`: o que sobrevive a interpolacao sao os literais, e e por eles
    que a busca precisa ser feita. Procurar o caminho inteiro nao encontraria nada e o inventario
    declararia orfa toda rota com parametro -- metade delas, todas falsas.
    """
    return [parte for parte in caminho.split("/") if parte and not parte.startswith("{")]


def usado_em(texto: str, caminho: str) -> bool:
    """Primeiro e ultimo literal do caminho, com qualquer interpolacao no meio.

    A primeira versao excluia aspas do trecho do meio, para nao atravessar a fronteira de uma
    string. Isso parecia prudente e estava errado: o teste escreve
    `f"/api/v1/contracts/{contrato['id']}/revisions"`, e a interpolacao de um f-string **contem
    aspas**. O inventario declarou sem teste nove rotas cobertas por testes que eu mesmo tinha
    acabado de rodar verdes -- numeros confiantes e falsos, que e o pior resultado possivel para
    um medidor. O autoteste no fim deste arquivo existe por causa disso.
    """
    uteis = [p for p in segmentos(caminho) if p not in ("api", "v1")]
    if not uteis:
        return False
    if len(uteis) == 1:
        return re.search(rf"[`'\"/]{re.escape(uteis[0])}[`'\"?/\\]", texto) is not None
    # O limite de 60 caracteres e o que impede a busca de emendar dois caminhos diferentes da
    # mesma linha; a quebra de linha continua sendo fronteira absoluta.
    return re.search(rf"/{re.escape(uteis[0])}[^\n]{{0,60}}/{re.escape(uteis[-1])}\b", texto) is not None


# (rota, fonte, esperado) -- casos cuja resposta eu conferi a mao. Se o casador mudar e quebrar
# um destes, o inventario para em vez de publicar um numero errado com confianca.
AUTOTESTE = [
    ("/api/v1/contracts/{contract_id}/revisions", "testes", True),
    ("/api/v1/contacts/{record_id}/merge", "testes", True),
    ("/api/v1/crm/leads/{record_id}/score", "testes", True),
    ("/api/v1/campaigns", "testes", False),
    ("/api/v1/content/indicadores", "web", True),
    ("/api/v1/audit/verify", "testes", True),
]


def conferir_casador(web: str, testes: str) -> list[str]:
    falhas = []
    for caminho, fonte, esperado in AUTOTESTE:
        obtido = usado_em(web if fonte == "web" else testes, caminho)
        if obtido != esperado:
            falhas.append(f"{caminho} em {fonte}: esperado {esperado}, obtido {obtido}")
    return falhas


def grupo_de(caminho: str) -> str:
    partes = segmentos(caminho)
    if caminho.startswith("/webhooks") or caminho.startswith("/api/public"):
        return "entrada externa"
    uteis = [p for p in partes if p not in ("api", "v1")]
    if not uteis:
        return "raiz"
    cabeca = uteis[0]
    if cabeca in RESOURCES:
        return "domínio CRUD"
    return {"auth": "autenticação", "team": "equipe", "audit": "auditoria", "api-keys": "chaves de API",
            "crm": "operação comercial", "sales": "operação comercial", "contracts": "contratos",
            "content": "operação de conteúdo", "core": "motor de eventos", "synapse": "SYNAPSE",
            "instagram": "canais", "events": "motor de eventos", "knowledge": "conhecimento",
            "records": "registros", "dashboard": "painéis", "notifications": "painéis",
            }.get(cabeca, cabeca)


def main() -> int:
    so_orfas = "--orfas" in sys.argv
    app = create_app(Settings(_env_file=None, env="test", database_url="sqlite:///:memory:"))
    rotas = {}
    for rota in app.routes:
        if not hasattr(rota, "path"):
            continue
        metodos = sorted(getattr(rota, "methods", set()) - {"HEAD", "OPTIONS"})
        rotas.setdefault(rota.path, set()).update(metodos)

    web = fontes(WEB / "components", ".tsx") + fontes(WEB / "lib", ".ts") + fontes(WEB / "app", ".tsx")
    testes = fontes(API_TESTS, ".py") + fontes(E2E, ".ts")
    doc = API_DOC.read_text(encoding="utf-8", errors="replace") if API_DOC.exists() else ""

    falhas = conferir_casador(web, testes)
    if falhas:
        print("O casador de caminhos está errado; o inventário seria confiante e falso:")
        for falha in falhas:
            print(f"   - {falha}")
        return 1

    linhas = []
    for caminho in sorted(rotas):
        linhas.append({
            "caminho": caminho, "metodos": "/".join(sorted(rotas[caminho])) or "-",
            "grupo": grupo_de(caminho),
            "tela": usado_em(web, caminho), "teste": usado_em(testes, caminho),
            "doc": usado_em(doc, caminho), "infra": INFRAESTRUTURA.get(caminho, ""),
        })

    print("INVENTÁRIO DE FUNÇÕES DO SISTEMA — o que existe e quem usa\n")
    print(f"Denominador: {len(linhas)} rotas, {len(RESOURCES)} domínios, "
          f"{len(Base.metadata.tables)} tabelas, {len(list((WEB / 'app').rglob('page.tsx')))} telas\n")

    por_grupo = defaultdict(list)
    for linha in linhas:
        por_grupo[linha["grupo"]].append(linha)

    if not so_orfas:
        print(f"{'GRUPO':22} {'ROTAS':>6} {'TELA':>6} {'TESTE':>6} {'DOC':>5}  COBERTURA")
        print("-" * 78)
        for grupo in sorted(por_grupo, key=lambda g: -len(por_grupo[g])):
            conjunto = por_grupo[grupo]
            tela = sum(1 for l in conjunto if l["tela"])
            teste = sum(1 for l in conjunto if l["teste"])
            documentada = sum(1 for l in conjunto if l["doc"])
            # Cobertura pondera o que importa para quem mantem: uma rota testada vale mais que uma
            # documentada, porque o teste avisa quando ela quebra e o documento nao.
            cobertura = (teste * 0.6 + tela * 0.3 + documentada * 0.1) / len(conjunto) * 100
            print(f"{grupo:22} {len(conjunto):>6} {tela:>6} {teste:>6} {documentada:>5}  {cobertura:>3.0f}%")
        print("-" * 78)
        total = len(linhas)
        for rotulo, chave in (("Chamadas por alguma tela", "tela"), ("Exercidas por algum teste", "teste"),
                              ("Descritas na API.md", "doc")):
            quantas = sum(1 for l in linhas if l[chave])
            print(f"{rotulo:28} {quantas:>4} de {total}  ({quantas / total * 100:.0f}%)")

    orfas = [l for l in linhas if not (l["tela"] or l["teste"] or l["doc"]) and not l["infra"]]
    declaradas = [l for l in linhas if l["infra"]]
    sem_teste = [l for l in linhas if not l["teste"] and not l["infra"]]

    print(f"\nSEM TESTE NENHUM ({len(sem_teste)} de {len(linhas)}) — quebram em silêncio")
    for linha in sem_teste[:30]:
        marca = "tela" if linha["tela"] else ("doc" if linha["doc"] else "nada")
        print(f"   {linha['metodos']:16} {linha['caminho']:52} ({marca})")
    if len(sem_teste) > 30:
        print(f"   ... e mais {len(sem_teste) - 30}")

    print(f"\nÓRFÃS ({len(orfas)} de {len(linhas)}) — nenhuma tela, nenhum teste, nenhuma linha de documento")
    for linha in orfas:
        print(f"   {linha['metodos']:16} {linha['caminho']}")
    if not orfas:
        print("   nenhuma")

    print(f"\nINFRAESTRUTURA DECLARADA ({len(declaradas)}) — sem tela de propósito")
    for linha in declaradas:
        print(f"   {linha['caminho']:40} {linha['infra']}")

    print("\nÓRFÃ aqui significa 'ninguém explicou para que serve', não 'pode apagar'. Uma rota")
    print("consumida por chave de API é legítima — e precisa estar declarada em INFRAESTRUTURA,")
    print("não descoberta por acaso um ano depois.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
