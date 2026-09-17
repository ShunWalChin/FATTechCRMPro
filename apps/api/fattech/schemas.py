from datetime import datetime, timezone
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, EmailStr, Field, StringConstraints, field_validator, model_validator

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Text = Annotated[str, StringConstraints(max_length=20000)]
Cents = Annotated[int, Field(strict=True, ge=0, le=100_000_000_000)]
Identifier = Annotated[str, StringConstraints(max_length=36)]
StageKey = Annotated[str, StringConstraints(strip_whitespace=True, to_lower=True, max_length=40,
                                            pattern=r"^[a-z][a-z0-9_-]{0,39}$")]
Password = Annotated[str, StringConstraints(strip_whitespace=False, min_length=1, max_length=200)]
NewPassword = Annotated[str, StringConstraints(strip_whitespace=False, min_length=12, max_length=200)]
# Single source for the stage duration the radar measures against, shared with services and migration 0003.
DEFAULT_STAGE_HOURS = 72


def iso_date(value: str):
    if len(value) < 10 or value[4] != "-" or value[7] != "-":
        raise ValueError("Data ISO-8601 obrigatória")
    parsed = datetime.fromisoformat(value)
    if len(value) == 10:
        return parsed.date().isoformat()
    # The database and UI share one representation, including offsets and naive ISO input.
    return (parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed.astimezone(timezone.utc)).isoformat()


DateText = Annotated[str, StringConstraints(max_length=40), AfterValidator(iso_date)]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Qualification(StrictModel):
    """BANT declarado por uma pessoa. Cada eixo e opcional: nao saber e um estado legitimo,
    e forcar um valor padrao inventaria uma qualificacao que ninguem fez."""
    fit: Literal["alto", "medio", "baixo", "desconhecido"] = "desconhecido"
    intent: Literal["alto", "medio", "baixo", "desconhecido"] = "desconhecido"
    budget: Literal["confirmado", "estimado", "ausente", "desconhecido"] = "desconhecido"
    timeline: Literal["imediato", "trimestre", "ano", "sem_prazo", "desconhecido"] = "desconhecido"
    icp: bool | None = None
    notes: Text = ""


class Contact(StrictModel):
    name: Name
    email: EmailStr | None = None
    phone: str = Field(default="", max_length=40)
    company: str = Field(default="", max_length=200)
    company_id: Identifier | None = None
    status: Literal["new", "qualified", "active", "customer", "inactive", "lead"] = "new"
    source: str = Field(default="manual", max_length=100)
    tags: list[Name] = Field(default_factory=list, max_length=30)
    score: int = Field(default=0, strict=True, ge=0, le=100)
    consent: bool = False
    notes: Text = ""
    owner_id: Identifier | None = None
    # Ciclo de vida do lead, separado de status: status descreve o relacionamento, lead_stage descreve
    # onde a qualificacao parou. Misturar os dois foi o que obrigou a distinguir os dois campos.
    lead_stage: Literal["novo", "em_contato", "qualificado", "descartado", "convertido"] = "novo"
    disqualified_reason: str = Field(default="", max_length=400)
    next_action_at: DateText | None = None
    qualification: Qualification = Field(default_factory=Qualification)
    campaign_id: Identifier | None = None
    # UTM deixa de viver so dentro de attribution: campo consultavel e o que permite agrupar por origem.
    utm_source: str = Field(default="", max_length=200)
    utm_medium: str = Field(default="", max_length=200)
    utm_campaign: str = Field(default="", max_length=200)
    utm_content: str = Field(default="", max_length=200)
    utm_term: str = Field(default="", max_length=200)


class Company(StrictModel):
    name: Name
    website: str = Field(default="", max_length=500)
    industry: str = Field(default="", max_length=100)
    email: EmailStr | None = None
    phone: str = Field(default="", max_length=40)
    document: str = Field(default="", max_length=40)
    status: Literal["active", "inactive", "prospect"] = "active"
    notes: Text = ""


