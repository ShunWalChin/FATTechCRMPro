"""A trilha de auditoria deixa de ser apenas inalteravel pela aplicacao e passa a ser verificavel.

O que ja existia: `REVOKE UPDATE, DELETE ON audit_log FROM fattech_app`. Isso impede que a
aplicacao altere a trilha, e e a metade facil. A metade que faltava e a outra: um restore parcial,
um superusuario do banco, um dump editado e um `DELETE` rodado por fora da aplicacao continuam
possiveis, e nenhum deles deixa marca. Uma trilha que so o proprio suspeito pode apagar nao serve
de prova -- e exatamente disso que o manual do Palantyr v4 trata no passo F1-03.

A cadeia resolve tornando a alteracao **detectavel**, nao impossivel. Cada linha carrega o hash da
anterior da mesma organizacao. Mudar o conteudo de uma linha antiga quebra o elo de todas as
seguintes; remover uma abre um buraco na numeracao. Nao ha chave secreta aqui, e isso e deliberado:
quem quiser reescrever a cadeia inteira consegue, mas precisa reescrever **tudo**, e quem confere
gasta um SELECT para descobrir. O valor esta em a verificacao ser barata e o conserto, caro.

Duas diferencas em relacao ao gatilho do manual, ambas por causa de concorrencia:

1. O manual le `ORDER BY id DESC LIMIT 1` sem travar nada. Duas transacoes simultaneas leem o mesmo
   elo anterior e gravam duas linhas irmas -- a cadeia bifurca em silencio e a verificacao passa
   a acusar problema num banco intacto. Aqui a numeracao por organizacao e serializada com
   `pg_advisory_xact_lock`, e um indice unico em (tenant_id, seq) transforma a bifurcacao restante
   em erro de gravacao, nunca em fork silencioso.
2. O elo e por organizacao, nao global. Uma cadeia unica acoplaria tenants: a verificacao de um
   cliente dependeria das linhas de outro, que ele nao pode ler sob RLS.
"""
import hashlib
import json
from datetime import timezone

from sqlalchemy import event, func, select, text
from sqlalchemy.orm import Session

from .models import Audit, now, uid

GENESIS = "GENESIS"


def instante(valor) -> str:
    """O carimbo entra no selo sempre como UTC sem fuso, com microssegundos.

    O banco nao devolve o objeto que recebeu: o SQLite perde o fuso e o Postgres o devolve
    normalizado. Selar o `isoformat()` cru fazia **toda** linha falhar a reconferencia um instante
    depois de gravada -- a cadeia acusava adulteracao num banco intacto. E a pior forma de um
    controle falhar: ele grita sempre, e quem confere aprende a ignora-lo.
    """
    if valor.tzinfo is not None:
        valor = valor.astimezone(timezone.utc).replace(tzinfo=None)
    return valor.isoformat(timespec="microseconds")


def impressao(seq: int, linha: Audit) -> str:
    """O que entra no hash. Lista canonica em JSON, nunca concatenacao com separador.

    Um separador literal e ambiguo: `action="a|b"` com `resource_id="c"` produz a mesma cadeia que
    `action="a"` com `resource_id="b|c"`, e duas linhas diferentes com o mesmo hash sao uma porta.
    """
    corpo = [seq, linha.tenant_id, linha.id, linha.actor_id or "", linha.action, linha.resource_id,
             instante(linha.created_at), linha.details or {}, linha.hash_prev]
    bruto = json.dumps(corpo, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)
    return hashlib.sha256(bruto.encode("utf-8")).hexdigest()


def cauda(db, tenant_id: str) -> tuple[int, str]:
    """Ultimo elo da organizacao. Sem linhas, a cadeia comeca em GENESIS."""
    linha = db.execute(select(Audit.seq, Audit.hash_self).where(Audit.tenant_id == tenant_id)
                       .order_by(Audit.seq.desc()).limit(1)).first()
    return (linha[0], linha[1]) if linha and linha[1] else (0, GENESIS)


