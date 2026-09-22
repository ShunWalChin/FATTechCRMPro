"""O catalogo de ferramentas do agente, derivado do sistema em vez de escrito a mao.

`fattech:contrato:lista-fixa-em-dois-lugares`: um conjunto escrito em dois lugares diverge no
primeiro ajuste. Este projeto ja pagou por isso -- `fattech:chaves:limite-menor-que-o-catalogo`
registra o dia em que o limite de escopos de uma chave ficou abaixo do catalogo que a API oferecia,
e nenhuma chave podia pedir todos os escopos que existiam.

Entao o catalogo nao e uma lista. Ele e **gerado** de `RESOURCES` mais as operacoes nomeadas, e
cada ferramenta declara o escopo que a autoriza. Dominio novo no CRM aparece como ferramenta no
mesmo deploy, sem ninguem lembrar de atualizar nada, e o teste que conta ferramentas contra escopos
falha no dia em que os dois divergirem.

Tres coisas que o catalogo declara e que decidem o portao (E2):

  `classe`      interna  -- nao sai da maquina. E a autonomia real, e nao exige trava desligada.
                externa  -- entrega a terceiro. Passa por external_sends_enabled e por compliance.
  `reversivel`  falso    -- exige aprovacao, sempre, e o agente nunca e o decisor.
  `escopo`      o escopo da chave que autoriza. Sem ele na chave, 403 com o escopo que faltou.

O que **nao** esta aqui e tao importante quanto o que esta: escrita em equipe, chaves de API, leitura
da trilha. Nao e omissao -- `Principal.admin()` recusa qualquer chave, sempre, entao essas operacoes
sao estruturalmente inalcancaveis para um agente. O catalogo apenas nao mente sobre isso.
"""
from .schemas import RESOURCES

# Kind que o agente nunca opera, com o motivo. Declarado aqui, visivel, em vez de filtrado em silencio.
FORA_DO_ALCANCE = {
    "custom_fields": "muda o esquema da organizacao; decisao de configuracao, nao de operacao",
    "lead_rules": "muda como todo lead e pontuado; um agente ajustando a propria regua nao e auditavel",
    "approvals": "o agente e solicitante da cadeia, nunca decisor",
}
# Operacoes nomeadas que nao sao CRUD de kind. O escopo de cada uma e o que a API ja exige.
NOMEADAS = [
    ("crm.leads.fila", "Ler a fila de leads com SLA e temperatura", "contacts:read", "interna", True),
    ("crm.leads.score", "Ler a pontuacao explicada de um lead", "contacts:read", "interna", True),
    ("crm.radar", "Ler oportunidades paradas e seu tempo de parada", "deals:read", "interna", True),
    ("crm.dashboard", "Ler funil, previsao ponderada e conversao", "dashboard:read", "interna", True),
    ("sales.report", "Ler o relatorio comercial do periodo", "deals:read", "interna", True),
    ("sales.proposals.read", "Ler propostas", "invoices:read", "interna", True),
    ("sales.proposals.write", "Criar ou ajustar proposta em rascunho", "invoices:write", "interna", True),
    ("sales.proposals.issue", "Emitir proposta ao cliente", "invoices:write", "externa", False),
    ("contracts.read", "Ler contratos e suas revisoes", "contracts:read", "interna", True),
    ("contracts.write", "Criar ou editar contrato", "contracts:write", "interna", True),
    ("contracts.transition", "Mudar o estado de um contrato", "contracts:write", "interna", False),
    ("contracts.signature", "Solicitar assinatura externa", "contracts:write", "externa", False),
    ("content.indicadores", "Ler a apuracao mensal de conteudo", "content_posts:read", "interna", True),
    ("contacts.merge", "Fundir dois contatos", "contacts:write", "interna", False),
    ("work_queue.read", "Ler a fila de trabalho", "tasks:read", "interna", True),
    ("messages.send", "Enviar mensagem por um canal externo", "messages:write", "externa", False),
]
# Kind cuja escrita cria efeito fora da maquina ou destroi historico.
ESCRITA_EXTERNA = {"messages"}
ESCRITA_IRREVERSIVEL = {"messages"}


def ferramentas() -> list[dict]:
    """Uma entrada por operacao, com o escopo que a autoriza. Ordenada para o diff ser legivel."""
    catalogo = []
    for kind in sorted(RESOURCES):
        if kind in FORA_DO_ALCANCE:
            continue
        catalogo.append({"nome": f"{kind}.read", "descricao": f"Listar e ler {kind}",
                         "escopo": f"{kind}:read", "classe": "interna", "reversivel": True})
        catalogo.append({"nome": f"{kind}.write", "descricao": f"Criar e editar {kind}",
                         "escopo": f"{kind}:write",
                         "classe": "externa" if kind in ESCRITA_EXTERNA else "interna",
                         "reversivel": kind not in ESCRITA_IRREVERSIVEL})
        # Excluir e irreversivel em todo kind: `fattech:merge:destrutivo-declarado`.
        catalogo.append({"nome": f"{kind}.delete", "descricao": f"Excluir {kind}",
                         "escopo": f"{kind}:write", "classe": "interna", "reversivel": False})
    for nome, descricao, escopo, classe, reversivel in NOMEADAS:
        catalogo.append({"nome": nome, "descricao": descricao, "escopo": escopo,
                         "classe": classe, "reversivel": reversivel})
    return sorted(catalogo, key=lambda ferramenta: ferramenta["nome"])


def por_nome() -> dict[str, dict]:
    return {ferramenta["nome"]: ferramenta for ferramenta in ferramentas()}


def escopos_de(nomes) -> set[str]:
    """Escopos minimos para as ferramentas pedidas. E o que a chave do agente precisa carregar."""
    mapa = por_nome()
    return {mapa[nome]["escopo"] for nome in nomes if nome in mapa}


def desconhecidas(nomes) -> list[str]:
    mapa = por_nome()
    return sorted({nome for nome in nomes if nome not in mapa})


def catalogo_publicado() -> dict:
    """O que a rota devolve. Reporta o denominador: contagem por classe e o que ficou de fora."""
    from .agent_gate import executaveis
    prontas = executaveis()
    lista = [{**f, "executavel": f["nome"] in prontas} for f in ferramentas()]
    return {
        "items": lista,
        "total": len(lista),
        "por_classe": {"interna": sum(1 for f in lista if f["classe"] == "interna"),
                       "externa": sum(1 for f in lista if f["classe"] == "externa")},
        "irreversiveis": sum(1 for f in lista if not f["reversivel"]),
        "escopos_distintos": len({f["escopo"] for f in lista}),
        # Anunciar ferramenta que nenhum despachante executa seria o catalogo mentindo.
        "executaveis": sum(1 for f in lista if f["executavel"]),
        # Fora do alcance aparece com o motivo: catalogo que omite em silencio parece completo.
        "fora_do_alcance": FORA_DO_ALCANCE,
        "nota": ("Escrita em equipe, chaves de API e leitura da trilha nao aparecem porque "
                 "Principal.admin() recusa qualquer chave de API; sao inalcancaveis para um agente, "
                 "nao omitidas deste catalogo."),
    }