class PipelineStage(StrictModel):
    key: StageKey
    label: Name
    probability: int = Field(default=0, strict=True, ge=0, le=100)
    outcome: Literal["open", "won", "lost"] = "open"
    # How long a deal is expected to sit here; the radar measures staleness against this, not a global constant.
    expected_duration_hours: int = Field(default=DEFAULT_STAGE_HOURS, strict=True, ge=1, le=8760)
    required_fields: list[Literal["contact_id", "company_id", "owner_id", "value_cents", "expected_close", "next_action_at"]] = Field(default_factory=list, max_length=6)

    @field_validator("required_fields")
    @classmethod
    def unique_requirements(cls, values):
        if len(values) != len(set(values)):
            raise ValueError("Campos obrigatórios não podem se repetir")
        return values

    @model_validator(mode="after")
    def terminal_probability(self):
        if self.outcome != "open":
            self.probability = 100 if self.outcome == "won" else 0
        return self


class Pipeline(StrictModel):
    name: Name
    description: Text = ""
    status: Literal["active", "inactive"] = "active"
    is_default: bool = False
    stages: list[PipelineStage] = Field(min_length=1, max_length=40)
    loss_reasons: list[Name] = Field(default_factory=list, max_length=50)

    @field_validator("stages")
    @classmethod
    def unique_stage_keys(cls, stages):
        if len({stage.key for stage in stages}) != len(stages):
            raise ValueError("Chaves de etapas devem ser únicas no funil")
        return stages

    @field_validator('loss_reasons')
    @classmethod
    def unique_loss_reasons(cls, values):
        if len({value.casefold() for value in values}) != len(values):
            raise ValueError('Motivos de perda devem ser únicos')
        return values


# Migration 0002 stores this literal without validation, so every field the schema reads must be present.
DEFAULT_PIPELINE = {"name": "Funil comercial", "status": "active", "is_default": True,
                    # Empty keeps free text: a team standardises its reasons when it knows them.
                    "loss_reasons": [],
                    "description": "Etapas iniciais do processo comercial. Ajuste conforme a sua operação.",
                    # Durations only steer the radar, and 72h is what an absent field already resolved to,
                    # so adding them here changes no behaviour for a database migrated before this field existed.
                    # An empty requirement list is the only default that keeps legacy funnels advancing.
                    "stages": [{"key": "lead", "label": "Entrada", "probability": 10, "outcome": "open",
                                "expected_duration_hours": 48,
                                "required_fields": []},
                               {"key": "qualified", "label": "Qualificação", "probability": 30, "outcome": "open",
                                "expected_duration_hours": 72,
                                "required_fields": []},
                               {"key": "proposal", "label": "Proposta", "probability": 60, "outcome": "open",
                                "expected_duration_hours": 120,
                                "required_fields": []},
                               {"key": "negotiation", "label": "Negociação", "probability": 80, "outcome": "open",
                                "expected_duration_hours": 120,
                                "required_fields": []},
                               {"key": "won", "label": "Ganho", "probability": 100, "outcome": "won",
                                "expected_duration_hours": 72,
                                "required_fields": []},
                               {"key": "lost", "label": "Perdido", "probability": 0, "outcome": "lost",
                                "expected_duration_hours": 72,
                                "required_fields": []}]}


class Deal(StrictModel):
    title: Name
    contact_id: Identifier | None = None
    company_id: Identifier | None = None
    pipeline_id: Identifier | None = None
    stage: StageKey = "lead"
    value_cents: Cents = 0
    probability: int = Field(default=0, strict=True, ge=0, le=100)
    expected_close: DateText | None = None
    next_action_at: DateText | None = None
    position: int = Field(default=0, strict=True, ge=0, le=1_000_000_000)
    owner_id: Identifier | None = None
    lost_reason: str = Field(default="", max_length=500)
    notes: Text = ""


class Task(StrictModel):
    title: Name
    description: Text = ""
    status: Literal["todo", "in_progress", "done"] = "todo"
    priority: Literal["low", "medium", "high", "urgent"] = "medium"
    due_date: DateText | None = None
    contact_id: Identifier | None = None
    deal_id: Identifier | None = None
    project_id: Identifier | None = None
    owner_id: Identifier | None = None


