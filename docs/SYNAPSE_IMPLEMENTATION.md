# SYNAPSE — implementação local de 24/09/2026

Esta entrega prepara a operação comercial do SYNAPSE dentro do CRM. Não equivale à implantação de todos os componentes do blueprint nem à publicação na Oracle.

## Fluxo entregue

1. Administrador abre `/crm/synapse` e prepara a estrutura por organização, com valores editáveis de implantação e licença.
2. O backend cria um funil dedicado, dois itens de catálogo e o cadastro pausado de um copiloto. Não substitui o funil padrão nem o catálogo existente. Repetição retorna a configuração original.
3. O administrador define responsável e prazo, liga ou pausa a operação e pode habilitar vinculação da captura pública.
4. Vincular contato cria oportunidade e tarefa com vencimento; uma execução persistente impede duplicação mesmo com operadores ou requisições diferentes.
5. A captura pública habilitada usa esse fluxo na mesma transação. Caso uma alteração posterior invalide o funil, o contato continua salvo e uma pendência é auditada.
6. Webhooks Instagram autenticados resolvem todas as contas do envelope. Mensagens novas materializam contato, conversa e mensagem recebida. Duplicatas são reconhecidas por mensagem; eco/status não viram leads. Datas fora de ordem não reabrem a janela indevidamente.
7. A consulta de conhecimento cita documentos ativos da organização. Ausência de evidência cria uma tarefa de revisão humana, sem duplicá-la, e deixa a conversa pendente. Não ocorre envio externo.
8. Quando o Core-Engine fecha um lote de mensagens recebidas, uma organização com SYNAPSE ativo ganha uma ação operacional na mesma transação: evidência suficiente cria um rascunho citável; ausência de evidência cria uma tarefa de handoff para o responsável da operação. O lote é a chave de idempotência, então replay de evento não duplica nem rascunho nem tarefa.

## API

| Método e rota | Contrato |
|---|---|
| GET `/api/v1/synapse/overview` | Configuração, métricas, prontidão e últimos vínculos |
| POST `/api/v1/synapse/setup` | `setup_cents`, `monthly_cents`, `sla_hours`; somente admin; singleton por tenant |
| POST `/api/v1/synapse/settings` | `version`, `enabled`, `capture_enabled`, `owner_id`, `sla_hours`; 409 em concorrência |
| POST `/api/v1/synapse/enroll` | `contact_id`; retorna `deal_id`, `task_id`, `due_at` e `duplicate` |
| GET `/api/v1/synapse/runs` | Histórico paginado por `limit`/`offset` |
| POST `/api/v1/synapse/assist` | `conversation_id`, `question` opcional até 500 caracteres; `Idempotency-Key` opcional |
| POST `/api/v1/synapse/knowledge/bootstrap` | Admin; instala de forma idempotente o corpus comercial revisado do SYNAPSE no tenant |
| POST `/api/v1/synapse/assists/{id}/generate` | Aprimora manualmente um rascunho extrativo com o modelo configurado; preserva a versão original, fontes e `sent=false` |

`assist` retorna `status=draft|handoff`, `body`, `citations`, `provider=lexical`, `sent=false`, `reason`, `task_id`. É uma consulta extrativa, não um modelo gerador. Examina até 200 documentos recentes e devolve até três fontes. Termos, versões e hashes explicam de onde vieram os trechos. Índices antigos não reintroduzem documentos excluídos. Um replay idempotente representa a resposta original, como nos demais comandos de criação do sistema.

O executor interno reutiliza a mesma preparação por meio de `prepare_assistance(...)` no módulo `synapse_assistant`. Ele recebe o texto do lote, limita a pergunta a 500 caracteres, consulta o corpus atual e grava `synapse_assists` com `source_batch_id`, `trigger=message_batch`, `requested_by=core-engine` e `sent=false`. O evento de auditoria é `synapse.auto_assisted`. O worker não possui caminho para chamada de provedor ou envio; somente uma etapa posterior, explicitamente aprovada, poderá converter o rascunho em mensagem externa.

