from datetime import datetime
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, EmailStr, Field, StringConstraints

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Text = Annotated[str, StringConstraints(max_length=20000)]
Cents = Annotated[int, Field(strict=True, ge=0, le=100_000_000_000)]
Identifier = Annotated[str, StringConstraints(max_length=36)]
Password = Annotated[str, StringConstraints(strip_whitespace=False, min_length=1, max_length=200)]
NewPassword = Annotated[str, StringConstraints(strip_whitespace=False, min_length=12, max_length=200)]


def iso_date(value: str):
    if len(value) < 10 or value[4] != "-" or value[7] != "-":
        raise ValueError("Data ISO-8601 obrigatória")
    datetime.fromisoformat(value)
    return value


DateText = Annotated[str, StringConstraints(max_length=40), AfterValidator(iso_date)]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Contact(StrictModel):
    name: Name
    email: EmailStr | None = None
    phone: str = Field(default="", max_length=40)
    company: str = Field(default="", max_length=200)
    company_id: Identifier | None = None
    status: Literal["new", "qualified", "active", "customer", "inactive", "lead"] = "new"
    source: str = Field(default="manual", max_length=100)
    tags: list[Name] = Field(default_factory=list, max_length=30)
    score: int = Field(default=0, ge=0, le=100)
    consent: bool = False
    notes: Text = ""
    owner_id: Identifier | None = None


class Company(StrictModel):
    name: Name
    website: str = Field(default="", max_length=500)
    industry: str = Field(default="", max_length=100)
    email: EmailStr | None = None
    phone: str = Field(default="", max_length=40)
    document: str = Field(default="", max_length=40)
    status: Literal["active", "inactive", "prospect"] = "active"
    notes: Text = ""


class Deal(StrictModel):
    title: Name
    contact_id: Identifier | None = None
    company_id: Identifier | None = None
    stage: Literal["lead", "qualified", "proposal", "negotiation", "won", "lost"] = "lead"
    value_cents: Cents = 0
    probability: int = Field(default=0, ge=0, le=100)
    expected_close: DateText | None = None
    owner_id: Identifier | None = None
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


RESOURCES = {"contacts": Contact, "companies": Company, "deals": Deal, "tasks": Task,
             "conversations": Conversation, "messages": Message, "campaigns": Campaign,
             "automations": Automation, "knowledge": Knowledge, "approvals": Approval,
             "agents": Agent, "projects": Project, "invoices": Invoice, "products": Product}


class Login(StrictModel):
    # Local bootstrap addresses deliberately supported without DNS/TLD verification.
    email: str = Field(min_length=3, max_length=320)
    password: Password


class TeamCreate(StrictModel):
    name: Name
    email: EmailStr
    password: NewPassword
    role: Literal["admin", "member", "viewer"] = "member"


class TeamUpdate(StrictModel):
    name: Name | None = None
    role: Literal["owner", "admin", "member", "viewer"] | None = None
    active: bool | None = None


class PasswordChange(StrictModel):
    current_password: Password
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