class Conversation(StrictModel):
    title: Name
    contact_id: Identifier | None = None
    channel: Literal["internal", "whatsapp", "instagram", "email"] = "internal"
    status: Literal["open", "pending", "closed"] = "open"
    owner_id: Identifier | None = None
    last_message: str = Field(default="", max_length=1000)
    last_inbound_at: Literal[None] = None


class Message(StrictModel):
    conversation_id: Identifier
    body: Annotated[str, StringConstraints(min_length=1, max_length=10000)]
    direction: Literal["outbound"] = "outbound"
    status: Literal["draft"] = "draft"


class Campaign(StrictModel):
    name: Name
    channel: Literal["email", "whatsapp", "instagram", "social", "ads"] = "email"
    status: Literal["draft", "paused", "archived"] = "draft"
    budget_cents: Cents = 0
    audience: str = Field(default="", max_length=2000)
    scheduled_at: DateText | None = None
    content: Text = ""
    tags: list[Name] = Field(default_factory=list, max_length=30)


class FlowNode(StrictModel):
    id: Name
    type: Literal["start", "condition", "message", "delay", "set", "end", "handoff", "ai", "webhook"]
    config: dict = Field(default_factory=dict)


class FlowEdge(StrictModel):
    source: Name
    target: Name
    condition: str = Field(default="", max_length=100)


class Automation(StrictModel):
    name: Name
    description: Text = ""
    status: Literal["draft", "paused"] = "draft"
    trigger: str = Field(default="manual", max_length=100)
    nodes: list[FlowNode] = Field(default_factory=list, max_length=100)
    edges: list[FlowEdge] = Field(default_factory=list, max_length=200)


class Knowledge(StrictModel):
    title: Name
    content: Text = ""
    category: str = Field(default="general", max_length=100)
    tags: list[Name] = Field(default_factory=list, max_length=30)
    source: str = Field(default="", max_length=1000)


class Approval(StrictModel):
    title: Name
    gate: Literal["G1", "G2", "G3", "G4", "G5", "G6"] = "G3"
    description: Text = ""
    status: Literal["pending"] = "pending"
    intent: dict = Field(default_factory=dict)


class Agent(StrictModel):
    name: Name
    squad: str = Field(default="", max_length=100)
    role: str = Field(default="", max_length=100)
    status: Literal["paused"] = "paused"
    autonomy: Literal["A0", "A1"] = "A0"
    description: Text = ""
    budget_cents: Cents = 0
    spent_cents: Literal[0] = 0


class Project(StrictModel):
    name: Name
    description: Text = ""
    status: Literal["planning", "active", "paused", "completed"] = "planning"
    company_id: Identifier | None = None
    owner_id: Identifier | None = None
    budget_cents: Cents = 0
    due_date: DateText | None = None
    progress: int = Field(default=0, ge=0, le=100)


class Invoice(StrictModel):
    title: Name
    company_id: Identifier | None = None
    contact_id: Identifier | None = None
    status: Literal["draft", "pending", "paid", "overdue", "cancelled"] = "draft"
    amount_cents: Cents = 0
    due_date: DateText | None = None
    notes: Text = ""


class Product(StrictModel):
    name: Name
    description: Text = ""
    sku: str = Field(default="", max_length=100)
    price_cents: Cents = 0
    category: str = Field(default="service", max_length=100)
    status: Literal["active", "inactive"] = "active"


OPERADORES = ("igual", "diferente", "contem", "em", "maior", "maior_igual", "menor", "menor_igual",
              "preenchido", "vazio")


