"""Explicit, repeatable owner bootstrap. Demo records require --demo and development mode."""
import argparse
import os
from datetime import timedelta

from sqlalchemy import select

from .config import get_settings
from .db import make_engine, session_factory, set_tenant
from .models import Record, Tenant, User, now
from .schemas import DEFAULT_PIPELINE
from .security import hasher
from .services import create_record, default_pipeline


def bootstrap(db, *, slug: str, email: str, password: str, name="FAT Tech", demo=False):
    if not email or "@" not in email or len(email) > 320:
        raise ValueError("FATTECH_BOOTSTRAP_EMAIL is required")
    if not 12 <= len(password) <= 200:
        raise ValueError("FATTECH_BOOTSTRAP_PASSWORD must contain 12 to 200 characters")
    tenant = db.scalar(select(Tenant).where(Tenant.slug == slug))
    if tenant is None:
        tenant = Tenant(name="FAT Tech", slug=slug)
        db.add(tenant)
        db.flush()
    set_tenant(db, tenant.id)
    user = db.scalar(select(User).where(User.email == email.strip().lower()))
    if user and (user.tenant_id != tenant.id or user.role != "owner"):
        raise ValueError("Bootstrap email belongs to another tenant or non-owner account")
    if user is None:
        user = User(tenant_id=tenant.id, email=email.strip().lower(), name=name,
                    password_hash=hasher.hash(password), role="owner")
        db.add(user)
        db.flush()
    # Every tenant needs a stage vocabulary before the first deal can be recorded.
    if default_pipeline(db, tenant.id) is None:
        create_record(db, tenant.id, user.id, "pipelines", DEFAULT_PIPELINE)
    # Re-running bootstrap never changes an existing owner's password or customer records.
    if demo and not db.scalar(select(Record.id).where(Record.tenant_id == tenant.id,
                                                      Record.kind != "pipelines").limit(1)):
        demo_records(db, tenant.id, user.id)
    db.commit()
    return tenant, user


def demo_records(db, tenant_id, user_id):
    def create(kind, payload):
        return create_record(db, tenant_id, user_id, kind, payload)

    company = create("companies", {"name": "Empresa Demonstração", "industry": "Serviços", "status": "prospect"})
    contact = create("contacts", {"name": "Contato Demonstração", "email": "demo@example.com",
        "company_id": company.id, "company": company.data["name"], "source": "demo", "tags": ["DEMONSTRAÇÃO"],
        "notes": "Registro fictício para explorar a interface. Não representa cliente ou receita real."})
    for stage, amount in (("lead", 120000), ("qualified", 250000), ("proposal", 380000)):
        create("deals", {"title": f"Demonstração · {stage}", "stage": stage, "contact_id": contact.id,
                         "company_id": company.id, "value_cents": amount, "owner_id": user_id})
    project = create("projects", {"name": "Projeto Demonstração", "status": "planning", "company_id": company.id})
    create("tasks", {"title": "Explore o CRM e remova os exemplos quando desejar", "priority": "medium",
                     "project_id": project.id, "owner_id": user_id, "due_date": (now() + timedelta(days=2)).date().isoformat()})
    conversation = create("conversations", {"title": "Conversa de demonstração", "contact_id": contact.id})
    create("messages", {"conversation_id": conversation.id, "body": "Rascunho de exemplo; nenhum envio foi realizado."})
    create("campaigns", {"name": "Campanha Demonstração", "status": "draft", "content": "Conteúdo de exemplo."})
    create("automations", {"name": "Qualificação de demonstração", "nodes": [
        {"id": "start", "type": "start"}, {"id": "message", "type": "message", "config": {"body": "Olá! Como podemos ajudar?"}},
        {"id": "end", "type": "end"}], "edges": [{"source": "start", "target": "message"}, {"source": "message", "target": "end"}]})
    create("knowledge", {"title": "Bem-vindo ao FAT Tech CRM", "category": "onboarding",
        "content": "Dados marcados Demonstração são fictícios. Provedores externos exigem configuração. Consulte API.md e os runbooks."})
    create("agents", {"name": "Assistente Comercial", "squad": "Vendas", "role": "Qualificação",
        "description": "Configuração de agente em pausa. Execução indisponível até integrar runtime e aprovação."})
    create("invoices", {"title": "Registro financeiro de demonstração", "status": "draft", "amount_cents": 120000})
    create("products", {"name": "Serviço de demonstração", "price_cents": 120000})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()
    settings = get_settings()
    if args.demo and settings.production:
        parser.error("Demo records are forbidden in production")
    engine = make_engine(settings.database_url)
    with session_factory(engine)() as db:
        bootstrap(db, slug=settings.public_tenant_slug,
                  email=os.environ.get("FATTECH_BOOTSTRAP_EMAIL", ""),
                  password=os.environ.get("FATTECH_BOOTSTRAP_PASSWORD", ""), demo=args.demo)
    print("Owner bootstrap complete. Existing credentials and records were preserved.")
    engine.dispose()


if __name__ == "__main__":
    main()
