"""E4: o agente acorda sozinho. O consumidor `openclaw` do Core-Engine.

## A decisao que muda o blueprint: o agente puxa, o CRM nao empurra

O projeto em docs/OPENCLAW_BLUEPRINT.md previa `POST {FATTECH_OPENCLAW_URL}/tasks` -- o CRM
empurrando trabalho. Ao ligar o consumidor ficou claro que isso custa caro por nada:

1. **Empurrar exigiria um segundo mecanismo de entrega.** O `core_engine.process()` e explicito:
   *"no broker, LLM or network call in a DB transaction"*. Um POST ao OpenClaw teria de sair da
   transacao, com lease, retentativa, espera progressiva e carta morta proprios -- tudo que o outbox
   ja faz, escrito de novo com outro nome. E `fattech:walchat:two-engines-debt` e exatamente a licao
   de recusar o segundo motor enquanto o primeiro puder ser estendido.
2. **Puxar da o modo degradado de graca.** OpenClaw fora do ar, provedor de LLM fora do ar,
   orcamento estourado: as corridas ficam em `pending` e ele recupera o atraso quando voltar. Isso
   e o DR-02 do manual Palantyr sem uma linha a mais.
3. **Nenhuma credencial de saida, nenhum buraco de entrada.** O agente ja tem chave; o CRM nao
   precisa saber onde o OpenClaw esta. Na topologia por VPS isso deixa de ser uma porta a abrir.

O que este modulo faz, entao, e a metade que **precisa** ser transacional: decidir qual evento
acorda qual agente e materializar a corrida. Quem reclama a corrida e o proprio agente, por
`POST /api/v1/agent/runs/claim`.

## O que o consumidor NAO faz

Nao planeja, nao chama modelo, nao executa ferramenta. Ele cria a corrida em `pending` com o evento
que a originou e para. Todo o resto continua passando pelo portao do E2, com a mesma ordem de
checagens -- um caminho de execucao que existisse so para o despacho automatico seria uma segunda
porta, e o E2 fechou as portas laterais de proposito.
"""
from sqlalchemy import select, update

from .events import utc
from .models import AgentRun, now
from .services import scoped

# Estados de corrida que ainda nao terminaram. Uma corrida presa em `planning` e visivel na tela:
# significa que um agente reclamou e nao voltou, e isso precisa aparecer em vez de sumir.
EM_ABERTO = ("pending", "planning", "executing", "awaiting_approval")


def agentes_despertos(db, tenant_id: str) -> list[tuple[str, dict]]:
    """Agentes ativos que declararam gatilho. Pausado nao acorda, e sem gatilho nao ha o que acordar."""
    saida = []
    for registro in db.scalars(scoped(tenant_id, "agents")):
        dados = registro.data or {}
        if dados.get("status") == "active" and dados.get("triggers"):
            saida.append((registro.id, dados))
    return saida


def tipos_observados(db, tenant_id: str) -> set[str]:
    """Os event_type que algum agente desperto observa. Vazio significa que nada e despachado.

    E isso que serve de trava de rollback deste estagio: sem agente ativo com gatilho, o escalonador
    nao cria entrega nenhuma para o papel `openclaw` e o sistema se comporta como antes -- sem
    variavel de ambiente, sem deploy, sem reverter codigo. `fattech:mano:rollback-por-configuracao`.
    """
    observados = set()
    for _agent_id, dados in agentes_despertos(db, tenant_id):
        observados.update(dados.get("triggers") or [])
    return observados