Na versão 0.7.0 local, o atendente pode escolher **Aprimorar rascunho com IA**. Isso exige modelo e URL `/v1` no servidor, `ai_enabled=true` no tenant e rascunho com fontes ainda vigentes. O servidor grava uma reivindicação curta antes da chamada externa, revalida documento, conversa e opt-out depois, e só então substitui o texto apresentado. Erro do modelo preserva o rascunho extrativo e permite nova tentativa. A resposta precisa citar índices válidos; o endpoint não chama canal de envio. O provedor remoto também exige `FATTECH_AI_REMOTE_ENABLED=true` no servidor, desligado por padrão. Identificadores comuns são mascarados, mas isso não substitui uma revisão de privacidade para transferência de dados reais.

Na instalação, três documentos revisados são criados no tenant: proposta de valor, limites de atendimento e roteiro de qualificação. A operação também pode repor os documentos ausentes pelo endpoint de bootstrap, sem duplicá-los. O corpus inicial só autoriza rascunhos fundamentados; ele não habilita um provedor LLM nem envio externo.

## Persistência e isolamento

Usa `records` com kinds internos `synapse_config`, `synapse_runs`, `synapse_assists`, cobertos pelo RLS existente. Eles não entram no CRUD genérico. Configuração e matrículas usam UUID determinístico por tenant; locks transacionais seguem contatos antes da configuração e recursos vinculados. Auditoria/outbox acompanham a transação. Os endpoints autenticados usam CSRF e scopes; admin por sessão é necessário para configurar.

Não há nova tabela nem migração de schema nesta rodada. A produção continua exigindo suas migrations e papel sem bypass de RLS. Testes SQLite não substituem homologação PostgreSQL.

## Instagram

O ID da conta deixou de ser usado como ID de entrega. Hash do envelope impede reprocessar a mesma entrega; conta + `mid` impede duplicação quando a mensagem reaparece em outro envelope. Envelopes misturando donos ou contas desconhecidas são recusados. Não há inferência de consentimento de marketing pela simples entrada da mensagem. PARAR registra opt-out; anexos são representados sem baixar URLs remotas.

O campo `last_inbound_at` continua protegido contra edição pública, mas sua presença não impede editar título/status da conversa. O evento `instagram.webhook.received` conserva a estrutura do envelope para os consumidores n8n existentes, retirando payloads de anexos que podem conter URLs temporárias com credenciais. Consumidores de mídia precisam ser adaptados para esse limite. Mensagens operacionais também geram seus eventos com identificadores de CRM.

## Limites

- WhatsApp oficial e envio externo ainda não implementados neste módulo.
- Executor autônomo de LLM, NVIDIA RAG semântico/pgvector e agenda Google ainda pendentes. O caminho inbound→rascunho/handoff continua extrativo; somente a ação manual de aprimorar pode chamar o modelo configurado, sempre sem envio.
- Preparar SYNAPSE não cria uma assinatura nem um workspace para o cliente comprador.
- Recorrência no catálogo ainda não gera cobranças.
- Instagram recebido entra na inbox; não aciona matrícula comercial automática nesta rodada.
- A captura pública do workspace FAT Tech foi habilitada em 24/09/2026 pela configuração administrativa da operação. O formulário institucional agora registra o lead no endpoint público antes de abrir o WhatsApp; essa alteração de frontend aguarda a próxima publicação. Nenhuma mensagem externa foi enviada e nenhum segredo ou DNS foi alterado.

## Validação

- Core-Engine: 9 testes passaram, incluindo crash antes da conclusão do lote, draft fundamentado, handoff e replay idempotente.
- SYNAPSE e assistência: 17 testes passaram, incluindo isolamento, bootstrap da base, matrícula, consulta manual e opt-out.
- TypeScript do frontend (`npm run typecheck`) passou.
- Ruff nos módulos e testes alterados passou; `git diff --check` não encontrou erro de whitespace.
- `graphify update .` continua bloqueado neste host porque o executável aponta para um Python 3.12 ausente; isso não afetou os testes do código.

Os pulados dependem de condições específicas do ambiente, incluindo PostgreSQL; não constituem prova desses cenários. Testes de mensagens não enviaram nada para provedores reais. O build gerou a rota `/crm/synapse`, mas não foi implantado na Oracle.

## Publicação e operação

Revisar diff e inventário, executar CI com PostgreSQL, gerar pacote do commit revisado e seguir `docs/OPERATIONS.md`. Após publicar, abrir `/crm/synapse` com administrador, preparar catálogo e habilitar captura conscientemente. Não marcar configurações externas como prontas até testar os conectores reais. Voltar a configuração `capture_enabled=false` impede novas matrículas pelo hook; os registros já criados permanecem auditáveis.