def encadear(db, novas: list[Audit]) -> None:
    """Numera e sela as linhas novas, uma organizacao de cada vez.

    A ordem dentro do flush precisa ser deterministica e nao e: `session.new` e um conjunto. Ordenar
    pelo id ja atribuido resolve, e por isso o id e atribuido aqui em vez de deixado para o INSERT.
    """
    if not novas:
        return
    postgres = db.bind.dialect.name == "postgresql"
    for linha in novas:
        linha.id = linha.id or uid()
        linha.created_at = linha.created_at or now()
    por_tenant: dict[str, list[Audit]] = {}
    for linha in sorted(novas, key=lambda linha: linha.id):
        por_tenant.setdefault(linha.tenant_id, []).append(linha)
    for tenant_id, linhas in por_tenant.items():
        if postgres:
            # Serializa a numeracao desta organizacao ate o fim da transacao. Sem isto, duas
            # requisicoes simultaneas do mesmo cliente leem a mesma cauda e bifurcam a cadeia.
            db.execute(text("SELECT pg_advisory_xact_lock(hashtext(:chave))"),
                       {"chave": f"audit:{tenant_id}"})
        seq, anterior = cauda(db, tenant_id)
        for linha in linhas:
            seq += 1
            linha.seq, linha.hash_prev = seq, anterior
            linha.hash_self = anterior = impressao(seq, linha)


@event.listens_for(Session, "before_flush")
def selar_trilha(session, _contexto, _instancias):
    """Toda linha de auditoria passa por aqui, venha de audit_event ou de um db.add direto.

    Prender isto a `audit_event` deixaria de fora os quatro lugares que constroem `Audit(...)` na
    mao -- e uma trilha com quatro linhas fora da cadeia nao e uma trilha verificavel.
    """
    encadear(session, [objeto for objeto in session.new if isinstance(objeto, Audit)])


def verificar(db, tenant_id: str, limite: int | None = None) -> dict:
    """Percorre a cadeia e devolve o denominador junto com o veredito.

    Saber que ha zero problemas nao vale nada sem saber quantas linhas foram conferidas: um
    verificador que le nada tambem termina sem achar problema.
    """
    consulta = select(Audit).where(Audit.tenant_id == tenant_id).order_by(Audit.seq.asc())
    if limite:
        # Conferir a cauda recente e barato e serve de sonda continua; a cadeia inteira e a auditoria.
        recentes = db.scalars(select(Audit.seq).where(Audit.tenant_id == tenant_id)
                              .order_by(Audit.seq.desc()).limit(limite)).all()
        consulta = consulta.where(Audit.seq >= min(recentes)) if recentes else consulta
    linhas = list(db.scalars(consulta))
    total = db.scalar(select(func.count()).select_from(Audit).where(Audit.tenant_id == tenant_id))
    problemas, anterior_seq, anterior_hash = [], None, None
    for linha in linhas:
        if not linha.hash_self:
            problemas.append({"seq": linha.seq, "id": linha.id, "falha": "linha fora da cadeia (sem selo)"})
            anterior_seq, anterior_hash = linha.seq, None
            continue
        if anterior_seq is not None and linha.seq != anterior_seq + 1:
            problemas.append({"seq": linha.seq, "id": linha.id,
                              "falha": f"salto na numeracao: {anterior_seq} → {linha.seq}"})
        esperado_prev = GENESIS if linha.seq == 1 else anterior_hash
        if anterior_hash is not None or linha.seq == 1:
            if linha.hash_prev != esperado_prev:
                problemas.append({"seq": linha.seq, "id": linha.id,
                                  "falha": "elo anterior não confere com a linha que o precede"})
        if impressao(linha.seq, linha) != linha.hash_self:
            problemas.append({"seq": linha.seq, "id": linha.id,
                              "falha": "conteúdo alterado depois de gravado"})
        anterior_seq, anterior_hash = linha.seq, linha.hash_self
    return {"integra": not problemas, "conferidas": len(linhas), "total_na_organizacao": total,
            "primeira_seq": linhas[0].seq if linhas else None,
            "ultima_seq": linhas[-1].seq if linhas else None,
            # Um buraco no fim da numeracao e o unico apagamento que nao quebra elo nenhum.
            "linhas_faltando": max(0, (linhas[-1].seq - linhas[0].seq + 1) - len(linhas)) if linhas else 0,
            "problemas": problemas[:50], "problemas_total": len(problemas)}
