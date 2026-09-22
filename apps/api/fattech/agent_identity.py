"""A identidade do agente: um `Principal` proprio, nunca uma pessoa emprestada.

`fattech:openclaw:agente-como-principal`. O agente ganha um `users` com papel `root` marcado como
agente, e uma chave de API criada **em nome dele**. Isso importa mais do que parece: `require_auth`
resolve o papel a partir de `api_keys.created_by`, entao uma chave criada por uma pessoa faria o
agente agir como aquela pessoa, e a trilha registraria as acoes autonomas no nome dela.

Tres garantias que essa escolha herda do sistema, sem uma linha de regra nova:

1. `Principal.admin()` recusa **qualquer** chave de API. O agente nao promove a equipe, nao troca
   senha, nao cria chave e nao le a trilha de auditoria. Nao e uma restricao que eu adicionei para
   ele -- e o que o codigo ja faz, e o agente herda por ser chave.
2. Toda acao dele carrega `actor_id` do agente na trilha selada, entao e atribuivel e verificavel
   por terceiro em `GET /api/v1/audit/verify`.
3. Desligar o agente e uma chamada, sem deploy e sem migracao -- mas **nao** pela via generica de
   chaves. Ver `desligar()`: `can_manage` exige patente estritamente maior e o agente e `root`,
   entao nem o owner que o criou alcancava `DELETE /api/v1/api-keys/{id}`. Isso apareceu num teste,
   depois de eu ter escrito aqui que revogar bastava.

A senha do usuario-agente e um valor aleatorio descartado no ato: ele **nao tem login**. Gravar um
hash de senha que ninguem conhece e mais seguro que deixar a coluna vazia, porque uma coluna vazia
convida um `if not password_hash` a virar porta em alguma refatoracao futura.
"""
import secrets
from datetime import timedelta

from fastapi import HTTPException
from sqlalchemy import select

from . import agent_tools
from .models import ApiKey, User, now, uid
from .security import digest, hasher
from .services import audit_event, get_record

# Dominio reservado: nao resolve na internet, e deixa obvio na tela de equipe que nao e uma pessoa.
DOMINIO_AGENTE = "agent.local"
VALIDADE_DIAS = 90


def email_do_agente(tenant_slug: str, agent_id: str) -> str:
    return f"openclaw+{agent_id[:8]}@{tenant_slug}.{DOMINIO_AGENTE}"


def usuario_do_agente(db, tenant_id: str, agent_id: str):
    return db.scalar(select(User).where(User.tenant_id == tenant_id, User.is_agent.is_(True),
                                       User.name == f"agente:{agent_id}"))


def desligar(db, principal, agent_id: str) -> dict:
    """Revoga todas as chaves ativas do agente e desativa o usuario dele. E o botao de desligar.

    Ele existe porque a via generica **nao alcanca**: `can_manage` exige patente estritamente maior,
    e o agente e `root`. Um owner que criou o agente nao conseguia revogar a chave dele pelo
    `DELETE /api/v1/api-keys/{id}` -- descoberto por teste, nao por leitura. Um botao de desligar que
    o operador nao alcanca nao e botao de desligar.

    A excecao e estreita de proposito: nao afrouxa a regra de patente entre pessoas. Ela vale para
    `is_agent`, e o motivo e que um agente nao e uma pessoa com patente -- contencao de automatismo
    nao pode depender de superar a patente do automatismo.
    """
    usuario = usuario_do_agente(db, principal.tenant_id, agent_id)
    if usuario is None:
        raise HTTPException(404, "Este agente não tem identidade provisionada")
    if not usuario.is_agent:
        # Salvaguarda: esta rota nunca desativa uma pessoa, aconteca o que acontecer com a consulta.
        raise HTTPException(409, "Esta identidade não é de agente")
    chaves = list(db.scalars(select(ApiKey).where(ApiKey.tenant_id == principal.tenant_id,
                                                 ApiKey.created_by == usuario.id,
                                                 ApiKey.revoked.is_(False))))
    for chave in chaves:
        chave.revoked = True
    usuario.active = False
    audit_event(db, principal.tenant_id, principal.actor_id, "agent.identity_disabled", usuario.id,
                {"agent_id": agent_id, "chaves_revogadas": [chave.id for chave in chaves]})
    return {"agent_id": agent_id, "user_id": usuario.id, "active": False,
            "chaves_revogadas": len(chaves),
            "nota": ("O agente está desligado. Provisionar de novo reativa o usuário e emite chave "
                     "nova; as chaves revogadas aqui não voltam.")}