class ScoreCriterion(StrictModel):
    """Um criterio explicavel: o rotulo e o que aparece para a pessoa, nao a expressao."""
    label: Name
    field: Annotated[str, StringConstraints(strip_whitespace=True, max_length=60,
                                            pattern=r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)?$")]
    operator: Literal[OPERADORES]
    value: str = Field(default="", max_length=400)
    points: int = Field(strict=True, ge=-100, le=100)


class LeadAssignment(StrictModel):
    """menor_carga em vez de ponteiro rotativo: um ponteiro guardado dessincroniza quando alguem
    sai da equipe ou um lead e reatribuido a mao, e ninguem percebe ate a fila ficar torta."""
    strategy: Literal["nenhuma", "menor_carga"] = "nenhuma"
    # owner e o papel do usuario inicial do bootstrap: deixa-lo de fora tornaria a distribuicao
    # inoperante justamente na organizacao recem-criada, que e onde ela precisa funcionar primeiro.
    roles: list[Literal["root", "super_admin", "owner", "admin", "member"]] = Field(
        default_factory=lambda: ["owner", "admin", "member"], max_length=5)


class LeadRules(StrictModel):
    name: Name
    description: Text = ""
    status: Literal["active", "inactive"] = "inactive"
    criteria: list[ScoreCriterion] = Field(default_factory=list, max_length=40)
    warm_at: int = Field(default=35, strict=True, ge=0, le=100)
    hot_at: int = Field(default=65, strict=True, ge=0, le=100)
    sla_hours: int = Field(default=24, strict=True, ge=1, le=720)
    assignment: LeadAssignment = Field(default_factory=LeadAssignment)

    @model_validator(mode="after")
    def validate_thresholds(self):
        if self.warm_at >= self.hot_at:
            raise ValueError("O limite de morno precisa ser menor que o de quente")
        chaves = [criterion.label.strip().lower() for criterion in self.criteria]
        if len(chaves) != len(set(chaves)):
            raise ValueError("Cada critério precisa de um rótulo distinto")
        return self


RESOURCES = {"contacts": Contact, "companies": Company, "pipelines": Pipeline, "deals": Deal, "tasks": Task,
             "conversations": Conversation, "messages": Message, "campaigns": Campaign,
             "automations": Automation, "knowledge": Knowledge, "approvals": Approval,
             "agents": Agent, "projects": Project, "invoices": Invoice, "products": Product,
             "lead_rules": LeadRules}


class ContactImport(StrictModel):
    """`commit` false previews the same batch the confirmation will write."""
    rows: list[dict] = Field(min_length=1, max_length=500)
    commit: bool = False


class Login(StrictModel):
    # Local bootstrap addresses deliberately supported without DNS/TLD verification.
    email: str = Field(min_length=3, max_length=320)
    password: Password


class TeamCreate(StrictModel):
    name: Name
    email: EmailStr
    password: NewPassword
    role: Literal["root", "super_admin", "admin", "member", "viewer"] = "member"


class TeamUpdate(StrictModel):
    name: Name | None = None
    role: Literal["root", "super_admin", "owner", "admin", "member", "viewer"] | None = None
    active: bool | None = None


class PasswordChange(StrictModel):
    current_password: Password
    new_password: NewPassword


class PasswordReset(StrictModel):
    new_password: NewPassword


class Lead(StrictModel):
    name: Name
    email: EmailStr
    phone: str = Field(default="", max_length=40)
    company: str = Field(default="", max_length=200)
    interest: str = Field(default="", max_length=200)
    message: Text = ""
    consent: Literal[True]
    utm_source: str = Field(default="", max_length=200)
    utm_medium: str = Field(default="", max_length=200)
    utm_campaign: str = Field(default="", max_length=200)
    utm_content: str = Field(default="", max_length=200)
    utm_term: str = Field(default="", max_length=200)


class KeyCreate(StrictModel):
    name: Name
    scopes: list[str] = Field(min_length=1, max_length=40)
    expires_in_days: int = Field(default=90, ge=1, le=365)


class Webhook(StrictModel):
    event_type: str = Field(pattern=r"^[a-z][a-z0-9_.-]{1,99}$")
    payload: dict
    trace_id: str | None = Field(default=None, max_length=100)
    hops: int = Field(default=0, ge=0, le=5)


class Version(StrictModel):
    version: int = Field(ge=1, strict=True)


class Decision(Version):
    decision: Literal["approved", "rejected"]
    reason: str = Field(default="", max_length=2000)


class Simulation(StrictModel):
    input: dict = Field(default_factory=dict)
