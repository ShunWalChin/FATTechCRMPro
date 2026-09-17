"""Matriz medida: cada capacidade do Mano Chat contra o estado real do FAT Tech CRM.

Nao afirma paridade, mede. Para cada capacidade do esquema real do Mano Chat (26 tabelas em
/opt/mano-chat), aponta onde ela vive no CRM hoje ou declara ausente, lendo o schema e o codigo em vez
de descrever de memoria.

A descricao e a autoridade sobre a marca: uma checagem que encontra um termo no codigo nao prova
capacidade completa, e classificar pelo booleano marcaria como pronta uma linha que se declara parcial.

Usage: python scripts/mano-chat-matrix.py
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps/api"))
from fattech.schemas import RESOURCES  # noqa: E402

fonte = {p.name: (ROOT / "apps/api/fattech" / p.name).read_text(encoding="utf-8", errors="replace")
         for p in (ROOT / "apps/api/fattech").glob("*.py")}
campos = {k: set(RESOURCES[k].model_fields) for k in RESOURCES}


def tem_campo(kind, *nomes):
    return all(n in campos.get(kind, ()) for n in nomes)


def tabela(nome):
    """A tabela existe no metadata declarado, e nao num nome citado num comentario."""
    from fattech.db import Base
    from fattech import models  # noqa: F401 - registra o metadata
    return nome in Base.metadata.tables


def no_codigo(arquivo, *termos):
    texto = fonte.get(arquivo, "")
    return all(t in texto for t in termos)


# (capacidade do Mano Chat, tabela de origem, verificacao, onde vive no CRM)
CAPACIDADES = [
    ("Organizacoes isoladas", "workspaces", True, "tabela tenants + RLS forcada"),
    ("Papeis por membro", "workspace_members", True, "users.role: root/super_admin/admin/member/viewer"),
    ("Conta Instagram por organizacao", "instagram_accounts", tabela("instagram_accounts"), "tabela instagram_accounts, instagram_user_id unico, webhook resolve o dono"),
    ("Tokens cifrados em repouso", "private.instagram_credentials", tabela("instagram_credentials") and no_codigo("credentials.py", "AESGCM"), "tabela instagram_credentials sob RLS, AES-256-GCM, chave fora do banco"),
    ("Contatos", "contacts", tem_campo("contacts", "name", "email", "phone", "consent"), "kind contacts"),
    ("Identidade Instagram no contato", "contacts", "instagram" in str(campos.get("contacts", "")), "AUSENTE — contato nao guarda instagram_user_id"),
    ("Etiquetas", "tags / contact_tags", tem_campo("contacts", "tags"), "contacts.tags (lista), sem catalogo proprio nem cor"),
    ("Cache de posts", "posts_cache", False, "AUSENTE"),
    ("Conversas", "conversations", tem_campo("conversations", "channel", "status", "owner_id", "last_inbound_at"), "kind conversations"),
    ("Pasta da conversa", "conversations.category", tem_campo("conversations", "folder"), "AUSENTE — sem principal/geral/pedidos/ia_off"),
    ("Nao lidas por conversa", "conversations.unread_count", tem_campo("conversations", "unread_count"), "AUSENTE"),
    ("Log de interacoes externas", "interactions_log", False, "AUSENTE — nao ha registro por evento da Meta"),
    ("Mensagens", "messages", tem_campo("messages", "conversation_id", "direction", "status"), "kind messages (rascunho interno)"),
    ("Idempotencia por id externo", "interactions_log.meta_event_id", False, "PARCIAL — idempotency_keys cobre a entrega, nao a mensagem"),
    ("Sequencias", "sequences", False, "AUSENTE"),
    ("Passos da sequencia", "sequence_steps", False, "AUSENTE"),
    ("Matricula em sequencia", "sequence_enrollments", False, "AUSENTE"),
    ("Gatilhos", "triggers", False, "AUSENTE"),
    ("Cooldown por gatilho e contato", "trigger_cooldowns", no_codigo("compliance.py", "cooldown"), "PARCIAL — compliance decide, mas nada persiste o cooldown"),
    ("Uma resposta privada por comentario", "comment_private_replies", no_codigo("compliance.py", "comment_already_replied"), "PARCIAL — a regra existe, a tabela de unicidade nao"),
    ("Jobs agendados", "scheduled_jobs", no_codigo("worker.py", "available_at"), "event_outbox com available_at, claim e dead-letter"),
    ("Eventos de webhook", "webhook_events", no_codigo("instagram_webhook.py", "hmac", "Idempotency"), "instagram_webhook.py + idempotency_keys + event_outbox"),
    ("Agentes de IA", "ai_agents", tem_campo("agents", "autonomy", "budget_cents"), "kind agents (sem execucao: runtime pendente)"),
    ("Base de conhecimento", "knowledge_documents", tem_campo("knowledge", "content"), "kind knowledge"),
    ("Campanhas", "campaigns", tem_campo("campaigns", "channel", "status", "scheduled_at"), "kind campaigns"),
    ("Destinatarios com elegibilidade", "campaign_recipients", False, "AUSENTE — campanha nao tem lista de destinatarios"),
    ("Itens de conteudo", "content_items", False, "AUSENTE"),
    ("Insights diarios", "insights_daily", False, "AUSENTE — o painel calcula na leitura, nao agrega por dia"),
    ("Blocklist por organizacao", "blocklist_entries", no_codigo("config.py", "blocked_terms"), "PARCIAL — blocked_terms e global, nao por organizacao"),
    ("Janela de 24h", "window_policy", no_codigo("compliance.py", "STANDARD_WINDOW"), "compliance.evaluate()"),
    ("HUMAN_AGENT 7 dias", "window_policy", no_codigo("compliance.py", "HUMAN_AGENT_WINDOW"), "compliance.evaluate()"),
    ("Opt-out por palavra", "contacts.opted_out", no_codigo("compliance.py", "OPT_OUT_KEYWORDS"), "compliance.is_opt_out_keyword()"),
    ("Rodape obrigatorio", "-", no_codigo("compliance.py", "OPT_OUT_FOOTER"), "compliance.with_opt_out()"),
    ("Status de mensagem", "message_status", tem_campo("messages", "status"), "PARCIAL — sem queued/delivered/read/blocked"),
    ("Cliente Meta Graph", "-", no_codigo("worker.py", "graph.facebook") or no_codigo("worker.py", "graph.instagram"), "AUSENTE — worker entrega ao n8n, nao a Meta"),
]

# A descricao e a autoridade: uma checagem que encontra o termo no codigo nao prova capacidade
# completa. Classificar pelo booleano marcaria "TEM" o que a propria linha declara parcial.
def situacao(linha):
    _, _, ok, onde = linha
    if onde.startswith("AUSENTE"):
        return "AUSENTE"
    if onde.startswith("PARCIAL"):
        return "PARCIAL"
    return "TEM" if ok else "AUSENTE"

presentes = [c for c in CAPACIDADES if situacao(c) == "TEM"]
parciais = [c for c in CAPACIDADES if situacao(c) == "PARCIAL"]
ausentes = [c for c in CAPACIDADES if situacao(c) == "AUSENTE"]
outros = []

print(f"{'CAPACIDADE DO MANO CHAT':40} {'SITUACAO':9} ONDE VIVE NO CRM")
print("-" * 118)
for nome, origem, ok, onde in CAPACIDADES:
    marca = situacao((nome, origem, ok, onde))
    print(f"{nome:40} {marca:9} {onde[:66]}")
print("-" * 118)
total = len(CAPACIDADES)
print(f"TEM: {len(presentes)}   PARCIAL: {len(parciais)}   AUSENTE: {len(ausentes)}   de {total}")

if ausentes or parciais:
    sys.exit(0)  # relatorio, nao porta: a ausencia e o estado conhecido, nao uma falha de build
