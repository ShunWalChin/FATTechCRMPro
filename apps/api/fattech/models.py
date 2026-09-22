from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


def now() -> datetime:
    return datetime.now(timezone.utc)


def uid() -> str:
    return str(uuid4())


class Tenant(Base):
    __tablename__ = "tenants"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    name: Mapped[str] = mapped_column(String(200))
    slug: Mapped[str] = mapped_column(String(80), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    email: Mapped[str] = mapped_column(String(320), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    password_hash: Mapped[str] = mapped_column(Text)
    role: Mapped[str] = mapped_column(String(20), default="member")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    # Um agente nao e uma pessoa com papel elevado: e outra categoria de ator. A marca existe para
    # que a tela de equipe nao ofereca troca de senha a quem nao tem senha, e para que a trilha
    # distinga acao autonoma de acao humana sem depender do formato do e-mail.
    is_agent: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class LoginSession(Base):
    __tablename__ = "login_sessions"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    id: Mapped[str] = mapped_column(String(36), unique=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    csrf_token: Mapped[str] = mapped_column(String(100))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)


class Record(Base):
    __tablename__ = "records"
    __table_args__ = (Index("ix_records_tenant_kind_active", "tenant_id", "kind", "deleted"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"))
    kind: Mapped[str] = mapped_column(String(40))
    data: Mapped[dict] = mapped_column(JSON, default=dict)
    version: Mapped[int] = mapped_column(Integer, default=1)
    deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Audit(Base):
    __tablename__ = "audit_log"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    actor_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    action: Mapped[str] = mapped_column(String(100))
    resource_id: Mapped[str] = mapped_column(String(100))
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    # Cadeia de integridade por organizacao, selada em audit_chain.py. seq comeca em 1, e a unicidade
    # de (tenant_id, seq) -- que transforma uma bifurcacao em erro de gravacao em vez de duas linhas
    # irmas -- e criada pela migracao 0007, nao declarada aqui. Declarar nos dois lugares daria duas
    # origens para a mesma regra: em banco novo ela viria do CREATE TABLE e em banco migrado do
    # indice, e so uma das duas seria removivel por quem precisasse reproduzir o estado anterior.
    seq: Mapped[int] = mapped_column(Integer, default=0)
    hash_prev: Mapped[str] = mapped_column(String(64), default="")
    hash_self: Mapped[str] = mapped_column(String(64), default="")


class Outbox(Base):
    __tablename__ = "event_outbox"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(100))
    payload: Mapped[dict] = mapped_column(JSON)
    actor: Mapped[dict] = mapped_column(JSON, default=dict)
    origin: Mapped[str] = mapped_column(String(30), default="legacy")
    trace_id: Mapped[str] = mapped_column(String(100), default=uid)
    hops: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(30), default="pending", index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, index=True)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    claim_token: Mapped[str | None] = mapped_column(String(36), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Idempotency(Base):
    __tablename__ = "idempotency_keys"
    __table_args__ = (UniqueConstraint("tenant_id", "key", name="uq_idempotency_tenant_key"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"))
    key: Mapped[str] = mapped_column(String(200))
    body_hash: Mapped[str] = mapped_column(String(64))
    response: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class KnowledgeChunk(Base):
    """Versioned retrieval units; embeddings remain provider-neutral until a vector backend is enabled."""
    __tablename__ = "knowledge_chunks"
    __table_args__ = (UniqueConstraint("tenant_id", "knowledge_id", "chunk_index", name="uq_knowledge_chunk"),
                      Index("ix_knowledge_chunks_tenant", "tenant_id", "knowledge_id"))
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    knowledge_id: Mapped[str] = mapped_column(String(36), index=True)
    chunk_index: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    # `metadata` e reservado pela API declarativa do SQLAlchemy e impedia o pacote inteiro de
    # importar. O atributo passa a ser `meta`; a coluna no banco continua chamando-se metadata.
    meta: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    embedding: Mapped[list | None] = mapped_column(JSON, nullable=True)
    content_hash: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class ApiKey(Base):
    __tablename__ = "api_keys"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(100))
    key_hash: Mapped[str] = mapped_column(String(64), unique=True)
    prefix: Mapped[str] = mapped_column(String(20))
    scopes: Mapped[list] = mapped_column(JSON)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class RateLimit(Base):
    __tablename__ = "rate_limits"
    bucket: Mapped[str] = mapped_column(String(100), primary_key=True)
    window: Mapped[int] = mapped_column(Integer)
    count: Mapped[int] = mapped_column(Integer, default=0)


class InstagramAccount(Base):
    """A conta Instagram de uma organizacao.

    Tabela real, e nao um kind em records, por dois motivos que so o banco resolve: o
    webhook precisa achar o tenant antes de existir contexto de tenant, e duas
    organizacoes nao podem reivindicar a mesma conta -- unicidade que so uma restricao
    garante. Fica fora de TENANT_TABLES pela mesma razao que users fica: a resolucao e
    anterior ao contexto. O escopo por tenant e aplicado em cada consulta.
    """
    __tablename__ = "instagram_accounts"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    instagram_user_id: Mapped[str] = mapped_column(String(64), unique=True)
    username: Mapped[str] = mapped_column(String(120), default="")
    label: Mapped[str] = mapped_column(String(200), default="")
    status: Mapped[str] = mapped_column(String(20), default="connected")
    version: Mapped[int] = mapped_column(Integer, default=1)
    connected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class InstagramCredential(Base):
    """O token, cifrado. Nunca e um kind: todo kind ganha GET /api/v1/{kind} que serializa data inteiro."""
    __tablename__ = "instagram_credentials"
    account_id: Mapped[str] = mapped_column(ForeignKey("instagram_accounts.id", ondelete="CASCADE"), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    sealed_token: Mapped[str] = mapped_column(Text)
    fingerprint: Mapped[str] = mapped_column(String(32))
    scopes: Mapped[list] = mapped_column(JSON, default=list)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rotated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class AgentRun(Base):
    """Uma corrida do agente: o evento que a disparou, a justificativa e o custo.

    Tabela real e nao kind, por `fattech:mano:paradigma-hibrido`: volume alto, append-only na
    pratica, e uma restricao de unicidade que so o banco garante.

    Essa restricao e a peca central. O outbox entrega **pelo menos uma vez**, entao o mesmo evento
    pode chegar duas vezes ao agente. Deixar a deduplicacao com o OpenClaw poria a garantia numa
    camada que um prompt contraria; aqui o segundo INSERT falha e nao existe caminho em que o
    cliente receba a mesma mensagem duas vezes por replay.

    `rationale` e o que fecha o buraco da trilha: a cadeia de hash responde o que aconteceu e quem
    fez, e nunca foi projetada para responder por que. Com metade das acoes vindo de um modelo, essa
    pergunta e a que o cliente faz. Declaracao honesta que acompanha o campo: e o que o modelo disse
    que pensou, nao prova do que pensou.
    """
    __tablename__ = "agent_runs"
    # A unicidade e por (organizacao, agente, evento), e nao por (organizacao, evento): dois agentes
    # podem observar o mesmo evento e cada um tem direito a sua corrida. A migracao 0010 corrigiu
    # isso depois que o despacho automatico do E4 revelou a colisao silenciosa.
    __table_args__ = (UniqueConstraint("tenant_id", "agent_id", "trigger_event_id",
                                       name="uq_run_por_agente_e_evento"),
                      Index("ix_agent_runs_tenant_inicio", "tenant_id", "started_at"))
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    agent_id: Mapped[str] = mapped_column(String(36), index=True)
    trigger_event_id: Mapped[str] = mapped_column(String(36))
    trigger_type: Mapped[str] = mapped_column(String(100))
    mode: Mapped[str] = mapped_column(String(24))
    status: Mapped[str] = mapped_column(String(24), default="pending", index=True)
    rationale: Mapped[str] = mapped_column(Text, default="")
    model: Mapped[str] = mapped_column(String(120), default="")
    tokens_in: Mapped[int] = mapped_column(Integer, default=0)
    tokens_out: Mapped[int] = mapped_column(Integer, default=0)
    cost_cents: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)


class AgentStep(Base):
    """Cada ferramenta que o agente tentou, permitida ou recusada, com o motivo.

    Append-only como `audit_log`, e pelo mesmo motivo: um historico onde so aparece o que deu certo
    nao serve de prova. A recusa e o registro mais valioso desta tabela -- e ela que mostra que o
    portao existe e funcionou.
    """
    __tablename__ = "agent_steps"
    __table_args__ = (UniqueConstraint("tenant_id", "run_id", "seq", name="uq_step_por_run"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("agent_runs.id"), index=True)
    seq: Mapped[int] = mapped_column(Integer)
    tool: Mapped[str] = mapped_column(String(120))
    arguments: Mapped[dict] = mapped_column(JSON, default=dict)
    decision: Mapped[str] = mapped_column(String(24))
    refusal_reason: Mapped[str] = mapped_column(String(200), default="")
    result_ref: Mapped[str] = mapped_column(String(100), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
