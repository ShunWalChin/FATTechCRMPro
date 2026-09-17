"""Matriz medida da ORDEM PRINCIPAL DE ENGENHARIA contra o FAT Tech CRM Pro real.

Nao afirma paridade, mede. Cada capacidade que a ordem lista e conferida contra o schema
declarado, o codigo da API, as rotas efetivamente registradas, as tabelas do metadata e as
telas que existem no workspace -- e nao contra a lembranca de quem escreve.

A descricao e a autoridade sobre a marca. Uma checagem que encontra um termo no codigo nao
prova capacidade completa: classificar pelo booleano marcaria como pronta uma linha que a
propria descricao declara parcial. Por isso AUSENTE e PARCIAL vencem qualquer sonda.

O numero que importa nao e quantas capacidades existem: e o denominador. Uma verificacao que
compara pouco tambem termina sem encontrar problema.

Usage: python scripts/ordem-principal-matriz.py [--secao COMERCIAL]
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps/api"))

from fattech.config import Settings          # noqa: E402
from fattech.db import Base                  # noqa: E402
from fattech.main import create_app          # noqa: E402
from fattech.schemas import RESOURCES        # noqa: E402
from fattech import models                   # noqa: F401,E402  - registra o metadata

API = ROOT / "apps/api/fattech"
FONTE = {p.name: p.read_text(encoding="utf-8", errors="replace") for p in API.glob("*.py")}
TUDO = "\n".join(FONTE.values())
CAMPOS = {kind: set(modelo.model_fields) for kind, modelo in RESOURCES.items()}
TABELAS = set(Base.metadata.tables)
TELAS = {p.name for p in (ROOT / "apps/web/app/crm").iterdir() if p.is_dir()}
ROTAS = sorted({r.path for r in create_app(
    Settings(_env_file=None, env="test", database_url="sqlite:///:memory:")).routes if hasattr(r, "path")})


def campo(kind, *nomes):
    return all(nome in CAMPOS.get(kind, ()) for nome in nomes)


def codigo(arquivo, *termos):
    texto = FONTE.get(arquivo, "")
    return all(termo in texto for termo in termos)


def qualquer(*termos):
    return all(termo in TUDO for termo in termos)


def rota(fragmento):
    return any(fragmento in caminho for caminho in ROTAS)


def tabela(nome):
    return nome in TABELAS


def tela(nome):
    return nome in TELAS


# (secao, capacidade, sonda, onde vive no CRM -- ou AUSENTE / PARCIAL com o motivo)
CAPACIDADES = [
    # ---------------------------------------------------------------- COMERCIAL > LEADS
    ("COMERCIAL/Leads", "Captura manual", campo("contacts", "name", "source"), "kind contacts com source"),
    ("COMERCIAL/Leads", "Captura por site", rota("/public/leads"), "POST /api/v1/public/leads + capture_lead()"),
    ("COMERCIAL/Leads", "Captura por Instagram", False, "AUSENTE — webhook identifica a organizacao, nao cria lead"),
    ("COMERCIAL/Leads", "Captura por WhatsApp", False, "AUSENTE"),
    ("COMERCIAL/Leads", "Captura por formulario", rota("/public/leads"), "PARCIAL — endpoint existe, construtor de formularios nao"),
    ("COMERCIAL/Leads", "Captura por n8n", rota("/webhooks/n8n"), "POST /api/v1/webhooks/n8n com HMAC e escopo"),
    ("COMERCIAL/Leads", "Origem", campo("contacts", "source"), "contacts.source"),
    ("COMERCIAL/Leads", "Campanha", campo("contacts", "campaign_id", "utm_campaign"), "PARCIAL — campaign_id e utm_campaign existem; a campanha nao consolida resultado ainda"),
    ("COMERCIAL/Leads", "UTM", campo("contacts", "utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term"), "cinco campos consultaveis, promovidos de attribution pela migracao 0005"),
    ("COMERCIAL/Leads", "Responsavel", campo("contacts", "owner_id"), "contacts.owner_id"),
    ("COMERCIAL/Leads", "Score", codigo("services.py", "pontuar_contato"), "calculado por lead_rules ativo; edicao manual recusada com 409"),
    ("COMERCIAL/Leads", "Estagio do lead", campo("contacts", "lead_stage"), "contacts.lead_stage, separado de status"),
    ("COMERCIAL/Leads", "Ultima interacao", codigo("services.py", "last_interaction_at"), "gravada pelo servidor em toda atividade e captura"),
    ("COMERCIAL/Leads", "Proxima acao", campo("contacts", "next_action_at"), "contacts.next_action_at, com filtro sem_acao na fila"),
    ("COMERCIAL/Leads", "Consentimento", campo("contacts", "consent"), "contacts.consent + consented_at + opted_out_at"),
    ("COMERCIAL/Leads", "Status", campo("contacts", "status"), "contacts.status"),
    ("COMERCIAL/Leads", "Historico", rota("/activities"), "kind activities + GET /records/{kind}/{id}/overview"),
    ("COMERCIAL/Leads", "Deduplicacao", codigo("services.py", "find_contact_matches"), "find_contact_matches() por e-mail e telefone normalizados"),
    ("COMERCIAL/Leads", "Enriquecimento", False, "AUSENTE"),
    ("COMERCIAL/Leads", "Importacao CSV", rota("/contacts/import"), "POST /contacts/import com conferencia antes de gravar"),
    ("COMERCIAL/Leads", "Distribuicao automatica", codigo("services.py", "distribuir_lead"), "menor carga entre os papeis configurados, sem ponteiro guardado"),

    # ------------------------------------------------------- COMERCIAL > QUALIFICACAO
    ("COMERCIAL/Qualificacao", "Criterios configuraveis", campo("lead_rules", "criteria"), "kind lead_rules com dez operadores e rotulo por criterio"),
    ("COMERCIAL/Qualificacao", "Lead scoring", codigo("lead_scoring.py", "def avaliar"), "motor puro, soma limitada a 100 com a soma bruta visivel"),
    ("COMERCIAL/Qualificacao", "Classificacao por temperatura", codigo("lead_scoring.py", "def temperatura"), "quente, morno e frio por limiares configuraveis; nula sem regra ativa"),
    ("COMERCIAL/Qualificacao", "ICP", codigo("schemas.py", "icp"), "qualification.icp, pontuavel por criterio"),
    ("COMERCIAL/Qualificacao", "Fit da empresa", codigo("schemas.py", "fit:"), "qualification.fit em quatro niveis"),
    ("COMERCIAL/Qualificacao", "Intencao de compra", codigo("schemas.py", "intent:"), "qualification.intent"),
    ("COMERCIAL/Qualificacao", "Orcamento do lead", codigo("schemas.py", "budget:"), "qualification.budget: confirmado, estimado, ausente, desconhecido"),
    ("COMERCIAL/Qualificacao", "Prazo", codigo("schemas.py", "timeline:"), "qualification.timeline: imediato, trimestre, ano, sem prazo"),
    ("COMERCIAL/Qualificacao", "Comportamento", False, "AUSENTE"),
    ("COMERCIAL/Qualificacao", "Regras de qualificacao", campo("lead_rules", "criteria", "warm_at", "hot_at"), "kind lead_rules, um conjunto ativo por organizacao"),
    ("COMERCIAL/Qualificacao", "Passagem automatica para vendedor", codigo("services.py", "promote_lead"), "PARCIAL — promote_lead() cria oportunidade e tarefa, sem escolher vendedor"),
    ("COMERCIAL/Qualificacao", "Descarte com motivo", campo("contacts", "disqualified_reason"), "PARCIAL — o campo existe e o estagio descartado tambem; ainda nao e obrigatorio"),
    ("COMERCIAL/Qualificacao", "SLA de atendimento", codigo("lead_scoring.py", "def sla_estourado"), "prazo de primeira resposta; responder no prazo encerra para sempre"),
    ("COMERCIAL/Qualificacao", "Fila de leads sem acao", rota("/crm/leads"), "GET /crm/leads com sem_responsavel, sem_acao e sla_estourado"),
    ("COMERCIAL/Qualificacao", "Qualificacao explicavel e auditavel", rota("/leads/{record_id}/score"), "criterio a criterio, com o valor lido e o esperado"),

    # ------------------------------------------------------------ COMERCIAL > KANBAN
    ("COMERCIAL/Kanban", "Multiplos funis", campo("pipelines", "is_default", "stages"), "kind pipelines, varios por organizacao"),
    ("COMERCIAL/Kanban", "Etapas configuraveis", codigo("services.py", "guard_stage_removal"), "stages com chave, rotulo e desfecho, protegidas contra remocao ocupada"),
    ("COMERCIAL/Kanban", "Probabilidade", codigo("schemas.py", "probability"), "probabilidade por etapa, herdada pela oportunidade"),
    ("COMERCIAL/Kanban", "Duracao esperada", qualquer("expected_duration_hours"), "expected_duration_hours por etapa"),
    ("COMERCIAL/Kanban", "Motivo de perda", campo("deals", "lost_reason"), "obrigatorio ao entrar em etapa de perda; limpo ao reabrir"),
    ("COMERCIAL/Kanban", "Valor", campo("deals", "value_cents"), "deals.value_cents em centavos inteiros"),
    ("COMERCIAL/Kanban", "Previsao ponderada", qualquer("weighted_pipeline_cents"), "dashboard soma valor x probabilidade e divide uma vez so"),
    ("COMERCIAL/Kanban", "Responsavel", campo("deals", "owner_id"), "deals.owner_id"),
    ("COMERCIAL/Kanban", "Proxima acao", campo("deals", "next_action_at"), "deals.next_action_at"),
    ("COMERCIAL/Kanban", "Alertas de risco", rota("/crm/radar"), "GET /api/v1/crm/radar com quatro faixas e resumo"),
    ("COMERCIAL/Kanban", "Arrasto por mouse e toque", (ROOT / "apps/web/components/board-drag.ts").exists(), "board-drag.ts com eventos de ponteiro e alca de toque"),
    ("COMERCIAL/Kanban", "Historico de movimentacao", qualquer("deals.updated"), "PARCIAL — a trilha de auditoria registra, nao ha linha do tempo da etapa"),
    ("COMERCIAL/Kanban", "Filtros salvos", False, "AUSENTE — filtros vivem na URL, nao sao salvaveis"),
    ("COMERCIAL/Kanban", "Visao por equipe", False, "AUSENTE"),
    ("COMERCIAL/Kanban", "Visao por vendedor", campo("deals", "owner_id"), "PARCIAL — filtro por responsavel existe, visao dedicada nao"),

    # --------------------------------------------------------- COMERCIAL > PROPOSTAS
    ("COMERCIAL/Propostas", "Catalogo de produtos", campo("products", "price_cents", "sku"), "kind products"),
    ("COMERCIAL/Propostas", "Itens", codigo("sales_operations.py", "ProposalItem"), "itens com produto e quantidade"),
    ("COMERCIAL/Propostas", "Quantidades", codigo("sales_operations.py", "quantity"), "1..10.000 por item"),
    ("COMERCIAL/Propostas", "Descontos", codigo("sales_operations.py", "discount_cents"), "desconto em centavos no total"),
    ("COMERCIAL/Propostas", "Impostos internos", False, "AUSENTE"),
    ("COMERCIAL/Propostas", "Validade", False, "AUSENTE"),
    ("COMERCIAL/Propostas", "Versoes da proposta", False, "AUSENTE — ha versao otimista do registro, nao versoes da proposta"),
    ("COMERCIAL/Propostas", "Aprovacao", campo("approvals", "gate", "status"), "PARCIAL — kind approvals existe, sem vinculo com proposta"),
    ("COMERCIAL/Propostas", "Aprovacao em multiplos niveis", False, "AUSENTE — a decisao e de um nivel so"),
    ("COMERCIAL/Propostas", "Geracao de PDF", False, "AUSENTE"),
    ("COMERCIAL/Propostas", "Envio condicionado a integracao", qualquer("external_sends_enabled"), "trava external_sends_enabled desligada; envio recusa com motivo"),
    ("COMERCIAL/Propostas", "Aceite", codigo("sales_operations.py", "accepted"), "status accepted com transicao explicita"),
    ("COMERCIAL/Propostas", "Recusa", codigo("sales_operations.py", "rejected"), "status rejected"),
    ("COMERCIAL/Propostas", "Comentarios", False, "AUSENTE"),
    ("COMERCIAL/Propostas", "Assinatura eletronica preparada", False, "AUSENTE"),
    ("COMERCIAL/Propostas", "Total reproduzivel", codigo("sales_operations.py", "unit_price_cents"), "preco congelado do catalogo no instante da criacao"),
    ("COMERCIAL/Propostas", "Vinculo com oportunidade", codigo("sales_operations.py", "deal_id"), "proposta exige deal_id"),
    ("COMERCIAL/Propostas", "Vinculo com cliente", False, "PARCIAL — chega ao contato pela oportunidade, nao direto"),
    ("COMERCIAL/Propostas", "Geracao assistida por IA", False, "AUSENTE"),

    # --------------------------------------------------------- COMERCIAL > CONTRATOS
    ("COMERCIAL/Contratos", "Modelos contratuais", False, "AUSENTE"),
    ("COMERCIAL/Contratos", "Variaveis", False, "AUSENTE"),
    ("COMERCIAL/Contratos", "Versoes", False, "AUSENTE"),
    ("COMERCIAL/Contratos", "Status", False, "AUSENTE"),
    ("COMERCIAL/Contratos", "Vigencia", False, "AUSENTE"),
    ("COMERCIAL/Contratos", "Renovacao", False, "AUSENTE"),
    ("COMERCIAL/Contratos", "Responsaveis", False, "AUSENTE"),
    ("COMERCIAL/Contratos", "Aprovacoes", False, "AUSENTE"),
    ("COMERCIAL/Contratos", "Anexos", False, "AUSENTE — nao ha armazenamento de arquivo em nenhum dominio"),
    ("COMERCIAL/Contratos", "Assinatura externa preparada", False, "AUSENTE"),
    ("COMERCIAL/Contratos", "Alertas de vencimento", False, "AUSENTE"),
    ("COMERCIAL/Contratos", "Vinculo com proposta", False, "AUSENTE"),
    ("COMERCIAL/Contratos", "Vinculo com cliente", False, "AUSENTE"),
    ("COMERCIAL/Contratos", "Auditoria completa", qualquer("audit_event"), "PARCIAL — a trilha cobre tudo que existe; contrato nao existe"),

    # ------------------------------------------------- COMERCIAL > PRODUTOS E SERVICOS
    ("COMERCIAL/Produtos", "Catalogo", campo("products", "name", "price_cents"), "kind products"),
    ("COMERCIAL/Produtos", "Categorias", campo("products", "category"), "products.category como texto livre"),
    ("COMERCIAL/Produtos", "Preco", campo("products", "price_cents"), "products.price_cents"),
    ("COMERCIAL/Produtos", "Custo", False, "AUSENTE"),
    ("COMERCIAL/Produtos", "Margem", False, "AUSENTE — sem custo nao ha margem"),
    ("COMERCIAL/Produtos", "Recorrencia", False, "AUSENTE"),
    ("COMERCIAL/Produtos", "Unidade", False, "AUSENTE"),
    ("COMERCIAL/Produtos", "Disponibilidade", campo("products", "status"), "PARCIAL — status ativo/inativo, sem estoque nem disponibilidade"),
    ("COMERCIAL/Produtos", "Pacote", False, "AUSENTE"),
    ("COMERCIAL/Produtos", "Versao do produto", False, "AUSENTE"),
    ("COMERCIAL/Produtos", "Ativo/inativo", campo("products", "status"), "products.status"),
    ("COMERCIAL/Produtos", "Vinculo com propostas", codigo("sales_operations.py", "product_id"), "itens da proposta referenciam o produto"),
    ("COMERCIAL/Produtos", "Vinculo com contratos", False, "AUSENTE"),
    ("COMERCIAL/Produtos", "Vinculo com projetos", False, "AUSENTE"),

    # ---------------------------------------------------------- COMERCIAL > CLIENTES
    ("COMERCIAL/Clientes", "Cliente como entidade apos conversao", False, "AUSENTE — cliente e contacts.status=customer, nao entidade propria"),
    ("COMERCIAL/Clientes", "Status do relacionamento", campo("contacts", "status"), "PARCIAL — status do contato, nao do relacionamento"),
    ("COMERCIAL/Clientes", "Valor total do cliente", False, "AUSENTE"),
    ("COMERCIAL/Clientes", "Contratos do cliente", False, "AUSENTE"),
    ("COMERCIAL/Clientes", "Projetos do cliente", campo("projects", "company_id"), "PARCIAL — projeto liga a empresa, e a visao 360 nao mostra"),
    ("COMERCIAL/Clientes", "Contatos do cliente", campo("contacts", "company_id"), "contacts.company_id + overview de companies"),
    ("COMERCIAL/Clientes", "Historico", rota("/overview"), "GET /records/{kind}/{id}/overview"),
    ("COMERCIAL/Clientes", "Satisfacao", False, "AUSENTE"),
    ("COMERCIAL/Clientes", "Renovacao", False, "AUSENTE"),
    ("COMERCIAL/Clientes", "Expansao", False, "AUSENTE"),
    ("COMERCIAL/Clientes", "Risco de churn", False, "AUSENTE"),
    ("COMERCIAL/Clientes", "Oportunidades abertas", codigo("record_views.py", "deals"), "overview lista oportunidades do contato e da empresa"),
    ("COMERCIAL/Clientes", "Financeiro do cliente", campo("invoices", "company_id"), "PARCIAL — faturas ligam a empresa; nao ha consolidacao"),
    ("COMERCIAL/Clientes", "Comunicacao", campo("conversations", "contact_id"), "PARCIAL — conversas ligam ao contato, sem inbox unificada"),
    ("COMERCIAL/Clientes", "Documentos", False, "AUSENTE"),

    # ------------------------------------------------- CLIENTES > DADOS CADASTRAIS
    ("CLIENTES/Cadastro", "Pessoa", campo("contacts", "name"), "kind contacts"),
    ("CLIENTES/Cadastro", "Empresa", campo("companies", "name", "document"), "kind companies com documento"),
    ("CLIENTES/Cadastro", "Contatos vinculados", campo("contacts", "company_id"), "contacts.company_id"),
    ("CLIENTES/Cadastro", "Documentos anexos", False, "AUSENTE"),
    ("CLIENTES/Cadastro", "Enderecos", False, "AUSENTE — nenhum dominio guarda endereco"),
    ("CLIENTES/Cadastro", "Canais", campo("conversations", "channel"), "PARCIAL — canal vive na conversa, nao no cadastro"),
    ("CLIENTES/Cadastro", "Tags", campo("contacts", "tags"), "contacts.tags como lista livre, sem catalogo nem cor"),
    ("CLIENTES/Cadastro", "Consentimentos", campo("contacts", "consent"), "consent + consented_at + opted_out_at"),
    ("CLIENTES/Cadastro", "Origem", campo("contacts", "source"), "contacts.source"),
    ("CLIENTES/Cadastro", "Responsavel", campo("contacts", "owner_id"), "contacts.owner_id"),
    ("CLIENTES/Cadastro", "Campos personalizados", False, "AUSENTE — schema e StrictModel com extra=forbid"),
    ("CLIENTES/Cadastro", "Historico", rota("/overview"), "overview com atividades e auditoria do registro"),
    ("CLIENTES/Cadastro", "Notas", campo("contacts", "notes"), "contacts.notes"),
    ("CLIENTES/Cadastro", "Atividades", rota("/activities"), "POST /records/{kind}/{id}/activities"),
    ("CLIENTES/Cadastro", "Oportunidades na ficha", codigo("record_views.py", "deals"), "overview"),
    ("CLIENTES/Cadastro", "Contratos na ficha", False, "AUSENTE"),
    ("CLIENTES/Cadastro", "Projetos na ficha", False, "AUSENTE — overview nao traz projetos"),
    ("CLIENTES/Cadastro", "Financeiro na ficha", False, "AUSENTE"),
    ("CLIENTES/Cadastro", "Conversas na ficha", codigo("record_views.py", "conversations"), "overview"),
    ("CLIENTES/Cadastro", "Campo personalizado: tipo", False, "AUSENTE"),
    ("CLIENTES/Cadastro", "Campo personalizado: obrigatorio", False, "AUSENTE"),
    ("CLIENTES/Cadastro", "Campo personalizado: opcoes", False, "AUSENTE"),
    ("CLIENTES/Cadastro", "Campo personalizado: validacao", False, "AUSENTE"),
    ("CLIENTES/Cadastro", "Campo personalizado: visibilidade", False, "AUSENTE"),
    ("CLIENTES/Cadastro", "Campo personalizado: ordem", False, "AUSENTE"),
    ("CLIENTES/Cadastro", "Campo personalizado: historico", False, "AUSENTE"),
    ("CLIENTES/Cadastro", "Campo personalizado: permissao", False, "AUSENTE"),

    # ------------------------------------------------------------ CLIENTES > PROJETOS
    ("CLIENTES/Projetos", "Projetos", campo("projects", "name", "status"), "kind projects"),
    ("CLIENTES/Projetos", "Fases", False, "AUSENTE"),
    ("CLIENTES/Projetos", "Tarefas do projeto", campo("tasks", "project_id"), "tasks.project_id"),
    ("CLIENTES/Projetos", "Responsaveis", campo("projects", "owner_id"), "projects.owner_id"),
    ("CLIENTES/Projetos", "Prazos", campo("projects", "due_date"), "projects.due_date"),
    ("CLIENTES/Projetos", "Marcos", False, "AUSENTE"),
    ("CLIENTES/Projetos", "Orcamento", campo("projects", "budget_cents"), "projects.budget_cents"),
    ("CLIENTES/Projetos", "Horas", False, "AUSENTE — nao ha apontamento de horas"),
    ("CLIENTES/Projetos", "Entregaveis", False, "AUSENTE"),
    ("CLIENTES/Projetos", "Arquivos", False, "AUSENTE"),
    ("CLIENTES/Projetos", "Comentarios", rota("/activities"), "PARCIAL — activities cobrem contato, empresa e negocio, nao projeto"),
    ("CLIENTES/Projetos", "Aprovacoes", campo("approvals", "gate"), "PARCIAL — kind approvals sem vinculo com projeto"),
    ("CLIENTES/Projetos", "Status", campo("projects", "status"), "projects.status"),
    ("CLIENTES/Projetos", "Riscos", False, "AUSENTE"),
    ("CLIENTES/Projetos", "Margem", False, "AUSENTE"),
    ("CLIENTES/Projetos", "Vinculo com contrato", False, "AUSENTE"),
    ("CLIENTES/Projetos", "Vinculo com cliente", campo("projects", "company_id"), "projects.company_id"),

    # --------------------------------------------------------- CLIENTES > FINANCEIRO
    ("CLIENTES/Financeiro", "Lancamentos", campo("invoices", "amount_cents"), "PARCIAL — kind invoices e um titulo, nao um lancamento"),
    ("CLIENTES/Financeiro", "Contas a receber", campo("invoices", "due_date", "status"), "PARCIAL — faturas com vencimento e status, sem visao de carteira"),
    ("CLIENTES/Financeiro", "Contas a pagar", False, "AUSENTE"),
    ("CLIENTES/Financeiro", "Parcelas", False, "AUSENTE"),
    ("CLIENTES/Financeiro", "Vencimentos", campo("invoices", "due_date"), "invoices.due_date"),
    ("CLIENTES/Financeiro", "Status", campo("invoices", "status"), "invoices.status"),
    ("CLIENTES/Financeiro", "Centro de custo", False, "AUSENTE"),
    ("CLIENTES/Financeiro", "Receita recorrente", False, "AUSENTE"),
    ("CLIENTES/Financeiro", "Margem", False, "AUSENTE"),
    ("CLIENTES/Financeiro", "Previsao", qualquer("weighted_pipeline_cents"), "PARCIAL — previsao e do funil comercial, nao do caixa"),
    ("CLIENTES/Financeiro", "Inadimplencia", False, "AUSENTE"),
    ("CLIENTES/Financeiro", "Aprovacao financeira", False, "AUSENTE"),
    ("CLIENTES/Financeiro", "Vinculo com cliente", campo("invoices", "company_id", "contact_id"), "invoices liga empresa e contato"),
    ("CLIENTES/Financeiro", "Vinculo com projeto", False, "AUSENTE"),
    ("CLIENTES/Financeiro", "Vinculo com contrato", False, "AUSENTE"),

    # ------------------------------------------------------- PARIDADE > GESTAO DE VENDAS
    ("PARIDADE/Vendas", "Leads", campo("contacts", "lead_stage"), "ciclo de vida proprio e fila dedicada sobre o kind contacts"),
    ("PARIDADE/Vendas", "Contas", campo("companies", "name"), "kind companies"),
    ("PARIDADE/Vendas", "Contatos", campo("contacts", "name"), "kind contacts"),
    ("PARIDADE/Vendas", "Oportunidades", campo("deals", "value_cents", "stage"), "kind deals"),
    ("PARIDADE/Vendas", "Pipeline", campo("pipelines", "stages"), "kind pipelines configuravel"),
    ("PARIDADE/Vendas", "Forecast", qualquer("weighted_pipeline_cents"), "PARCIAL — previsao ponderada pela etapa, sem cenarios nem historico"),
    ("PARIDADE/Vendas", "Atividades", rota("/activities"), "kind activities"),
    ("PARIDADE/Vendas", "Cadencias", False, "AUSENTE"),
    ("PARIDADE/Vendas", "Proxima melhor acao", rota("/crm/radar"), "PARCIAL — o radar aponta o que esta parado, nao recomenda a acao"),
    ("PARIDADE/Vendas", "Metas", rota("/sales/goals"), "metas por vendedor e periodo"),
    ("PARIDADE/Vendas", "Territorios", False, "AUSENTE"),
    ("PARIDADE/Vendas", "Distribuicao automatica", codigo("services.py", "distribuir_lead"), "por menor carga, reproduzivel"),
    ("PARIDADE/Vendas", "Aprovacao", campo("approvals", "status"), "PARCIAL — decisao de um nivel, sem fluxo"),
    ("PARIDADE/Vendas", "Cotacao", rota("/sales/proposals"), "propostas com preco congelado"),
    ("PARIDADE/Vendas", "Contratos", False, "AUSENTE"),

    # --------------------------------------------------------- PARIDADE > MARKETING
    ("PARIDADE/Marketing", "Formularios", False, "AUSENTE — nao ha construtor; o site tem formulario fixo"),
    ("PARIDADE/Marketing", "Landing pages", False, "PARCIAL — 19 landing pages existem no site, nenhuma editavel no CRM"),
    ("PARIDADE/Marketing", "Campanhas", campo("campaigns", "channel", "status"), "PARCIAL — kind campaigns e cadastro, nao executa"),
    ("PARIDADE/Marketing", "UTMs", campo("contacts", "utm_source", "utm_campaign"), "PARCIAL — campos consultaveis e filtraveis; sem relatorio de conversao por canal"),
    ("PARIDADE/Marketing", "Origem", campo("contacts", "source"), "contacts.source"),
    ("PARIDADE/Marketing", "Segmentacao", campo("contacts", "tags"), "PARCIAL — etiquetas e filtros, sem publico salvo"),
    ("PARIDADE/Marketing", "Automacao", campo("automations", "nodes", "edges"), "PARCIAL — fluxo desenhado e simulado, nunca executado"),
    ("PARIDADE/Marketing", "Nutricao", False, "AUSENTE"),
    ("PARIDADE/Marketing", "Lead scoring", codigo("lead_scoring.py", "def avaliar"), "por regra configuravel e explicavel"),
    ("PARIDADE/Marketing", "Atribuicao", codigo("services.py", "attribution"), "PARCIAL — primeiro toque guardado, sem relatorio de atribuicao"),
    ("PARIDADE/Marketing", "Conversao por canal", False, "AUSENTE"),
    ("PARIDADE/Marketing", "ROI", False, "AUSENTE"),

    # -------------------------------------------------------- PARIDADE > ATENDIMENTO
    ("PARIDADE/Atendimento", "Inbox unificada", tela("conversas"), "PARCIAL — caixa por contato e canal, sem unificacao real de canais"),
    ("PARIDADE/Atendimento", "Historico", campo("conversations", "last_message"), "conversas com ultima mensagem e ultima entrada"),
    ("PARIDADE/Atendimento", "SLA", codigo("lead_scoring.py", "def prazo_sla"), "PARCIAL — SLA de primeira resposta ao lead; conversa e ticket nao tem"),
    ("PARIDADE/Atendimento", "Responsaveis", campo("conversations", "owner_id"), "conversations.owner_id"),
    ("PARIDADE/Atendimento", "Handoff", qualquer("HUMAN_AGENT"), "PARCIAL — a marca HUMAN_AGENT existe na elegibilidade, sem fluxo de transferencia"),
    ("PARIDADE/Atendimento", "Classificacao", False, "AUSENTE"),
    ("PARIDADE/Atendimento", "Templates", qualquer("whatsapp_template_required"), "PARCIAL — a regra exige template aprovado; nao ha cadastro de templates"),
    ("PARIDADE/Atendimento", "Base de conhecimento", campo("knowledge", "content"), "kind knowledge + grafo do sistema"),
    ("PARIDADE/Atendimento", "Satisfacao", False, "AUSENTE"),
    ("PARIDADE/Atendimento", "Tickets preparados", False, "AUSENTE"),

    # ------------------------------------------------------- PARIDADE > PRODUTIVIDADE
    ("PARIDADE/Produtividade", "Agenda", False, "AUSENTE"),
    ("PARIDADE/Produtividade", "Google Calendar", False, "AUSENTE"),
    ("PARIDADE/Produtividade", "Agendamento publico", False, "AUSENTE"),
    ("PARIDADE/Produtividade", "Lembretes", rota("/notifications"), "PARCIAL — avisos derivados de tarefa vencida e risco, sem lembrete agendado"),
    ("PARIDADE/Produtividade", "E-mail sincronizado", False, "AUSENTE"),
    ("PARIDADE/Produtividade", "Tarefas", campo("tasks", "due_date", "priority"), "kind tasks"),
    ("PARIDADE/Produtividade", "Filas de trabalho", rota("/work-queue"), "GET /work-queue com filtros no servidor e estado na URL"),
    ("PARIDADE/Produtividade", "Notificacoes", rota("/notifications"), "derivadas dos registros, sem fila armazenada"),
    ("PARIDADE/Produtividade", "Extensao de navegador", False, "AUSENTE"),
    ("PARIDADE/Produtividade", "PWA ou aplicativo movel", False, "PARCIAL — as telas respondem em celular, nao ha manifesto nem instalacao"),

    # --------------------------------------------------------- PARIDADE > INTELIGENCIA
    ("PARIDADE/Inteligencia", "Copiloto", False, "AUSENTE"),
    ("PARIDADE/Inteligencia", "Resumo de conversa", False, "AUSENTE"),
    ("PARIDADE/Inteligencia", "Classificacao por IA", False, "AUSENTE"),
    ("PARIDADE/Inteligencia", "Enriquecimento", False, "AUSENTE"),
    ("PARIDADE/Inteligencia", "Lead scoring por IA", False, "AUSENTE"),
    ("PARIDADE/Inteligencia", "Previsao", qualquer("weighted_pipeline_cents"), "PARCIAL — aritmetica de etapa, nao modelo"),
    ("PARIDADE/Inteligencia", "Recomendacao", False, "AUSENTE"),
    ("PARIDADE/Inteligencia", "Geracao de proposta", False, "AUSENTE"),
    ("PARIDADE/Inteligencia", "Analise de risco", codigo("services.py", "classify_risk"), "PARCIAL — risco comercial por tempo parado, regra e nao modelo"),
    ("PARIDADE/Inteligencia", "Analise de churn", False, "AUSENTE"),
    ("PARIDADE/Inteligencia", "Agentes com aprovacao e limites", campo("agents", "autonomy", "budget_cents"), "PARCIAL — cadastro com autonomia e orcamento; sem executor"),

    # -------------------------------------------------------------- CANAIS > INSTAGRAM
    ("CANAIS/Instagram", "OAuth", False, "PARCIAL — a conta e conectada por token colado, nao por fluxo OAuth"),
    ("CANAIS/Instagram", "Contas por tenant", tabela("instagram_accounts"), "tabela instagram_accounts com id unico global"),
    ("CANAIS/Instagram", "Tokens protegidos", tabela("instagram_credentials"), "AES-256-GCM, chave fora do banco, RLS forcada"),
    ("CANAIS/Instagram", "Webhook", rota("/webhooks/instagram"), "HMAC, idempotencia por entrega, outbox antes do processamento"),
    ("CANAIS/Instagram", "Mensagens", False, "AUSENTE — o evento entra na outbox e nao vira conversa"),
    ("CANAIS/Instagram", "Comentarios", False, "AUSENTE"),
    ("CANAIS/Instagram", "Mencoes", False, "AUSENTE"),
    ("CANAIS/Instagram", "Reacoes", False, "AUSENTE"),
    ("CANAIS/Instagram", "Private Reply", qualquer("comment_already_replied"), "PARCIAL — a regra de resposta unica existe, a tabela de unicidade nao"),
    ("CANAIS/Instagram", "Conversas", False, "AUSENTE"),
    ("CANAIS/Instagram", "Gatilhos", False, "AUSENTE"),
    ("CANAIS/Instagram", "Sequencias", False, "AUSENTE"),
    ("CANAIS/Instagram", "Janela de 24 horas", qualquer("STANDARD_WINDOW"), "compliance.evaluate()"),
    ("CANAIS/Instagram", "HUMAN_AGENT quando autorizado", qualquer("HUMAN_AGENT_WINDOW"), "sete dias, e automacao nunca pode usar"),
    ("CANAIS/Instagram", "Cooldown", qualquer("trigger_cooldown"), "PARCIAL — a decisao existe, nada persiste o intervalo"),
    ("CANAIS/Instagram", "Opt-out", qualquer("OPT_OUT_KEYWORDS"), "palavra de saida encerra e vence qualquer outra regra"),
    ("CANAIS/Instagram", "Blocklist", qualquer("blocked_terms"), "PARCIAL — lista global da instalacao, nao por organizacao"),
    ("CANAIS/Instagram", "Auditoria", qualquer("instagram.account.connected"), "conexao, rotacao, desconexao e recusa auditadas"),
    ("CANAIS/Instagram", "Rate limit", tabela("rate_limits"), "PARCIAL — limite existe no login, nao no canal"),
    ("CANAIS/Instagram", "Publicacao", False, "AUSENTE"),
    ("CANAIS/Instagram", "Insights", False, "AUSENTE"),

    # --------------------------------------------------------------- CANAIS > WHATSAPP
    ("CANAIS/WhatsApp", "Mensagens recebidas", False, "AUSENTE"),
    ("CANAIS/WhatsApp", "Mensagens enviadas", False, "AUSENTE — o envio recusa com motivo em vez de simular"),
    ("CANAIS/WhatsApp", "Templates", qualquer("whatsapp_template_not_approved"), "PARCIAL — a regra conhece template aprovado; nao ha cadastro"),
    ("CANAIS/WhatsApp", "Consentimento", campo("contacts", "consent"), "verificado antes de qualquer envio automatizado"),
    ("CANAIS/WhatsApp", "Janela de 24 horas", qualquer("STANDARD_WINDOW"), "compliance.evaluate()"),
    ("CANAIS/WhatsApp", "Opt-out", qualquer("with_opt_out"), "rodape obrigatorio contado dentro do limite"),
    ("CANAIS/WhatsApp", "Campanhas", campo("campaigns", "channel"), "PARCIAL — cadastro de campanha, sem destinatarios nem execucao"),
    ("CANAIS/WhatsApp", "Webhook", False, "AUSENTE"),
    ("CANAIS/WhatsApp", "Midia", False, "AUSENTE"),
    ("CANAIS/WhatsApp", "Historico", campo("conversations", "channel"), "PARCIAL — o canal whatsapp existe na conversa, sem mensagem real"),
    ("CANAIS/WhatsApp", "Rate limit", False, "AUSENTE"),

    # ----------------------------------------------------------------- CANAIS > E-MAIL
    ("CANAIS/Email", "Conexao por organizacao", False, "AUSENTE"),
    ("CANAIS/Email", "Caixa de entrada", False, "AUSENTE"),
    ("CANAIS/Email", "Envio", False, "AUSENTE"),
    ("CANAIS/Email", "Templates", False, "AUSENTE"),
    ("CANAIS/Email", "Rastreamento", False, "AUSENTE"),
    ("CANAIS/Email", "Threads", False, "AUSENTE"),
    ("CANAIS/Email", "Assinatura", False, "AUSENTE"),
    ("CANAIS/Email", "Opt-out", qualquer("OPT_OUT_FOOTER"), "PARCIAL — a regra e do motor de elegibilidade, sem canal de e-mail"),
    ("CANAIS/Email", "SPF/DKIM/DMARC documentados", False, "AUSENTE"),
    ("CANAIS/Email", "Cadencias", False, "AUSENTE"),
    ("CANAIS/Email", "Anexos", False, "AUSENTE"),
    ("CANAIS/Email", "Auditoria", qualquer("audit_event"), "PARCIAL — a trilha cobre o que existe; e-mail nao existe"),

    # ------------------------------------------------------------------------- IA
    ("IA/Agente", "Persona", campo("agents", "role", "description"), "PARCIAL — papel e descricao, sem instrucoes de sistema"),
    ("IA/Agente", "Objetivo", campo("agents", "description"), "PARCIAL — texto livre"),
    ("IA/Agente", "Instrucoes", False, "AUSENTE"),
    ("IA/Agente", "Base de conhecimento", campo("knowledge", "content"), "PARCIAL — kind knowledge existe, sem vinculo com agente"),
    ("IA/Agente", "Escopo de dados", False, "AUSENTE"),
    ("IA/Agente", "Modelo", False, "AUSENTE"),
    ("IA/Agente", "Orcamento", campo("agents", "budget_cents", "spent_cents"), "orcamento e gasto declarados em centavos"),
    ("IA/Agente", "Limite de tokens", False, "AUSENTE"),
    ("IA/Agente", "Autonomia", campo("agents", "autonomy"), "agents.autonomy"),
    ("IA/Agente", "Ferramentas permitidas", False, "AUSENTE"),
    ("IA/Agente", "Acoes proibidas", False, "AUSENTE"),
    ("IA/Agente", "Aprovacao necessaria", campo("approvals", "gate", "intent"), "PARCIAL — a aprovacao guarda a intencao represada e nao executa ao decidir"),
    ("IA/Agente", "Logs", qualquer("audit_event"), "PARCIAL — auditoria do cadastro, nao de execucao"),
    ("IA/Agente", "Custo", campo("agents", "spent_cents"), "PARCIAL — campo existe, nada o incrementa"),
    ("IA/Agente", "Avaliacao", False, "AUSENTE"),
    ("IA/Agente", "Versao do agente", False, "AUSENTE"),
    ("IA/Agente", "Rollback do agente", False, "AUSENTE"),
    ("IA/Modo", "Somente sugestao", False, "AUSENTE"),
    ("IA/Modo", "Copiloto", False, "AUSENTE"),
    ("IA/Modo", "Execucao com aprovacao", False, "AUSENTE"),
    ("IA/Modo", "Autonomo limitado", False, "AUSENTE"),
    ("IA/Guardrail", "Guardrails", False, "AUSENTE"),
    ("IA/Guardrail", "Orcamento reservado", False, "AUSENTE"),
    ("IA/Guardrail", "Limite de acoes", False, "AUSENTE"),
    ("IA/Guardrail", "Auditoria de execucao", False, "AUSENTE"),
    ("IA/Guardrail", "Interrupcao manual", False, "AUSENTE"),
    ("IA/Guardrail", "Avaliacao de risco", False, "AUSENTE"),
    ("IA/Guardrail", "Confirmacao de integracao externa", qualquer("external_sends_enabled"), "PARCIAL — a trava existe; nao ha execucao de agente para travar"),

    # ------------------------------------------------------- SEGURANCA E COMPLIANCE
    ("SEGURANCA", "RLS", codigo("migrate.py", "FORCE ROW LEVEL SECURITY"), "cinco tabelas com politica forcada, valida ate para o dono"),
    ("SEGURANCA", "Grants minimos", codigo("migrate.py", "NOBYPASSRLS"), "fattech_app sem superusuario, sem dono de tabela, sem bypass"),
    ("SEGURANCA", "RBAC", codigo("permissions.py", "ADMIN_ROLES"), "cinco papeis e regra de que ninguem promove ao proprio nivel"),
    ("SEGURANCA", "MFA", False, "AUSENTE"),
    ("SEGURANCA", "Recuperacao de conta", rota("/team/{user_id}/password"), "PARCIAL — administrador redefine senha; nao ha autoatendimento"),
    ("SEGURANCA", "Criptografia de tokens", tabela("instagram_credentials"), "AES-256-GCM com chave fora do banco"),
    ("SEGURANCA", "Rotacao de secrets", rota("/accounts/{account_id}/token"), "PARCIAL — rotacao do token do Instagram; sem rotacao dos segredos da instalacao"),
    ("SEGURANCA", "Rate limiting", tabela("rate_limits"), "PARCIAL — tentativas de login por e-mail e por IP; nao ha limite por rota"),
    ("SEGURANCA", "Auditoria", tabela("audit_log"), "append-only: a aplicacao nao tem permissao de alterar nem apagar"),
    ("SEGURANCA", "LGPD", campo("contacts", "consent"), "PARCIAL — consentimento, opt-out e trilha; sem retencao nem exclusao"),
    ("SEGURANCA", "Exportacao de dados", False, "AUSENTE — nao ha exportacao por titular"),
    ("SEGURANCA", "Exclusao de dados", qualquer("deleted"), "PARCIAL — exclusao logica do registro, sem apagamento definitivo por titular"),
    ("SEGURANCA", "Retencao", False, "AUSENTE"),
    ("SEGURANCA", "Consentimento", campo("contacts", "consent"), "verificado antes de envio automatizado"),
    ("SEGURANCA", "Opt-out", qualquer("is_opt_out_keyword"), "palavra de saida vence qualquer outra regra"),
    ("SEGURANCA", "Blocklist", qualquer("blocked_terms"), "PARCIAL — global, nao por organizacao"),
    ("SEGURANCA", "Paginas legais", (ROOT / "apps/web/app/(site)/privacidade").exists(), "pagina de privacidade publicada"),
    ("SEGURANCA", "Logs sem segredos", codigo("main.py", "type(exc).__name__"), "falha de banco registra o tipo e o rastro, nunca o conteudo"),
    ("SEGURANCA", "Backup", (ROOT / "infra/backup.sh").exists(), "infra/backup.sh com servico e temporizador"),
    ("SEGURANCA", "Restauracao", (ROOT / "infra/verify-backup.sh").exists(), "PARCIAL — a verificacao do backup existe; a restauracao nao e ensaiada"),
    ("SEGURANCA", "Rollback", (ROOT / "infra/install-release.sh").exists(), "instalacao com inventario, hash e poda; rollback por configuracao ausente"),
    ("PIPELINE", "Autorizacao", qualquer("require_auth"), "sessao ou chave de API com escopo"),
    ("PIPELINE", "Consentimento", qualquer("no_consent"), "compliance.evaluate() checa antes de tudo"),
    ("PIPELINE", "Elegibilidade", qualquer("def evaluate"), "ordem de decisao explicita e testada"),
    ("PIPELINE", "Blocklist", qualquer("blocked_content"), "detecta termo mesmo com caractere invisivel"),
    ("PIPELINE", "Cooldown", qualquer("trigger_cooldown"), "PARCIAL — decide, nao persiste"),
    ("PIPELINE", "Rate limit", qualquer("def rate_limit"), "PARCIAL — aplicado no login, nao no envio"),
    ("PIPELINE", "Idempotencia", tabela("idempotency_keys"), "chave por operacao, com conflito em conteudo diferente"),
    ("PIPELINE", "Outbox", tabela("event_outbox"), "gravada na mesma transacao do dado que a originou"),
    ("PIPELINE", "Worker", codigo("worker.py", "dead_letter"), "tentativa, espera progressiva, limite e carta morta"),
    ("PIPELINE", "Confirmacao externa", False, "AUSENTE — nada e entregue a um provedor final ainda"),
    ("PIPELINE", "Auditoria", tabela("audit_log"), "toda acao relevante com autor, recurso e instante"),
]


def situacao(linha):
    _, _, sonda, onde = linha
    if onde.startswith("AUSENTE"):
        return "AUSENTE"
    if onde.startswith("PARCIAL"):
        return "PARCIAL"
    return "TEM" if sonda else "AUSENTE"


def main() -> int:
    filtro = ""
    if "--secao" in sys.argv:
        filtro = sys.argv[sys.argv.index("--secao") + 1].upper()
    linhas = [c for c in CAPACIDADES if not filtro or c[0].upper().startswith(filtro)]

    print(f"ORDEM PRINCIPAL vs FAT Tech CRM Pro — {len(CAPACIDADES)} capacidades medidas")
    print(f"Denominador: {len(RESOURCES)} dominios, {len(TABELAS)} tabelas, {len(ROTAS)} rotas, {len(TELAS)} telas\n")
    print(f"{'SECAO':26} {'CAPACIDADE':38} {'SITUACAO':9} ONDE VIVE")
    print("-" * 150)
    secao_atual = None
    for secao, nome, sonda, onde in linhas:
        if secao != secao_atual:
            print("-" * 150)
            secao_atual = secao
        print(f"{secao:26} {nome:38} {situacao((secao, nome, sonda, onde)):9} {onde[:60]}")
    print("-" * 150)

    grupos = {}
    for linha in linhas:
        grupo = linha[0].split("/")[0]
        marca = situacao(linha)
        grupos.setdefault(grupo, {"TEM": 0, "PARCIAL": 0, "AUSENTE": 0})[marca] += 1
    print(f"\n{'GRUPO':18} {'TEM':>5} {'PARCIAL':>8} {'AUSENTE':>8} {'TOTAL':>7}  PRONTIDAO")
    for grupo, contagem in grupos.items():
        total = sum(contagem.values())
        # Parcial vale metade: uma regra que decide sem persistir nao entrega meia funcionalidade por acaso.
        pronto = (contagem["TEM"] + contagem["PARCIAL"] * 0.5) / total * 100
        print(f"{grupo:18} {contagem['TEM']:>5} {contagem['PARCIAL']:>8} {contagem['AUSENTE']:>8} {total:>7}  {pronto:>5.0f}%")

    tem = sum(1 for c in linhas if situacao(c) == "TEM")
    parcial = sum(1 for c in linhas if situacao(c) == "PARCIAL")
    ausente = sum(1 for c in linhas if situacao(c) == "AUSENTE")
    total = len(linhas)
    print("-" * 66)
    print(f"{'TOTAL':18} {tem:>5} {parcial:>8} {ausente:>8} {total:>7}  "
          f"{(tem + parcial * 0.5) / total * 100:>5.0f}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
