# SYNAPSE — implementação local de 20/09/2026

Esta entrega prepara a operação comercial do SYNAPSE dentro do CRM. Não equivale à implantação de todos os componentes do blueprint nem à publicação na Oracle.

## Fluxo entregue

1. Administrador abre `/crm/synapse` e prepara a estrutura por organização, com valores editáveis de implantação e licença.
2. O backend cria um funil dedicado, dois itens de catálogo e o cadastro pausado de um copiloto. Não substitui o funil padrão nem o catálogo existente. Repetição retorna a configuração original.
3. O administrador define responsável e prazo, liga ou pausa a operação e pode habilitar vinculação da captura pública.
4. Vincular contato cria oportunidade e tarefa com vencimento; uma execução persistente impede duplicação mesmo com operadores ou requisições diferentes.
5. A captura pública habilitada usa esse fluxo na mesma transação. Caso uma alteração posterior invalide o funil, o contato continua salvo e uma pendência é auditada.
6. Webhooks Instagram autenticados resolvem todas as contas do envelope. Mensagens novas materializam contato, conversa e mensagem recebida. Duplicatas são reconhecidas por mensagem; eco/status não viram leads. Datas fora de ordem não reabrem a janela indevidamente.
7. A consulta de conhecimento cita documentos ativos da organização. Ausência de evidência cria uma tarefa de revisão humana, sem duplicá-la, e deixa a conversa pendente. Não ocorre envio externo.

## API

| Método e rota | Contrato |
|---|---|
| GET `/api/v1/synapse/overview` | Configuração, métricas, prontidão e últimos vínculos |
| POST `/api/v1/synapse/setup` | `setup_cents`, `monthly_cents`, `sla_hours`; somente admin; singleton por tenant |
| POST `/api/v1/synapse/settings` | `version`, `enabled`, `capture_enabled`, `owner_id`, `sla_hours`; 409 em concorrência |
| POST `/api/v1/synapse/enroll` | `contact_id`; retorna `deal_id`, `task_id`, `due_at` e `duplicate` |
| GET `/api/v1/synapse/runs` | Histórico paginado por `limit`/`offset` |
| POST `/api/v1/synapse/assist` | `conversation_id`, `question` opcional até 500 caracteres; `Idempotency-Key` opcional |

`assist` retorna `status=draft|handoff`, `body`, `citations`, `provider=lexical`, `sent=false`, `reason`, `task_id`. É uma consulta extrativa, não um modelo gerador. Examina até 200 documentos recentes e devolve até três fontes. Termos, versões e hashes explicam de onde vieram os trechos. Índices antigos não reintroduzem documentos excluídos. Um replay idempotente representa a resposta original, como nos demais comandos de criação do sistema.

## Persistência e isolamento

Usa `records` com kinds internos `synapse_config`, `synapse_runs`, `synapse_assists`, cobertos pelo RLS existente. Eles não entram no CRUD genérico. Configuração e matrículas usam UUID determinístico por tenant; locks transacionais seguem contatos antes da configuração e recursos vinculados. Auditoria/outbox acompanham a transação. Os endpoints autenticados usam CSRF e scopes; admin por sessão é necessário para configurar.

Não há nova tabela nem migração de schema nesta rodada. A produção continua exigindo suas migrations e papel sem bypass de RLS. Testes SQLite não substituem homologação PostgreSQL.

## Instagram

O ID da conta deixou de ser usado como ID de entrega. Hash do envelope impede reprocessar a mesma entrega; conta + `mid` impede duplicação quando a mensagem reaparece em outro envelope. Envelopes misturando donos ou contas desconhecidas são recusados. Não há inferência de consentimento de marketing pela simples entrada da mensagem. PARAR registra opt-out; anexos são representados sem baixar URLs remotas.

O campo `last_inbound_at` continua protegido contra edição pública, mas sua presença não impede editar título/status da conversa. O evento `instagram.webhook.received` conserva a estrutura do envelope para os consumidores n8n existentes, retirando payloads de anexos que podem conter URLs temporárias com credenciais. Consumidores de mídia precisam ser adaptados para esse limite. Mensagens operacionais também geram seus eventos com identificadores de CRM.

## Limites

- WhatsApp oficial e envio externo ainda não implementados neste módulo.
- Executor autônomo de LLM, NVIDIA RAG semântico/pgvector e agenda Google ainda pendentes.
- Preparar SYNAPSE não cria uma assinatura nem um workspace para o cliente comprador.
- Recorrência no catálogo ainda não gera cobranças.
- Instagram recebido entra na inbox; não aciona matrícula comercial automática nesta rodada.
- Nenhum serviço público, segredo ou DNS foi alterado nesta entrega.

## Validação

- Backend completo: 260 passaram e 12 foram pulados; execução anterior aos ajustes finais de prontidão e vínculo de empresa.
- Módulos novos de SYNAPSE/assistência/Instagram: 29 passaram após a revisão de mídia; teste adicional de empresa incluído e suíte SYNAPSE novamente aprovada com 11 testes.
- Navegador: quatro testes passaram, incluindo contrato da interface, acesso de leitura, largura móvel, resposta inválida e matrícula via API real.
- TypeScript e build de produção do frontend passaram.
- Ruff nos novos módulos e testes passou.

Os pulados dependem de condições específicas do ambiente, incluindo PostgreSQL; não constituem prova desses cenários. Testes de mensagens não enviaram nada para provedores reais. O build gerou a rota `/crm/synapse`, mas não foi implantado na Oracle.

## Publicação e operação

Revisar diff e inventário, executar CI com PostgreSQL, gerar pacote do commit revisado e seguir `docs/OPERATIONS.md`. Após publicar, abrir `/crm/synapse` com administrador, preparar catálogo e habilitar captura conscientemente. Não marcar configurações externas como prontas até testar os conectores reais. Voltar a configuração `capture_enabled=false` impede novas matrículas pelo hook; os registros já criados permanecem auditáveis.
