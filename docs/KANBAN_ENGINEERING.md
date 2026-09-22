# Engenharia e lógica do Kanban 

Este documento define o contrato funcional e técnico do quadro de oportunidades. Ele é a referência para API, banco, frontend, automações, métricas e testes. O Kanban é uma projeção operacional do funil de vendas: a fonte de verdade é a oportunidade (`deal`) ligada a uma organização, a um funil e a uma etapa.

## 1. Escopo e princípios

- Cada organização possui seus próprios funis, etapas, oportunidades, usuários e configurações.
- Toda mutação é autorizada no servidor, validada contra o funil e registrada em auditoria.
- A oportunidade nunca pode ficar sem funil ou em uma etapa inexistente.
- A ordem visual é determinística e concorrente: `position` ordena os cartões e `version` protege contra sobrescrita perdida.
- O quadro não é a fonte de métricas derivadas. Histórico de etapas, atividades e eventos formam a trilha de auditoria.
- Operações externas (mensagens, agenda, cobrança) entram como eventos idempotentes; o Kanban não simula sucesso de integração.

## 2. Modelo de domínio

### Organização e autorização

Todas as tabelas de negócio carregam `organization_id`. O contexto autenticado fornece `user_id`, organização ativa e papel. `owner`/`super_admin` administra configuração do funil; `admin` gerencia registros; papéis comerciais podem operar oportunidades conforme escopo de proprietário/equipe; somente leitura não muta.

### Funil (`pipeline`)

Campos mínimos: `id`, `organization_id`, `name`, `description`, `status` (`active|inactive`), `is_default`, `version`, `created_at`, `updated_at`.

Uma configuração de etapa contém:

```json
{
  "key": "qualificacao",
  "label": "Qualificação",
  "probability": 25,
  "outcome": "open",
  "expected_duration_hours": 72,
  "required_fields": ["contact_id", "owner_id"]
}
```

`key` é estável para integrações; `label` é editável. Há de 1 a 40 etapas. Etapas abertas usam `outcome=open`; fechadas usam `won` ou `lost`. A probabilidade é um inteiro de 0 a 100.

### Oportunidade (`deal`)

Campos: `id`, `organization_id`, `title`, `contact_id`, `company_id`, `conversation_id`, `pipeline_id`, `stage`, `value_cents`, `probability`, `expected_close`, `next_action_at`, `position`, `owner_id`, `lost_reason`, `notes`, `last_activity_at`, `version`, `created_at`, `updated_at`.

`last_activity_at` é servidor-owned e muda quando há atividade comercial relevante. `position` é inteiro positivo; valores espaçados (por exemplo, 1000) permitem reordenação barata. `version` começa em 1 e incrementa em toda mutação.

### Histórico e atividades

`deal_stage_history` registra `deal_id`, etapas anterior/nova, usuário ou agente executor, motivo, instante, probabilidade e valor observados. `activities` registra notas, ligações, reuniões, mensagens, tarefas e automações. Ambos são append-only para auditoria e relatórios.

## 3. Invariantes do negócio

1. Oportunidade e funil pertencem à mesma organização.
2. A etapa informada deve existir no funil.
3. Funil inativo não aceita criação nem atribuição de novas oportunidades; registros existentes continuam editáveis.
4. Ao omitir `pipeline_id`, usar o funil ativo padrão da organização e persistir a escolha.
5. Ao criar ou mover uma oportunidade em etapa aberta, a probabilidade omitida herda a da etapa; uma probabilidade explícita, inclusive zero, é preservada.
6. Etapa `won` força probabilidade 100 e etapa `lost` força 0.
7. Entrar em `lost` exige `lost_reason` não vazio. Reabrir limpa o motivo; ganhar também não mantém motivo de perda.
8. Campos exigidos pela etapa são validados antes da transação (`contact_id`, `company_id`, `owner_id`, `value_cents`, `expected_close` ou `next_action_at`).
9. Não se remove nem renomeia uma etapa que tenha oportunidades ativas. Não se exclui um funil com oportunidades ativas.
10. Uma oportunidade só pode ter uma posição dentro do seu funil e etapa; a ordenação usa `position ASC, created_at ASC, id ASC`.

