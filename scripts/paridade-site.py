"""Mede o que o site vende contra o que o sistema entrega.

A ordem de engenharia mede o CRM contra CRMs de mercado. Esta matriz mede outra coisa, e a
diferenca importa: **o que a FAT Tech ja cobra por**. Uma capacidade ausente na ordem e trabalho
futuro; uma capacidade ausente aqui e uma promessa comercial em aberto, com preco publicado e
possivelmente ja vendida.

As promessas sao lidas do proprio site (apps/web/public), nao de memoria: se o texto da pagina
mudar, a matriz muda junto. O estado do sistema e lido do schema, das rotas e do codigo.

Uso: python scripts/paridade-site.py
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps/api"))

from fattech.config import Settings      # noqa: E402
from fattech.db import Base              # noqa: E402
from fattech.main import create_app      # noqa: E402
from fattech.schemas import RESOURCES    # noqa: E402
from fattech import models               # noqa: F401,E402

SITE = ROOT / "apps/web/public"
API = ROOT / "apps/api/fattech"
FONTE = {p.name: p.read_text(encoding="utf-8", errors="replace") for p in API.glob("*.py")}
TUDO = "\n".join(FONTE.values())
CAMPOS = {kind: set(m.model_fields) for kind, m in RESOURCES.items()}
TABELAS = set(Base.metadata.tables)
ROTAS = sorted({r.path for r in create_app(
    Settings(_env_file=None, env="test", database_url="sqlite:///:memory:")).routes if hasattr(r, "path")})


def campo(kind, *nomes):
    return all(n in CAMPOS.get(kind, ()) for n in nomes)


def codigo(arquivo, *termos):
    return all(t in FONTE.get(arquivo, "") for t in termos)


def rota(fragmento):
    return any(fragmento in c for c in ROTAS)


def promessa_no_site(texto: str) -> list[str]:
    """Onde esta promessa aparece. Vazio significa que ela saiu do site e a linha pode sair daqui."""
    onde = []
    for pagina in sorted(SITE.rglob("*.html")):
        conteudo = pagina.read_text(encoding="utf-8", errors="replace")
        if re.search(texto, conteudo, re.I):
            onde.append(pagina.relative_to(SITE).as_posix())
    return onde


# (promessa como o site a nomeia, regex que a encontra na pagina, sonda no sistema, veredito)
PROMESSAS = [
    ("Agentes Neurais de IA com RAG", r"Agentes? Neurais?",
     False,
     "AUSENTE — kind agents guarda persona, autonomia e orcamento; nao ha executor nem RAG"),
    ("WhatsApp API Oficial da Meta", r"WhatsApp API Oficial",
     False,
     "AUSENTE — compliance conhece janela de 24h e template; nao ha entrega a Meta"),
    ("CRM Kanban autonomo", r"Kanban Aut[oô]nomo",
     rota("/crm/radar"),
     "PARCIAL — quadro configuravel com arraste e radar de risco; nada se move sozinho"),
    ("Agenda automatica via IA", r"Agenda Aut[oô]noma|Agenda Autom[aá]tica",
     False,
     "AUSENTE — nao ha agenda, nem integracao de calendario, nem agendamento"),
    ("Dashboard de diretoria em tempo real", r"Dashboard de Diretoria",
     rota("/dashboard"),
     "PARCIAL — painel com funil, previsao ponderada e conversao; sem tempo real nem configuracao"),
    ("Laboratorio sandbox", r"Laborat[oó]rio Sandbox",
     codigo("services.py", "def simulate"),
     "PARCIAL — simulador de automacao que executa sem enviar; nao e ambiente isolado completo"),
    ("Contador de janela de atendimento", r"Janela de Atendimento",
     codigo("compliance.py", "STANDARD_WINDOW"),
     "PARCIAL — a janela de 24h e decidida no servidor; a tela nao mostra contador"),
    ("Webhooks e integracoes", r"WebHooks?\s*&amp;?\s*Integra",
     rota("/webhooks/n8n"),
     "entrada HMAC + outbox transacional + chaves de API com escopo"),
    ("Catalogo neural de produtos", r"Cat[aá]logo Neural",
     campo("products", "price_cents", "cost_cents"),
     "PARCIAL — catalogo com preco, custo, unidade e recorrencia; sem camada neural"),
    ("Disparo em massa via API oficial", r"Disparo (em )?Mass",
     False,
     "AUSENTE — campanhas sao cadastro; nao ha destinatarios nem envio"),
    ("Gestao completa de operadores", r"Gest[aã]o Completa de Operadores",
     rota("/team"),
     "cinco papeis, permissoes, sessoes revogaveis e trilha de auditoria"),
    ("Vendas e cobrancas diretas no chat", r"Vendas e Cobran",
     False,
     "AUSENTE — nao ha cobranca, pagamento nem envio pelo chat"),
    ("Sistema FAT Tech CRM completo", r"Sistema FAT Tech CRM",
     len(RESOURCES) >= 15,
     f"PARCIAL — {len(RESOURCES)} dominios, contratos, propostas, leads e funil; 57% da ordem"),
    ("Integracao com Instagram", r"Instagram",
     "instagram_accounts" in TABELAS,
     "PARCIAL — conta por organizacao e webhook que resolve o dono; mensagem nao vira conversa"),
    ("Conteudo integrado ao CRM (vertente Posiciona)", r"Conte[uú]do Integrado a CRM",
     rota("/content/indicadores"),
     "calendario, banco de pautas e apuracao do publicado contra a frequencia contratada"),
    ("Calendario editorial entregue ao cliente", r"calend[aá]rio editorial",
     rota("/content_posts"),
     "peca com pilar, formato, responsavel e ciclo ate publicado, versionada e auditada"),
    ("Fecha vendas enquanto voce dorme", r"enquanto voc[eê] dorme",
     False,
     "AUSENTE — nenhuma acao comercial acontece sem uma pessoa; a trava de envio externo esta desligada"),
]


def situacao(linha):
    _, _, sonda, veredito = linha
    if veredito.startswith("AUSENTE"):
        return "AUSENTE"
    if veredito.startswith("PARCIAL"):
        return "PARCIAL"
    return "TEM" if sonda else "AUSENTE"


def main() -> int:
    print("O QUE O SITE VENDE  ×  O QUE O SISTEMA ENTREGA\n")
    print(f"{'PROMESSA DO SITE':38} {'SITUACAO':9} {'PAGS':>5}  ESTADO REAL")
    print("-" * 132)
    fantasmas = []
    for promessa, padrao, sonda, veredito in PROMESSAS:
        paginas = promessa_no_site(padrao)
        marca = situacao((promessa, padrao, sonda, veredito))
        if not paginas:
            fantasmas.append(promessa)
        print(f"{promessa:38} {marca:9} {len(paginas):>5}  {veredito[:66]}")
    print("-" * 132)

    tem = sum(1 for p in PROMESSAS if situacao(p) == "TEM")
    parcial = sum(1 for p in PROMESSAS if situacao(p) == "PARCIAL")
    ausente = sum(1 for p in PROMESSAS if situacao(p) == "AUSENTE")
    total = len(PROMESSAS)
    print(f"\nTEM: {tem}   PARCIAL: {parcial}   AUSENTE: {ausente}   de {total} promessas")
    print(f"Cobertura ponderada: {(tem + parcial * 0.5) / total * 100:.0f}%")
    if fantasmas:
        # Promessa que nao aparece mais no site nao precisa de sistema: a linha e que esta velha.
        print(f"\nNao encontradas no site (revisar esta matriz): {', '.join(fantasmas)}")
    print("\nAUSENTE aqui nao e trabalho futuro como na ordem de engenharia: e promessa publicada,")
    print("com preco na pagina de planos, que o sistema ainda nao cumpre.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
