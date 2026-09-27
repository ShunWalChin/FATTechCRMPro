r"""O catalogo de tipos de evento que o CRM emite. Derivado, nunca escrito a mao.

O Palantyr v5 registra como divida (DT-14) "conferir gatilhos contra `GET /api/v1/core/contract`".
Essa rota devolve o **esquema do envelope**: ela valida o formato do nome do evento
(`^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*){1,7}$`) e nao sabe dizer se o evento existe. Um agente ativo
com gatilho inexistente passa em toda validacao e **nunca acorda** -- o estado diz uma coisa e a
operacao faz outra, e quem configurou fica esperando por uma corrida que nao vem.

Este catalogo responde a outra pergunta: quais nomes o sistema realmente emite. Ele e montado de
duas fontes, e as duas sao codigo:

  1. `{kind}.created|updated|deleted` para todo dominio de RESOURCES -- `create_record` e
     `update_record` emitem esses tres por construcao;
  2. os eventos nomeados, varridos das chamadas de `audit_event` no proprio pacote.

A varredura e por expressao regular sobre o codigo-fonte, e isso tem limite declarado: um evento
cujo nome for montado em tempo de execucao a partir de variavel nao aparece aqui. E por isso que a
resposta traz `observados_no_banco` junto -- o que a trilha de producao registrou de fato. As duas
listas juntas sao mais honestas que qualquer uma sozinha: a primeira diz o que o codigo pode emitir,
a segunda diz o que ja emitiu.
"""
import pathlib
import re

from sqlalchemy import func, select

from .models import Audit
from .schemas import RESOURCES

PACOTE = pathlib.Path(__file__).parent
# audit_event(db, tenant, actor, "nome.do.evento", ...) -- o nome literal no quarto argumento.
LITERAL = re.compile(r'audit_event\(\s*[^,]+,\s*[^,]+,\s*[^,]+,\s*"([a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+)"')
CICLO = ("created", "updated", "deleted")
# Eventos cujo nome e montado em tempo de execucao e que a varredura de literais nao alcanca. Eles
# sao reais e precisam estar no catalogo: um gatilho valido recusado na escrita e tao ruim quanto um
# invalido aceito. A lista e curta de proposito -- cada linha aqui e uma f-string no codigo, e o
# caminho certo e reduzi-la, nao crescer.
#
# `agent.*` sai de agent_gate.agir() como f"agent.{decisao}". O prefixo e reservado: um evento do
# proprio agente nunca o acorda de novo, entao declara-lo aqui nao abre laco.
DINAMICOS = ("agent.allowed", "agent.refused", "agent.suggested", "agent.approval_required")


def eventos_de_dominio() -> dict[str, list[str]]:
    """Os tres do ciclo de vida, para cada dominio. Emitidos por construcao em create/update/delete."""
    return {kind: [f"{kind}.{acao}" for acao in CICLO] for kind in sorted(RESOURCES)}


def eventos_nomeados() -> dict[str, list[str]]:
    """Eventos com nome proprio, por modulo que os emite."""
    saida = {}
    for arquivo in sorted(PACOTE.glob("*.py")):
        if arquivo.name == pathlib.Path(__file__).name:
            # A varredura nao le o proprio arquivo: o exemplo citado no cabecalho entrava como
            # evento real, catalogado por auto-referencia. Um medidor nao se mede.
            continue
        achados = sorted(set(LITERAL.findall(arquivo.read_text(encoding="utf-8", errors="replace"))))
        if achados:
            saida[arquivo.name] = achados
    return saida


def catalogo(db=None, tenant_id: str | None = None) -> dict:
    """O catalogo publicado. Com `db`, acrescenta o que a trilha desta organizacao ja registrou."""
    dominio = eventos_de_dominio()
    nomeados = eventos_nomeados()
    do_codigo = {evento for lista in dominio.values() for evento in lista}
    do_codigo |= {evento for lista in nomeados.values() for evento in lista}
    do_codigo |= set(DINAMICOS)
    observados = {}
    if db is not None and tenant_id:
        observados = {acao: quantos for acao, quantos in db.execute(
            select(Audit.action, func.count()).where(Audit.tenant_id == tenant_id)
            .group_by(Audit.action).order_by(func.count().desc())).all()}
    return {
        "total": len(do_codigo),
        "events": sorted(do_codigo),
        "por_dominio": dominio,
        "nomeados_por_modulo": nomeados,
        "nome_montado_em_execucao": sorted(DINAMICOS),
        "observados_no_banco": observados,
        # Um evento observado que nao esta no catalogo e sinal de nome montado em tempo de execucao,
        # nao de erro: a varredura le literais, e declarar o limite vale mais que esconde-lo.
        "observados_fora_do_catalogo": sorted(set(observados) - do_codigo),
        "nota": ("Gatilho de agente precisa estar em `events`. O prefixo `agent.` e reservado: um "
                 "evento do proprio agente nunca o acorda de novo, para nao virar laco."),
    }


def desconhecidos(gatilhos) -> list[str]:
    """Quais dos gatilhos pedidos o CRM nao emite. Vazio significa que todos existem."""
    catalogo_atual = set(catalogo()["events"])
    return sorted({gatilho for gatilho in gatilhos if gatilho not in catalogo_atual})