## 4. Máquina de estados

O estado visual é derivado de `pipeline.stages[stage].outcome`:

```text
open --qualquer etapa aberta--> open
open --etapa won-------------> won (terminal operacional)
open --etapa lost------------> lost (terminal operacional)
won --reabertura explícita---> open
lost --reabertura explícita--> open
```

Mover entre duas etapas abertas gera uma transição normal. Mover para fechamento exige os campos e registra histórico. Uma reabertura deve indicar usuário, motivo opcional e nova etapa aberta. Alterar diretamente `outcome` de uma etapa ocupada é rejeitado para impedir mudança retroativa de semântica.

## 5. Operações transacionais

### Criar

1. Resolver organização e autorização.
2. Resolver funil explícito ou padrão ativo.
3. Validar status do funil, etapa, campos obrigatórios e referências.
4. Calcular probabilidade e `position = max(position)+1000` na etapa.
5. Inserir oportunidade, histórico inicial e evento `deal.created` na mesma transação.

### Atualizar dados

Receber `version` obrigatório. Validar somente campos enviados, reaplicar as invariantes e incrementar versão. Uma alteração de contato, empresa, proprietário, valor, previsão ou próxima ação atualiza `last_activity_at` quando representar atividade comercial; alterações puramente administrativas podem informar `touch_activity=false`.

### Mover etapa

Receber `{stage, version, lost_reason?}`. Validar estado, requisitos e fechamento; calcular probabilidade quando não explícita; atribuir nova posição no fim da coluna se nenhuma posição foi fornecida; gravar histórico e emitir `deal.stage_changed` atomicamente.

### Reordenar

Receber `{deal_id, target_stage, before_deal_id?, after_deal_id?, version}`. Calcular posição entre vizinhos (`floor((before+after)/2)`) ou no início/fim. Se o intervalo ficar pequeno, renumerar apenas a coluna em uma transação. Retornar a lista ordenada e as versões afetadas.

## 6. Concorrência e idempotência

- Toda atualização usa `UPDATE ... WHERE id=? AND version=?`; zero linhas resulta em `409 VERSION_CONFLICT` com estado atual.
- Drag-and-drop deve aplicar atualização otimista no cliente e reverter para o snapshot do servidor em conflito.
- Eventos de entrada usam `provider`, `external_event_id` e `organization_id` únicos. Repetição retorna o resultado original.
- Jobs de automação usam chave idempotente `deal_id + rule_id + execution_window`.
- Transações curtas; bloqueio de linha somente para cálculo de posição, renumeração e troca de funil padrão.

## 7. API HTTP

Rotas base: `GET/POST/PATCH/DELETE /api/v1/{resource}`. Consultas de oportunidades aceitam `q`, `status`, `stage`, `pipeline_id`, `contact_id`, `conversation_id`, `limit` e `offset`; resposta inclui `contact_name` e `company_name` quando disponíveis.

Endpoints especializados recomendados:

- `POST /api/v1/deals/{id}/move` — mudança de etapa.
- `POST /api/v1/deals/{id}/reorder` — posição dentro da coluna.
- `GET /api/v1/pipelines/{id}/board` — colunas, cartões e contagens paginadas.
- `GET /api/v1/deals/{id}/timeline` — histórico, atividades e auditoria.
- `GET /api/v1/crm/radar?pipeline_id=` — risco operacional.

Erros são estáveis: `422 VALIDATION_ERROR` (inclui `required_fields` e `stage`), `409 VERSION_CONFLICT`, `409 STAGE_IN_USE`, `409 PIPELINE_IN_USE`, `403 FORBIDDEN`, `404 NOT_FOUND`. Nunca retornar stack trace ou segredo.

## 8. Frontend e experiência

