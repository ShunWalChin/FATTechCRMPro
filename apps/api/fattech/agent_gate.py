"""O portao de execucao do agente. Toda acao autonoma passa por aqui, nesta ordem.

`fattech:walchat:compliance-order` registra que a ordem de decisao de um envio **e contrato, nao
preferencia: inverter dois passos muda quem recebe mensagem**. O mesmo vale para um agente, e por
isso a sequencia abaixo esta escrita uma vez, num lugar so, e nao espalhada por rota:

    1. escopo da chave cobre a ferramenta        -> recusa: escopo insuficiente
    2. a ferramenta esta na lista do agente      -> recusa: ferramenta nao habilitada
    3. o modo permite a classe da acao           -> sugestao vira rascunho; externa em modo interno recusa
    4. teto de acoes na hora                     -> recusa: teto de acoes por hora
    5. teto de gasto do mes                      -> recusa: orcamento do mes
    6. envio externo: trava global e compliance  -> recusa: envio externo desligado
    7. irreversivel ou marcado                   -> aprovacao necessaria, e o agente nao decide
    8. executa e registra o passo                -> sempre registra, inclusive a recusa

O passo 8 nao e opcional em nenhum caminho. `fattech:lead:explicacao-e-o-produto` -- *"a explicacao
e o produto, nao o numero"* -- traduzido para o agente: **a justificativa e o produto, nao a acao**.
Uma tentativa recusada que nao deixa registro faz o portao parecer que nunca foi testado.

O que este modulo **nao** faz, de proposito: nao reavalia compliance com os dados do momento. Isso
e o E5, e ate la envio externo e recusado pela trava global antes de chegar la. Um portao que
fingisse avaliar compliance sem os dados do instante seria pior que um que recusa.
"""
from datetime import timedelta

from fastapi import HTTPException
from sqlalchemy import func, select

from . import agent_tools
from .models import AgentRun, AgentStep, now
from .services import audit_event, create_record, get_record, list_records, scoped, serialize, update_record

# O que cada modo autoriza. `sugestao` nao escreve: ela propoe, e uma pessoa aplica.
MODO_PERMITE = {
    "sugestao": {"ler": True, "escrever": False, "externo": False},
    "execucao_interna": {"ler": True, "escrever": True, "externo": False},
    "execucao_externa": {"ler": True, "escrever": True, "externo": True},
}
# Ferramentas que o despachante sabe executar hoje. O catalogo publica isso como `executavel`:
# anunciar ferramenta que ninguem implementou seria o catalogo mentindo.
def executaveis() -> set[str]:
    from .schemas import RESOURCES
    nomes = set()
    for kind in RESOURCES:
        if kind in agent_tools.FORA_DO_ALCANCE:
            continue
        nomes |= {f"{kind}.read", f"{kind}.write"}
    return nomes


class Recusa(Exception):
    """Recusa de negocio, nao erro. Vira passo gravado com motivo, e a corrida continua."""
    def __init__(self, motivo: str, decisao: str = "refused"):
        self.motivo, self.decisao = motivo, decisao
        super().__init__(motivo)


def gasto_do_mes(db, tenant_id: str, agent_id: str, quando=None) -> int:
    alvo = (quando or now()).strftime("%Y-%m")
    return sum(corrida.cost_cents for corrida in
               db.scalars(select(AgentRun).where(AgentRun.tenant_id == tenant_id,
                                                 AgentRun.agent_id == agent_id))
               if corrida.started_at.isoformat()[:7] == alvo)


def acoes_na_ultima_hora(db, tenant_id: str, agent_id: str) -> int:
    """Conta passos **permitidos** na ultima hora, nao tentativas.

    Contar recusas no teto puniria o agente por ser barrado: ele bateria no teto justamente quando o
    portao estivesse funcionando, e a recusa viraria um segundo castigo.
    """
    corte = now() - timedelta(hours=1)
    return db.scalar(
        select(func.count()).select_from(AgentStep)
        .join(AgentRun, AgentRun.id == AgentStep.run_id)
        .where(AgentStep.tenant_id == tenant_id, AgentRun.agent_id == agent_id,
               AgentStep.decision.in_(("allowed", "suggested")), AgentStep.created_at >= corte)) or 0