def provisionar(db, principal, tenant_slug: str, agent_id: str, ferramentas: list[str]) -> dict:
    """Cria (ou reaproveita) o usuario-agente e emite uma chave nova com os escopos das ferramentas.

    Emitir chave nova **nao** revoga a anterior automaticamente: rotacao e revogacao sao decisoes
    diferentes, e revogar em silencio derrubaria um agente em operacao no meio de uma corrida. A
    resposta diz quantas chaves ativas existem para quem decidir.
    """
    desconhecidas = agent_tools.desconhecidas(ferramentas)
    if desconhecidas:
        raise HTTPException(422, f"Ferramenta desconhecida: {', '.join(desconhecidas)}")
    # O agente precisa existir como configuracao antes de existir como identidade.
    registro = get_record(db, principal.tenant_id, "agents", agent_id)
    derivados = agent_tools.escopos_de(ferramentas)
    if not derivados:
        raise HTTPException(422, "Um agente sem ferramenta declarada não recebe chave")
    # Alem dos escopos das ferramentas, o agente precisa operar o proprio ciclo: abrir corrida,
    # tentar acao, encerrar. Sem isso a chave nao alcanca nem o portao, e a ferramenta declarada
    # seria uma permissao que nunca chega a ser exercida.
    escopos = sorted(derivados | {"agent:operate", "agents:read"})

    usuario = usuario_do_agente(db, principal.tenant_id, agent_id)
    if usuario is None:
        usuario = User(tenant_id=principal.tenant_id, email=email_do_agente(tenant_slug, agent_id),
                       name=f"agente:{agent_id}", role="root", is_agent=True, active=True,
                       # Senha aleatoria descartada: o agente nao faz login, e coluna vazia convida
                       # um `if not password_hash` a virar porta.
                       password_hash=hasher.hash(secrets.token_urlsafe(32)))
        db.add(usuario)
        db.flush()
        audit_event(db, principal.tenant_id, principal.actor_id, "agent.identity_created", usuario.id,
                    {"agent_id": agent_id, "agent_name": (registro.data or {}).get("name", "")})
    elif not usuario.active:
        # Reprovisionar reativa: desligar precisa ser reversivel, ou vira exclusao com outro nome.
        usuario.active = True
        audit_event(db, principal.tenant_id, principal.actor_id, "agent.identity_reenabled", usuario.id,
                    {"agent_id": agent_id})

    token = "fat_" + secrets.token_urlsafe(40)
    chave = ApiKey(tenant_id=principal.tenant_id, created_by=usuario.id,
                   name=f"OpenClaw · {(registro.data or {}).get('name', agent_id)}"[:100],
                   key_hash=digest(token), prefix=token[:12], scopes=escopos,
                   expires_at=now() + timedelta(days=VALIDADE_DIAS))
    db.add(chave)
    db.flush()
    audit_event(db, principal.tenant_id, principal.actor_id, "agent.key_issued", chave.id,
                {"agent_id": agent_id, "scopes": escopos, "tools": sorted(ferramentas)})
    ativas = list(db.scalars(select(ApiKey.id).where(ApiKey.created_by == usuario.id,
                                                     ApiKey.revoked.is_(False))))
    return {
        "agent_id": agent_id, "user_id": usuario.id, "email": usuario.email, "role": usuario.role,
        "key_id": chave.id, "prefix": chave.prefix, "scopes": escopos,
        "tools": sorted(ferramentas), "expires_at": chave.expires_at.isoformat(),
        # O token aparece uma vez. Depois disso existe so a impressao digital do prefixo, no espirito
        # de `fattech:mano:impressao-digital` -- guarde agora ou emita outra.
        "key": token,
        "chaves_ativas": len(ativas),
        "aviso": ("Guarde a chave agora: ela não é exibida novamente. Emitir esta chave não revogou "
                  "as anteriores — rotação e revogação são decisões diferentes."
                  if len(ativas) > 1 else "Guarde a chave agora: ela não é exibida novamente."),
    }
