# Prontidão comercial dos produtos FAT Tech

Avaliação em 20/09/2026. Fontes: site público, contratos do código local, testes executados e consulta HTTP de saúde/OpenAPI da instalação publicada. Esta avaliação não é uma homologação completa de produção e não pressupõe que um pacote já esteja cadastrado no banco real.

## Parecer

O CRM oferece a base para venda consultiva e controle interno. Ainda não oferece o ciclo completo de comercialização modular, cobrança recorrente, ativação do cliente e operação autônoma do SYNAPSE. O cadastro de uma recorrência em um produto não cria uma assinatura, e preparar o SYNAPSE no workspace comercial da FAT Tech não provisiona uma organização para o comprador.

A API publicada em `https://fattechcrmpro.64.181.178.125.nip.io/api/health` respondeu HTTP 200, `status=ok`, `version=0.5.1`. A OpenAPI pública respondeu HTTP 200 e não apresentou rotas `/synapse`. As novas rotas desta rodada são locais; não foram implantadas na Oracle nesta avaliação.

## Oferta pública e enquadramento

Valores observados na [home](https://fattech.com.br/): Start R$357/mês; Tração R$717/mês; SYNAPSE R$3.260 de implantação e R$497/mês; Board BPO R$2.997/mês mais implantação SYNAPSE. Existem também serviços avulsos. A [página do CRM](https://fattech.com.br/crm) apresenta operação de IA, WhatsApp, agenda e cobranças; essa apresentação precisa corresponder a capacidades homologadas.

SYNAPSE deve ser o produto principal de software e automação. Start e Tração são ofertas de serviços com composição própria. Board BPO deve ser modelado como uma oferta de operação assistida que inclui SYNAPSE e serviços adicionais: ter mensalidade maior não precisa significar um segundo produto principal de software.

| Oferta | Venda com atendimento humano | Operação atualmente demonstrável no CRM | Lacuna para oferta completa |
|---|---|---|---|
| Start | Base de catálogo, oportunidade, proposta e contrato permite registrar uma negociação | Projetos e tarefas podem organizar a entrega manual | Checklist específico, entregáveis, acessos de ativos e aceite do cliente |
| Tração | Mesma base permite negociação consultiva | Cadastro de campanhas e atribuição UTM | Gestão real de mídia, importação de custos, separação de verba de anúncios e honorários, rotina de relatório |
| SYNAPSE | Catálogo implantação/licença e funil estão sendo integrados localmente | Leads, oportunidade, tarefa com prazo, consulta documental e entrada Instagram nesta rodada | WhatsApp oficial bidirecional, executor de IA, agenda, cobrança, onboarding por cliente, planos e quotas |
| Board BPO | Pode ser vendido mediante escopo de serviço e operação humana definida | Projetos, tarefas, contratos e relatórios dão apoio | Composição comercial, capacidade da equipe, agenda de acompanhamento, SLA e evidências de entrega |
| Avulsos | Podem ser representados como produtos/serviços do catálogo | Proposta com itens e controle de projeto | Fluxos próprios de briefing, revisão, aprovação, publicação e recorrência de hospedagem |

“Permite registrar” significa recurso no código, não confirmação de produto configurado em produção, disponibilidade da equipe ou entrega integral automatizada.

## Evidência do sistema atual

| Capacidade | Evidência | Conclusão |
|---|---|---|
| Produtos, preço, custo, recorrência, composição e versão | `apps/api/fattech/schemas.py`: Product, BundleItem | Existe modelo de catálogo |
| Pacote com produtos filhos | `bundle_items`, validação de referências em services | Existe composição declarativa; não é motor de configuração de oferta |
| Proposta com valores reprodutíveis | `sales_operations.py`: create_proposal | Congela nome, SKU, quantidade e preço; soma/subtrai valores inteiros |
| Termos de recorrência na proposta | Snapshot atual das linhas não inclui recurrence/unit | Falta distinguir cobrança única, mensalidade, primeiro pagamento e compromisso total |
| Composição automática da proposta | O criador precifica cada produto informado, sem expandir bundle_items | O operador ainda precisa compor a proposta conscientemente |
| Aprovação comercial | decide_proposal e contracts/approval_chain | Há transições internas; aceite registrado por operador não é aceite externo comprovado |
| Assinatura eletrônica | contracts.py, solicitação de assinatura recusa sem provedor | Integração de assinatura ausente |
| Financeiro | Invoice e rotas existentes | Controle interno, sem processador de pagamentos ou emissão fiscal |
| Assinatura de software | Ausência de subscription/billing/entitlements operacionais nos modelos e rotas | Não há liberação/suspensão automática de plano |
| Autonomia de IA | main.py: run_agent termina em 503 | Cadastro de agentes não executa atendimento autônomo |
| Conhecimento | Busca lexical e chunks; novo synapse_assistant.py | Consulta com citações; não é RAG semântico completo nem geração por LLM |
| Entrada Instagram | Novo instagram_ingest.py e correção de instagram_webhook.py | Materialização de mensagens autenticadas em desenvolvimento local |
| Entrega de mensagens | main.py: send/compliance | Avaliar elegibilidade não envia mensagem; adaptador continua pendente |
| Agenda | Nenhum serviço operacional de calendário/agendamento no catálogo atual | Ainda precisa ser implementado |
| Ambiente do comprador | Tenant existe, mas compra não cria tenant nem membership/entitlements | Falta provisionamento comercial e acesso do cliente |

## Engenharia necessária para venda modular

### 1. Catálogo único e ofertas versionadas

Criar `offer_versions`, `offer_components`, `price_versions` e regras de elegibilidade. Cada oferta precisa registrar módulos, serviço humano incluído, quantidade, prazo, limites e dependências. O backend deve calcular a composição; o site e o comercial consultam a mesma versão publicada.

Não usar apenas o nome do produto para habilitar recursos. Não inferir que toda oferta de maior preço contém automaticamente todas as inferiores. O enquadramento observado exige composição explícita, inclusive tráfego como adicional ao SYNAPSE quando aplicável.

### 2. Precificação e proposta

Congelar produto e versão, componentes, preço único, recorrente e por consumo, periodicidade, validade, escopo e descontos. Mostrar separadamente: implantação, primeiro pagamento, mensalidade e extras. Definir desconto recorrente versus desconto de implantação; não aplicar ambos por acidente. Alteração do catálogo não reescreve proposta emitida.

Evitar ciclos de pacote, duplicação de módulo em dois componentes e cobrança duplicada. Upgrade deve considerar o contrato já ativo, e não apenas gerar outra venda integral.

### 3. Contratação e cobrança

Criar pedido a partir de proposta aceita. Prover aceite público com token restrito, expiração e evidência. Conectar assinatura quando necessária ao modelo contratual. Integrar provedor de cobrança com IDs e webhooks idempotentes. Criar estados `pending`, `active`, `past_due`, `suspended`, `cancelled` e processo de conciliação. Retorno do navegador não comprova pagamento.

PIX, cartão e emissão fiscal são integrações distintas. A existência de Invoice não prova nenhuma delas. Primeiro selecionar e homologar o provedor; não fixar regras tributárias no código sem especificação adequada.

### 4. Ativação e permissões contratadas

Vincular contrato/assinatura ao tenant do comprador, com processo idempotente de provisionamento. Separar usuários da FAT Tech e equipe do cliente. Autorizações, módulos e quotas devem ser aplicados no servidor. Atraso/cancelamento precisa de política de acesso, exportação e retenção; nunca apagar dados pela simples falha de pagamento.

### 5. Implantação e entrega

Gerar projeto e checklist por oferta a partir do pedido. Definir responsável, dependências, prazos, briefing, acessos, fontes de conhecimento, validação de canal e aceite. Acompanhamento VIP precisa de datas e atividades verificáveis, não apenas uma descrição no produto.

### 6. SYNAPSE operacional

Completar WhatsApp oficial por organização, identidade de contatos, inbox, status de entrega e handoff. Conectar runtime de IA com ferramentas tipadas, conhecimento isolado, limites de custo e políticas de execução. Fazer qualificação/follow-up alterar tarefas e Kanban com versão/idempotência. Integrar agenda interna e Google Calendar com controle de conflito. Nenhuma confirmação de reunião ou pagamento pode ser produzida apenas por texto do agente.

### 7. Homologação pública

Testar a jornada: página → lead → proposta composta → aceite → pagamento confirmado → assinatura → tenant → implantação → mensagem recebida → atendimento → próxima ação → relatório → suporte/cancelamento. Repetir com dois tenants, eventos duplicados, falhas do provedor e alteração concorrente.

Publicar primeiro uma oferta piloto com capacidade de suporte conhecida. Venda consultiva pode usar etapas manuais declaradas; compra autônoma requer todo o ciclo integrado. Ter uma página com CTA de WhatsApp já permite iniciar vendas, mas não comprova checkout, contratação ou operação autônoma.

## Divergências comerciais a resolver

A home informa acompanhamento VIP de 60 dias e a página CRM informa 30 dias. A página CRM exibe indicadores de sistema/API ativos, embora os contratos locais ainda recusem execução de IA e envio real. Também apresenta agenda incluída no setup, enquanto não existe calendário operacional neste backend. Há referência temporal antiga na disponibilidade comercial. Essas diferenças devem ser revisadas com base no produto homologado antes de escalar a aquisição; nenhuma alteração no site foi feita nesta rodada.

## Critério para declarar “apto”

- **Venda consultiva assistida:** catálogo e escopo revisados, preços discriminados, contrato, cobrança por canal definido e responsável pela entrega.
- **Venda modular no CRM:** composição e preços calculados pelo servidor, snapshots, upgrades/adicionais e permissões por plano.
- **Venda pública autônoma:** aceite, cobrança confirmada, provisionamento e recuperação de falhas validados de ponta a ponta.
- **Promessa completa SYNAPSE:** atendimento real em canal oficial, IA executora, agenda, follow-up e métricas homologados no ambiente do cliente.

O estado atual suporta a base da primeira categoria. As outras não devem ser apresentadas como concluídas. A prova local da implementação desta rodada está em `docs/SYNAPSE_IMPLEMENTATION.md`.