def avaliar(db, principal, configuracao: dict, corrida: AgentRun, ferramenta: str, settings) -> str:
    """Devolve a decisao: allowed, suggested, approval_required. Levanta Recusa para o resto."""
    catalogo = agent_tools.por_nome()
    descricao = catalogo.get(ferramenta)
    if descricao is None:
        raise Recusa(f"ferramenta desconhecida: {ferramenta}")

    # 1. Escopo da chave. A chave foi emitida com os escopos das ferramentas declaradas; uma
    # ferramenta acrescentada a configuracao depois disso nao passa sem reemitir a chave.
    if principal.key and descricao["escopo"] not in principal.key.scopes:
        raise Recusa(f"escopo insuficiente: a chave não carrega {descricao['escopo']}")

    # 2. Lista de permissao do agente. Vazia significa nenhuma, nunca todas.
    if ferramenta not in (configuracao.get("tools") or []):
        raise Recusa(f"ferramenta não habilitada para este agente: {ferramenta}")

    modo = configuracao.get("mode") or "sugestao"
    permite = MODO_PERMITE.get(modo)
    if permite is None:
        raise Recusa(f"modo de operação desconhecido: {modo}")
    escreve = not ferramenta.endswith(".read")

    # 3. Classe da acao contra o modo.
    if descricao["classe"] == "externa" and not permite["externo"]:
        raise Recusa(f"modo {modo} não autoriza ação externa")
    if escreve and not permite["escrever"] and modo != "sugestao":
        raise Recusa(f"modo {modo} não autoriza escrita")

    # 4 e 5. Tetos. Zero e "ninguem declarou" e recusa; nunca vale como ilimitado.
    if modo != "sugestao":
        teto_hora = configuracao.get("max_actions_per_hour") or 0
        teto_mes = configuracao.get("budget_month_cents") or 0
        if not teto_hora or not teto_mes:
            raise Recusa("teto de ações e orçamento do mês precisam estar declarados")
        feitas = acoes_na_ultima_hora(db, principal.tenant_id, corrida.agent_id)
        if feitas >= teto_hora:
            raise Recusa(f"teto de ações por hora atingido: {feitas} de {teto_hora}")
        gasto = gasto_do_mes(db, principal.tenant_id, corrida.agent_id)
        if gasto >= teto_mes:
            raise Recusa(f"orçamento do mês esgotado: {gasto} de {teto_mes} centavos")

    # 6. Envio externo continua atras da trava global. A reavaliacao de compliance com os dados do
    # momento e o E5; ate la a trava recusa antes, e recusar e melhor que fingir que avaliou.
    if descricao["classe"] == "externa" and not settings.external_sends_enabled:
        raise Recusa("envio externo desligado nesta instalação")

    # 7. Irreversivel ou marcado pela configuracao: vira solicitacao, e o agente nunca e o decisor.
    if not descricao["reversivel"] or ferramenta in (configuracao.get("require_approval_for") or []):
        return "approval_required"

    # 3b. Em sugestao, a escrita vira proposta. O agente propoe; uma pessoa aplica.
    if escreve and modo == "sugestao":
        return "suggested"
    return "allowed"


def executar(db, principal, ferramenta: str, argumentos: dict) -> tuple[str, dict]:
    """Executa a ferramenta ja autorizada. Devolve (referencia, corpo).

    So chega aqui o que o portao decidiu `allowed`. Uma ferramenta do catalogo que o despachante nao
    conhece e recusada com motivo explicito, em vez de silenciosamente nao fazer nada -- ferramenta
    anunciada que nao executa e catalogo mentindo.
    """
    if ferramenta not in executaveis():
        raise Recusa(f"ferramenta ainda não executável nesta versão: {ferramenta}")
    kind, operacao = ferramenta.rsplit(".", 1)
    if operacao == "read":
        record_id = argumentos.get("id")
        if record_id:
            return record_id, serialize(get_record(db, principal.tenant_id, kind, record_id))
        filtros = {chave: argumentos.get(chave) for chave in
                   ("q", "status", "stage", "contact_id", "owner_id", "pipeline_id")}
        filtros["limit"] = min(int(argumentos.get("limit") or 50), 200)
        filtros["offset"] = int(argumentos.get("offset") or 0)
        return "", list_records(db, principal.tenant_id, kind, filtros)
    record_id = argumentos.get("id")
    corpo = {chave: valor for chave, valor in argumentos.items() if chave != "id"}
    if record_id:
        registro = update_record(db, principal, kind, record_id, corpo)
        return record_id, serialize(registro) if hasattr(registro, "data") else {"id": record_id}
    registro = create_record(db, principal.tenant_id, principal.actor_id, kind, corpo, role=principal.role)
    return registro.id, serialize(registro)


