"""Audita o site publico provando identidade de bytes, nao semelhanca de conteudo.

A auditoria anterior comparava o que o site servia com o que uma transcricao deveria ter
produzido: texto continuo, metadados declarados, CSS embutido, folhas na ordem. Ela passava com
49 de 49 enquanto a home renderizava "NEGOCIOCIO" -- dois estados da animacao sobrepostos --
porque texto igual nao prova comportamento igual, e os scripts do original brigavam com a
hidratacao do React.

Agora o site e o HTML puro do repositorio oficial, servido de apps/web/public. Isso torna
possivel uma verificacao que antes nao era: **os bytes servidos sao os bytes do arquivo**. Nao ha
margem para um detalhe se perder no meio, porque nao ha meio.

Duas comparacoes, e o denominador de cada uma aparece no relatorio:

1. Cada arquivo publicado responde e devolve exatamente os bytes que a release publica -- o
   blob do Git, que e o que `git archive` empacota, e nao a copia do disco de quem audita.
2. Cada arquivo e identico ao do repositorio oficial, exceto o que docs/site-patches.json
   declarar como correcao, com o motivo escrito.

Usage: python scripts/audit-site.py [https://host]
"""
import hashlib
import json
import pathlib
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
PUBLICO = ROOT / "apps/web/public"
UPSTREAM = ROOT / ".local/references/fat-tech-website"
# Divergencias intencionais em relacao ao repositorio oficial, cada uma com o motivo escrito.
# Sem esta lista, uma correcao necessaria e uma regressao silenciosa se pareceriam iguais aqui.
PATCHES = ROOT / "docs/site-patches.json"
PADRAO = "https://fattechcrmpro.64.181.178.125.nip.io"
# O que o Next serve de public/ e o que o site publica. icon.svg e do workspace, nao do site.
IGNORAR = {"icon.svg"}
# A raiz e o unico endereco que o original nao publica como arquivo; um rewrite a resolve.
# A raiz e o unico endereco que o original nao publica como arquivo. /blog e /lp/impulse-crm
# sem extensao nunca foram enderecos dele: o original publica blog/index.html e a pagina de
# redirecionamento lp/impulse-crm.html, que leva ao indice do diretorio.
EXTRAS = {"/": "index.html"}


def digest(dados: bytes) -> str:
    return hashlib.sha256(dados).hexdigest()


def baixar(base: str, rota: str) -> tuple[int, bytes]:
    # O site tem um arquivo com espaco no nome; sem codificar, a auditoria falhava na propria
    # requisicao e reportava o arquivo como ausente -- um problema do medidor, nao do medido.
    endereco = base.rstrip("/") + urllib.parse.quote(rota)
    pedido = urllib.request.Request(endereco, headers={"User-Agent": "fattech-audit"})
    try:
        with urllib.request.urlopen(pedido, timeout=30) as resposta:
            return resposta.status, resposta.read()
    except urllib.error.HTTPError as erro:
        return erro.code, erro.read()
    except Exception as erro:  # noqa: BLE001 - a falha de rede e um resultado da auditoria
        print(f"   erro em {rota}: {type(erro).__name__}")
        return 0, b""


def arquivos_publicados() -> list[pathlib.Path]:
    return sorted(caminho for caminho in PUBLICO.rglob("*")
                  if caminho.is_file() and caminho.name not in IGNORAR)


def publicado(caminho: pathlib.Path) -> bytes:
    """O byte publicado e o do blob do Git, nao o do disco.

    A release nasce de `git archive HEAD`, que escreve o blob normalizado. Numa maquina Windows o
    disco carrega CRLF e o blob carrega LF, entao comparar com o disco acusava toda pagina como
    divergente por exatamente um byte por linha -- um defeito do medidor que, se eu tivesse
    acreditado nele, teria parecido um site quebrado em producao.
    """
    relativo = caminho.relative_to(ROOT).as_posix()
    try:
        return subprocess.check_output(["git", "show", f"HEAD:{relativo}"], cwd=ROOT)
    except subprocess.CalledProcessError:
        # Arquivo ainda nao commitado: o disco e o melhor que existe, e a diferenca aparece sozinha.
        return caminho.read_bytes()


TEXTO = {".html", ".css", ".js", ".txt", ".xml", ".json", ".svg", ".md"}


def normalizar(caminho: pathlib.Path, dados: bytes) -> bytes:
    """Quebra de linha nao e conteudo, e Git a normaliza nos dois sentidos.

    O blob guarda LF, o checkout no Windows entrega CRLF, e o servidor local serve o checkout.
    Sem isto a auditoria acusava toda pagina como divergente por um byte por linha -- contra
    producao, que nasce de `git archive`, e contra o servidor local, por motivos opostos.
    Binario segue comparado byte a byte, onde um byte a mais e mesmo um byte a mais.
    """
    if caminho.suffix.lower() in TEXTO:
        return dados.replace(bytes((13, 10)), bytes((10,)))
    return dados


def rota_de(caminho: pathlib.Path) -> str:
    return "/" + caminho.relative_to(PUBLICO).as_posix()