def despertar(db, source, envelope, settings) -> None:
    """Handler do papel `openclaw`. Materializa uma corrida por agente que observa este evento.

    Dois agentes podem observar o mesmo evento, e cada um ganha a sua corrida -- por isso a
    unicidade e por (tenant, agente, evento) e nao por (tenant, evento). A primeira versao usava a
    segunda forma e o segundo agente colidia em silencio com o primeiro; so apareceu aqui, ao ligar
    o despacho, porque ate o E2 nunca houve mais de um agente reagindo ao mesmo evento.

    O evento que o proprio agente gerou nao o acorda de novo: `agent.` e prefixo reservado, e sem
    isso uma escrita do agente dispararia a corrida seguinte, que escreveria, que dispararia a
    proxima. O limite de saltos do outbox cortaria o laco em cinco voltas; cortar na origem e melhor
    do que cortar no quinto giro.
    """
    if envelope.event.startswith("agent."):
        return
    for agent_id, dados in agentes_despertos(db, source.tenant_id):
        if envelope.event not in (dados.get("triggers") or []):
            continue
        ja_existe = db.scalar(select(AgentRun.id).where(
            AgentRun.tenant_id == source.tenant_id, AgentRun.agent_id == agent_id,
            AgentRun.trigger_event_id == source.id))
        if ja_existe:
            continue
        db.add(AgentRun(
            tenant_id=source.tenant_id, agent_id=agent_id, trigger_event_id=source.id,
            trigger_type=envelope.event, mode=dados.get("mode") or "sugestao", status="pending",
            # A justificativa nasce vazia e e do agente preencher ao reclamar a corrida. Escrever
            # aqui um texto generico do sistema seria por na boca do modelo uma razao que nao e dele.
            rationale="", model=dados.get("model") or ""))


def reclamar(db, principal, agent_id: str, limite: int = 5) -> list[AgentRun]:
    """O agente reclama corridas pendentes. Transicao atomica `pending` -> `planning`.

    A transicao condicionada ao estado anterior e o que impede duas instancias do OpenClaw de
    pegarem a mesma corrida: a segunda encontra `rowcount == 0` e segue para a proxima. Nao ha
    coluna de lease -- uma corrida presa em `planning` fica visivel na tela como agente que nao
    voltou, e um operador enxerga isso. Reciclagem automatica de corrida travada e trabalho de um
    estagio posterior, e fingir que ela existe seria pior que declarar que nao existe.
    """
    candidatas = list(db.scalars(select(AgentRun).where(
        AgentRun.tenant_id == principal.tenant_id, AgentRun.agent_id == agent_id,
        AgentRun.status == "pending").order_by(AgentRun.started_at.asc()).limit(limite)))
    reclamadas = []
    for corrida in candidatas:
        mudou = db.execute(update(AgentRun).where(
            AgentRun.id == corrida.id, AgentRun.tenant_id == principal.tenant_id,
            AgentRun.status == "pending").values(status="planning")
            .execution_options(synchronize_session=False))
        if mudou.rowcount == 1:
            db.refresh(corrida)
            reclamadas.append(corrida)
    return reclamadas


def fila_do_agente(db, tenant_id: str, agent_id: str) -> dict:
    """Quantas corridas esperam, e ha quanto tempo a mais antiga espera.

    A idade da mais antiga e o numero que diz se o agente esta acompanhando ou acumulando atraso.
    A contagem sozinha nao diz: dez corridas de um minuto atras e uma operacao saudavel, e uma
    corrida de seis horas atras e um agente que morreu.
    """
    pendentes = list(db.scalars(select(AgentRun).where(
        AgentRun.tenant_id == tenant_id, AgentRun.agent_id == agent_id,
        AgentRun.status == "pending").order_by(AgentRun.started_at.asc())))
    # utc() porque o SQLite devolve carimbo sem fuso e subtrair um naive de um aware estoura. A
    # mesma pedra ja tinha aparecido no selo da trilha; usar o utilitario que o motor de eventos ja
    # tem e melhor que escrever a terceira normalizacao de fuso deste repositorio.
    mais_antiga = utc(pendentes[0].started_at) if pendentes else None
    return {"pendentes": len(pendentes),
            "mais_antiga_em": mais_antiga.isoformat() if mais_antiga else None,
            "espera_segundos": int((now() - mais_antiga).total_seconds()) if mais_antiga else 0}