def agir(db, principal, corrida: AgentRun, configuracao: dict, ferramenta: str,
         argumentos: dict, settings) -> dict:
    """Uma tentativa do agente: avalia, executa se puder, e **sempre** grava o passo.

    O `try` cobre tanto a recusa de negocio quanto a recusa que as regras normais do CRM levantam
    -- 409 de versao, 422 de validacao, 404 de registro inexistente. Todas viram passo gravado: o
    agente que tentou escrever por cima de uma pessoa deixa rastro, e esse rastro e o que mostra que
    a concorrencia otimista segurou.
    """
    proxima = (db.scalar(select(func.max(AgentStep.seq)).where(
        AgentStep.tenant_id == principal.tenant_id, AgentStep.run_id == corrida.id)) or 0) + 1
    decisao, motivo, referencia, corpo = "refused", "", "", None
    try:
        decisao = avaliar(db, principal, configuracao, corrida, ferramenta, settings)
        if decisao == "allowed":
            referencia, corpo = executar(db, principal, ferramenta, argumentos)
    except Recusa as recusa:
        decisao, motivo = recusa.decisao, recusa.motivo
    except HTTPException as erro:
        decisao = "refused"
        detalhe = erro.detail
        motivo = (detalhe if isinstance(detalhe, str) else str(detalhe))[:200]
    passo = AgentStep(tenant_id=principal.tenant_id, run_id=corrida.id, seq=proxima,
                      tool=ferramenta, arguments=argumentos, decision=decisao,
                      refusal_reason=motivo[:200], result_ref=referencia or "")
    db.add(passo)
    db.flush()
    # A trilha selada recebe o run_id: e o elo entre "o que aconteceu" e "por que o agente tentou".
    audit_event(db, principal.tenant_id, principal.actor_id, f"agent.{decisao}", passo.id,
                {"run_id": corrida.id, "step_seq": proxima, "tool": ferramenta,
                 "reason": motivo[:200], "result_ref": referencia or ""})
    return {"run_id": corrida.id, "seq": proxima, "tool": ferramenta, "decision": decisao,
            "refusal_reason": motivo, "result_ref": referencia or "", "result": corpo,
            "step_id": passo.id,
            "nota": {"suggested": "Rascunho registrado. Uma pessoa precisa aplicar para que exista.",
                     "approval_required": "Ação irreversível: virou solicitação, e o agente não decide.",
                     "refused": "Recusado pelo portão; o motivo fica gravado no passo."}.get(decisao, "")}


def aplicar_sugestao(db, principal, passo: AgentStep, corrida: AgentRun) -> dict:
    """Uma pessoa aplica o rascunho que o agente propos. E aqui que a sugestao vira efeito.

    Quem aplica e o autor do que acontece: a escrita entra com o `Principal` da pessoa, e a trilha
    registra o nome dela. O agente sugeriu; a pessoa decidiu. Confundir os dois seria dar ao agente
    escrita sem modo de execucao, por um caminho lateral.
    """
    if passo.decision != "suggested":
        raise HTTPException(409, "Só um passo em rascunho pode ser aplicado")
    if passo.result_ref:
        raise HTTPException(409, "Este rascunho já foi aplicado")
    referencia, corpo = executar(db, principal, passo.tool, passo.arguments or {})
    passo.result_ref = referencia or "aplicado"
    audit_event(db, principal.tenant_id, principal.actor_id, "agent.suggestion_applied", passo.id,
                {"run_id": corrida.id, "step_seq": passo.seq, "tool": passo.tool,
                 "result_ref": referencia or ""})
    return {"step_id": passo.id, "tool": passo.tool, "result_ref": referencia or "", "result": corpo,
            "aplicado_por": principal.actor_id}