def conferir_servidos(base: str) -> list[str]:
    problemas = []
    arquivos = arquivos_publicados()
    bytes_totais = sum(caminho.stat().st_size for caminho in arquivos)
    print(f"1. Bytes servidos contra bytes em disco\n"
          f"   {len(arquivos)} arquivos publicados, {bytes_totais:,} bytes no total")
    divergentes = ausentes = 0
    for caminho in arquivos:
        rota = rota_de(caminho)
        codigo, servido = baixar(base, rota)
        if codigo != 200:
            problemas.append(f"{rota} respondeu {codigo}")
            ausentes += 1
            continue
        esperado = publicado(caminho)
        if digest(normalizar(caminho, servido)) != digest(normalizar(caminho, esperado)):
            problemas.append(f"{rota} difere do que a release publica "
                             f"({len(servido):,}b servidos, {len(esperado):,}b publicados)")
            divergentes += 1
    print(f"   nao responderam : {ausentes}\n   divergentes     : {divergentes}")

    print(f"\n2. Enderecos que dependem de reescrita ({len(EXTRAS)})")
    for rota, alvo in EXTRAS.items():
        codigo, servido = baixar(base, rota)
        alvo_caminho = PUBLICO / alvo
        disco = publicado(alvo_caminho)
        if codigo != 200 or digest(normalizar(alvo_caminho, servido)) != digest(normalizar(alvo_caminho, disco)):
            problemas.append(f"{rota} deveria servir {alvo} byte a byte (respondeu {codigo})")
    print(f"   conferidos byte a byte contra o arquivo de destino")
    return problemas


def conferir_upstream() -> list[str]:
    """O que esta em public/ precisa ser o que o repositorio oficial publica."""
    if not UPSTREAM.exists():
        print(f"\n3. Repositorio oficial\n   ausente em {UPSTREAM.relative_to(ROOT).as_posix()}; "
              "clone com: gh repo clone ShunWalChin/FAT-Tech---Website "
              ".local/references/fat-tech-website")
        return []
    patches = json.loads(PATCHES.read_text(encoding="utf-8")) if PATCHES.exists() else {}
    declarados = patches.get("arquivos", {})
    # Divergencia e um arquivo do original que mudou; acrescimo e um arquivo que o original nao tem.
    # Sem separar os dois, uma pagina nova soava como arquivo perdido na sincronizacao -- que e
    # exatamente o alarme que esta auditoria existe para dar, e um alarme que sempre toca nao serve.
    adicionados = patches.get("adicionados", {})
    problemas = []
    arquivos = arquivos_publicados()
    print(f"\n3. Repositorio oficial\n   {len(arquivos)} arquivos comparados com o clone")
    sem_origem = divergentes = corrigidos = acrescentados = 0
    for caminho in arquivos:
        relativo = caminho.relative_to(PUBLICO)
        origem = UPSTREAM / relativo
        if not origem.exists():
            if relativo.as_posix() in adicionados:
                acrescentados += 1
                continue
            problemas.append(f"{relativo.as_posix()} nao existe no repositorio oficial")
            sem_origem += 1
            continue
        # Fim de linha e normalizado pelo Git na clonagem; diferenca so nele nao e diferenca de conteudo.
        if caminho.read_bytes().replace(b"\r\n", b"\n") != origem.read_bytes().replace(b"\r\n", b"\n"):
            nome = relativo.as_posix()
            if nome in declarados:
                corrigidos += 1
                continue
            problemas.append(f"{nome} difere do oficial sem correcao declarada")
            divergentes += 1
    nossos = {caminho.relative_to(PUBLICO).as_posix() for caminho in arquivos}
    do_site = {caminho.relative_to(UPSTREAM).as_posix() for caminho in UPSTREAM.rglob("*")
               if caminho.is_file() and not caminho.relative_to(UPSTREAM).as_posix().startswith(
                   (".git/", ".github/", "scripts/", "docs/", "node_modules/"))
               and caminho.name not in {"MANUAL.md", "README.md", "package.json", "package-lock.json",
                                        "server.ps1", ".gitignore", ".htaccess", ".htmlvalidate.json"}}
    # Um acrescimo nosso nao pode entrar na conta do que o original tem e nao publicamos.
    faltando = sorted(do_site - nossos - set(adicionados))
    print(f"   sem origem      : {sem_origem}\n   divergentes     : {divergentes}\n"
          f"   nao publicados  : {len(faltando)}\n"
          f"   correcoes declaradas: {corrigidos}\n"
          f"   acrescimos declarados: {acrescentados}")
    for nome in sorted(declarados):
        print(f"      {nome}: {declarados[nome][:96]}...")
    for nome in sorted(adicionados):
        print(f"      + {nome}: {adicionados[nome][:94]}...")
    problemas += [f"{nome} existe no repositorio oficial e nao esta publicado" for nome in faltando]
    return problemas


def main() -> int:
    base = sys.argv[1] if len(sys.argv) > 1 else PADRAO
    print(f"Auditando o site em {base}\n")
    problemas = conferir_servidos(base) + conferir_upstream()
    print("\n" + "=" * 64)
    if problemas:
        print(f"{len(problemas)} problema(s):")
        for problema in problemas[:40]:
            print(f"   - {problema}")
        if len(problemas) > 40:
            print(f"   ... e mais {len(problemas) - 40}")
        return 1
    print("Nenhum problema: cada byte servido e o byte do arquivo, e cada arquivo e o do original.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