O quadro renderiza colunas por configuração do funil, contagem total e paginação/infinite scroll. Cada cartão mostra título, contato, empresa, valor, probabilidade, próxima ação, idade e proprietário. Drag-and-drop usa eventos de ponteiro para mouse, toque e caneta; teclado oferece seletor de etapa, mover para início/fim e anúncio via live region. Ao soltar em `lost`, abrir diálogo de motivo; ao encontrar conflito, informar que o cartão foi atualizado por outra pessoa e recarregar.

Filtros de busca, proprietário, etapa, risco, período e valor devem ser refletidos na URL. O detalhe da oportunidade possui abas de dados, atividades, tarefas, conversas, histórico e auditoria.

## 9. Radar, SLA e previsão

Para cada oportunidade aberta, calcular `elapsed_hours = now - last_activity_at` e comparar com `expected_duration_hours`. Próxima ação futura mantém risco controlado; ausência de ação, atraso e etapa parada classificam `em_dia`, `em_voo`, `em_risco` ou `critico`. A faixa quente/morno/frio deriva da probabilidade. O forecast ponderado soma `value_cents * probability / 100`, segmentado por proprietário, origem, funil e período.

## 10. Eventos e automações

Eventos mínimos: `deal.created`, `deal.updated`, `deal.stage_changed`, `deal.reordered`, `deal.won`, `deal.lost`, `deal.reopened`, `deal.risk_changed`. Um outbox transacional publica esses eventos para notificações, tarefas, agentes de IA, n8n, agenda e relatórios. Consumidores devem ser idempotentes, ter retry com backoff e dead-letter; falha de integração não desfaz a transação do Kanban.

Regras configuráveis podem criar tarefa, notificar responsável, solicitar aprovação, iniciar sequência ou chamar agente. Toda ação externa passa por política de consentimento, janela do canal, blocklist e limite de frequência; o Kanban apenas registra a decisão e o resultado.

## 11. Segurança, RLS e auditoria

RLS deve restringir todas as consultas por `organization_id` e escopo do usuário. Alterações de pipeline exigem papel administrativo; alterações de oportunidade respeitam proprietário/equipe. Campos sensíveis e tokens de integração ficam fora das respostas públicas. Auditoria registra ator humano/agente, ação, recurso, antes/depois, IP/correlation-id e motivo. Exclusões seguem soft delete quando houver dependências; hard delete só por rotina administrativa documentada.

## 12. Banco e desempenho

Índices essenciais: `(organization_id, pipeline_id, stage, position)`, `(organization_id, owner_id, status)`, `(organization_id, last_activity_at)`, `(organization_id, expected_close)`, histórico por `(deal_id, created_at DESC)` e outbox por `(status, available_at)`.

Usar paginação por cursor no board em grandes volumes, selecionar colunas necessárias e pré-carregar nomes de contato/empresa sem N+1. Métricas de consulta, latência de transição, conflitos de versão e tamanho de outbox entram em observabilidade.

## 13. Testes de aceitação

- criação sem funil adota o padrão correto;
- funil inativo, etapa desconhecida e campo obrigatório retornam erro;
- probabilidades herdadas, explícitas e estados won/lost obedecem às invariantes;
- motivo de perda é obrigatório e reabertura limpa o motivo;
- etapa/funil ocupados não podem ser removidos;
- duas escritas com a mesma versão produzem uma vitória e um `409`;
- reordenação funciona no início, meio, fim e após renumeração;
- RLS impede acesso entre organizações e auditoria não pode ser alterada;
- eventos duplicados não criam tarefas ou mensagens duplicadas;
- quadro funciona com teclado, toque, leitor de tela e conexão interrompida;
- radar e forecast reproduzem os valores esperados com relógio congelado.

## 14. Entrega incremental

**Fase A — contrato:** consolidar schema, invariantes, erros, índices e testes de transição.

**Fase B — operação:** timeline, atividades, tarefas, busca global, filtros, paginação e notificações.

**Fase C — receita:** propostas, produtos, contratos, motivos de perda, forecast e metas.

**Fase D — inteligência:** scoring, playbooks, agentes executores, recomendações e automações via outbox.

Cada fase deve manter migração reversível, feature flag, telemetria e documentação de API. Nenhuma evolução deve alterar o significado de uma `stage.key` já usada por integrações.
