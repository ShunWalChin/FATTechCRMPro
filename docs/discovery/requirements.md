# Matriz de requisitos — FAT Tech CRM Pro

Consolidação em 2026-09-10. Documento de escopo e aceitação; **não é uma declaração de funcionalidades implementadas**. O estado de implementação deve ser demonstrado por código, testes e fluxo observado, e não inferido desta matriz.

## Objetivo de produto

Um site público FAT Tech em React com captura comercial integrada e uma aplicação interna para Walfredo e equipe operarem aquisição, vendas, atendimento, entrega, retenção, automações e conhecimento. A base técnica é TypeScript + Python; o domínio e a identidade são únicos, com separação explícita entre páginas públicas, operação autenticada e serviços internos.

“Completo”, “robusto” e “o melhor sistema” são objetivos de qualidade, não garantias de ausência de falhas. A entrega exige comportamento verificável, recuperação e diagnóstico. Multiempresas precisa contemplar tanto unidades de um mesmo grupo quanto organizações isoladas: compartilhar contato dentro de um grupo não autoriza ler outro tenant.

## Fontes

| Código | Fonte |
|---|---|
| U | Pedido explícito atual do usuário |
| P0–P5 | Markdown Palantyr numerados de 00 a 05 |
| K | Código, migrations, ADRs e registro do ZIP Palantyr v5.3 |
| S | Texto colado de transferência de conhecimento de 2026-09-10 |
| F | `PROJETO_FORT_GRUPO.md` |
| FC | `PROPOSTA_COMERCIAL_FORT_GRUPO.md` |
| R | Repositórios indicados pelo usuário; cobertura em `repositories.md` |

Prioridades: **P0** protege dados e permite o primeiro fluxo operacional; **P1** completa a operação comercial; **P2** amplia canais e inteligência; **P3** acrescenta verticais e escala. Uma dependência P0 não deve desaparecer por haver uma tela P2.

## Núcleo, site e experiência

| ID | Requisito | Fontes | Prioridade | Critério de aceite observável |
|---|---|---|---|---|
| WEB-01 | Site público FAT Tech em React, responsivo e consistente com HeroUI | U | P0 | Páginas abrem em desktop/mobile, navegação por teclado, layout sem overflow |
| WEB-02 | Serviços de IA, funis, marketing e contato com conteúdo fiel à empresa | U, P3, F | P0 | Conteúdo é revisável, sem depoimentos fabricados ou métricas/preços históricos tratados como atuais |
| WEB-03 | Formulário público integrado ao CRM | U, F | P0 | Submissão válida cria contato/oportunidade/atividade; reenvio não duplica; erros são claros |
| WEB-04 | Origem de lead, UTMs, página de entrada e registro de consentimento | F, FC | P0 | Operador vê origem e finalidade; consentimento não é presumido de dados importados |
| WEB-05 | SEO técnico, metadados, sitemap, robots e desempenho | U, F, FC | P1 | HTML indexável, canonical correto, rotas privadas fora do sitemap, assets otimizados |
| UX-01 | Login, sessão, logout e acesso restrito à equipe | U, S | P0 | Usuário não autenticado não acessa dados/API; logout invalida sessão conforme contrato |
| UX-02 | Estados vazio, carregando, erro, sem permissão e pendência de aprovação | P3, S | P0 | Toda área apresenta o estado real e permite recuperação; 202 aparece como pendente |
| UX-03 | Visão de sistema com capacidades ligadas, modo e saúde | S | P1 | Interface distingue funcional, indisponível e planejado; não mostra mock como integração ativa |
| UX-04 | Atualizações de inbox/gates com canal autenticado | S | P2 | Reconexão funciona, eventos respeitam tenant, fallback não finge “ao vivo” |

## CRM e operação

| ID | Requisito | Fontes | Prioridade | Critério de aceite observável |
|---|---|---|---|---|
| CRM-01 | Organizações, unidades de negócio, usuários, vínculos e papéis | U, P2, F | P0 | Escopo de unidade e tenant é explícito; usuário só seleciona organizações com vínculo ativo |
| CRM-02 | Contatos/clientes, empresas, tags, origem, responsável e histórico | P2, F | P0 | Criar, consultar, editar, buscar e filtrar persiste; detalhe reúne relacionamentos |
| CRM-03 | Deduplicação por identificadores normalizados | F, P2 | P0 | Telefone/e-mail repetido não cria duplicata silenciosa; merge mantém trilha |
| CRM-04 | Pipelines configuráveis, etapas, oportunidades e kanban | P2, F | P0 | Mudança de etapa persiste, tem autoria e concorrência tratada; não perde ordenação |
| CRM-05 | Valores em centavos, probabilidade, previsão, ganho/perda e motivo | P2, F | P0 | Soma e valor ponderado são exatos; perda registra motivo; dashboard deriva do banco |
| CRM-06 | Atividades, tarefas, agenda, lembretes e responsáveis | F, S, R | P1 | Próxima ação tem prazo/dono/status; tarefas vencidas e concluídas são filtráveis |
| CRM-07 | Catálogo de serviços/produtos e proposta comercial | F, FC | P1 | Itens, setup, recorrência, descontos e versões compõem total reprodutível |
| CRM-08 | Projetos de implantação, etapas de entrega e onboarding | K/processos, FC | P1 | Oportunidade ganha gera entrega rastreável; marcos, responsáveis e pendências são visíveis |
| CRM-09 | Retenção, health score, renovação e recompra | K/processos, F | P2 | Critérios do score são explícitos; rotina gera tarefa mensurável com supressão respeitada |
| CRM-10 | Importação/exportação com validação e auditoria | F, FC, P2 | P1 | Preview mostra erros/duplicatas; reimportação é segura; export respeita autorização/tenant |
| CRM-11 | Indicadores de aquisição, conversão, pipeline, receita e atividade | F, K/processos | P1 | Valores reconciliam com registros de origem e período; não são constantes de demonstração |
| CRM-12 | Campos/extensões por vertical | F | P3 | Frota/OS/pedidos não contaminam cadastro genérico nem exigem dados irrelevantes |
| CRM-13 | Frota, KM/horímetro, serviço, garantia, laudo PDF e recompra | F, FC | P3 | Extensão opt-in; cálculos configuráveis, documento ligado à OS, dados auditados |

## Canais e automações

| ID | Requisito | Fontes | Prioridade | Critério de aceite observável |
|---|---|---|---|---|
| MSG-01 | Inbox unificado, conversas, mensagens, responsável e estado | P2, S, R | P1 | Entrada autenticada gera uma única mensagem; histórico respeita canal e tenant |
| MSG-02 | WhatsApp oficial/Evolution e Instagram como adaptadores separados | U, P2, R | P2 | Cada conector declara capacidades, versão/API, saúde e credenciais; desconectado não envia |
| MSG-03 | Compliance determinístico no instante de envio | P2, P4, K | P0 antes de envio | Reavalia opt-out, blocklist, janela, template, automação e cooldown sobre corpo final |
| MSG-04 | Política de canal atualizável e baseada em documentação oficial | P4 | P0 antes de envio | Limites/janelas não são universalizados; política vigente é revisada ao ativar fornecedor |
| MSG-05 | Ingestão sem eco/grupo indevido e opt-out robusto | P2, S | P0 antes de envio | `is_echo` não reabre janela; variantes normalizadas de parada são reconhecidas e auditadas |
| MSG-06 | Entrega idempotente com claimed/sent/blocked/unknown/failed | P2, P4, S | P0 antes de envio | Claim precede rede; mesma chave/corpo repete resposta; corpo divergente retorna 409 |
| MSG-07 | Reconciliação de saída ambígua | P2, P5 | P0 antes de envio | Timeout/ambiguidade não causa retry automático; operador vê fila e motivo |
| MSG-08 | Templates, campanhas, sequências e pacing | P2, S, R | P2 | Preview congelado, segmentação/supressão, limite e execução rastreável; regras do provedor aplicadas |
| AUTO-01 | Flows como grafo persistido, versões e execuções | P2, R | P1 | Nós/arestas válidos; execução usa versão congelada; cada etapa registra saída/erro |
| AUTO-02 | Gatilhos, filtros, espera, ação, cooldown e agenda | P2, F | P1 | Reexecução/restart não duplica ação; waits duráveis; opt-out posterior cancela envio |
| AUTO-03 | Outbox transacional e workers separados da API | P2, P4 | P0 | Alteração e evento commitam juntos; rollback não publica; worker recupera lease vencido |
| AUTO-04 | Retries limitados, DLQ, rastreio e disjuntor de ciclos | P2, K | P0 | Falha permanente termina em fila visível; `trace_id`, origem e `hops` preservados |
| API-01 | API documentada, validação e envelope de erro estável | U, P2, S | P0 | OpenAPI e handlers concordam; entradas inválidas são recusadas sem stack/segredo |
| API-02 | Webhooks assinados, replay controlado e persistência idempotente | U, P2, P4 | P0 | HMAC usa corpo bruto; timestamp/ID quando disponíveis; duplicata não repete efeito |
| API-03 | Tokens de API com hash, escopo, expiração e revogação | P2, K | P1 | Token sem escopo recebe 403; revogado/expirado deixa de funcionar; segredo aparece só na criação |
| API-04 | Integração n8n por API/eventos | U, P2 | P1 | n8n consome eventos duráveis com autenticação e idempotência; indisponibilidade não perde alteração |

## Governança, IA e conhecimento

| ID | Requisito | Fontes | Prioridade | Critério de aceite observável |
|---|---|---|---|---|
| GOV-01 | Registro dos 39 agentes, 11 squads e seis papéis executivos | U, P2, S, K | P1 | Contratos descrevem papel, ferramentas, autonomia, orçamento e supervisão; quantidade não implica 39 processos permanentes |
| GOV-02 | Autonomia A0–A4 e autorização por capacidade | P2, S | P0 antes de agente com efeito | Políticas negam ação não permitida no servidor; chamada direta não contorna UI |
| GOV-03 | Gates G1–G6 com intenção imutável, expiração e decisão auditada | P2, S | P1 | 202 retém operação; aprovação executa exatamente uma vez; rejeição/expiração não executa |
| GOV-04 | Separação de funções e exceções estritas | P4, S | P0 antes de gates ativos | Solicitante não aprova por padrão; exceção de proprietário explícita por identidade e organização |
| GOV-05 | Modo seguro/dry-run com trava persistente | P5, S | P0 | Recurso desarmado não produz efeito externo; UI informa simulação, log registra intenção |
| AI-01 | Ruflo instalado e usado no fluxo de engenharia | U | P0 de ambiente | Versão/proveniência documentada e execução local demonstrada; não confundir CLI instalada com agentes de produção ativos |
| AI-02 | Ponytail instalado/usado para trabalho com código | U | P0 de ambiente | Integração e comando verificáveis; entrada/saída documentadas |
| AI-03 | Budget Guard executável por organização | P2, S | P0 antes de IA paga | Reserva atômica antes da chamada, reconciliação do custo, teto compartilhado entre workers e kill-switch persistente |
| AI-04 | IA copiloto e execução Python com contrato explícito | U, P2, S | P2 | Sem chave/provedor responde indisponível; não fabrica resposta real; timeout e custo são registrados |
| AI-05 | Conteúdo externo sem autoridade e ferramentas com allowlist | P2, P4, S | P0 antes de IA | E-mail/documento/grafo não concede capacidade; texto malicioso não dispara envio/exportação |
| KB-01 | Base de conhecimento, notas, revisões, relações e busca | P2, K | P1 | Documentos são ligados a tenant/dono, busca mantém proveniência e ACL |
| KB-02 | Graphify instalado e integrado ao trabalho/sistema | U | P1 | Grafo é gerado de fontes permitidas com proveniência; ingestão não executa comandos do conteúdo |
| KB-03 | IMAP somente leitura, agenda e digest | P2, S | P2 | Consulta não altera caixa; permissão pessoal não é concedida a todo admin; digest cita origem |
| KB-04 | MCP e integrações de ferramentas | P2 | P3 | Capacidades explícitas, autenticação, rate limit e autorização equivalente à API |

## Segurança, dados e operação

| ID | Requisito | Fontes | Prioridade | Critério de aceite observável |
|---|---|---|---|---|
| SEC-01 | RLS e contexto de organização por transação | P2, P4, S | P0 | Papel da aplicação não é dono/superuser/BYPASSRLS; tenant A não lê/altera/apaga/insere dados de B |
| SEC-02 | Mesmo isolamento e RBAC em CRM, governança, IA e jobs | S | P0 | Token de qualquer tenant/papel não atravessa plano menos protegido |
| SEC-03 | Organização derivada de credencial confiável | P4, S | P0 | Body/query com tenant alheio não muda autorização; job tem contexto persistido e validado |
| SEC-04 | Autenticação real e sessões protegidas | P2, S | P0 | Login de demonstração não entra em produção; expiração, assinatura e revogação são testadas |
| SEC-05 | Cofre de credenciais server-side e rotação | P2, K | P0 | Frontend/logs não recebem segredo; cifra autenticada tem chave versionada separada do banco |
| SEC-06 | Auditoria transacional por organização e concorrência | P2, S | P0 | Mutação e registro não divergem; concorrência não bifurca cadeia; modificação indevida é detectada |
| SEC-07 | Âncora externa de auditoria | P2, S | P2 | Hash final é armazenado fora do alcance administrativo do banco; verificação é rastreável |
| SEC-08 | Proxy seguro, URLs validadas e defesa SSRF | P2, P4 | P0 antes de fetch arbitrário | Rede interna/metadados bloqueados; redirects e DNS rebinding não escapam à validação |
| SEC-09 | Cabeçalhos, CORS, CSRF e proxy confiável | S | P0 | Resposta HTML real recebe política; origem indevida recusada; IP forjado não reinicia cota |
| SEC-10 | Consentimento, opt-out, supressão, anonimização e portabilidade | F, FC, P2 | P1 | Histórico de finalidade é mantido; pedido de supressão altera todos envios futuros |
| OPS-01 | Repo canônico FATTechCRMPro, documentação e CI | U, S | P0 | Build/testes reproduzíveis, lockfiles e migrations versionados, nenhum segredo ou base real no Git |
| OPS-02 | Deploy Oracle isolado do legado | U, P5, S | P0 | Projeto/volumes próprios; inventário anterior preservado; health e rollback do novo serviço demonstrados |
| OPS-03 | Liveness barata e readiness limitada | S | P0 | Health não varre auditoria nem expõe configuração; dependência indisponível aparece sem custo ilimitado |
| OPS-04 | Backup consistente e restauração testada | P5, S | P0 antes de dados reais | Artefato restaurado em banco descartável; RPO/RTO medidos e execução registrada |
| OPS-05 | Migrations explícitas e banco descartável | P4, S | P0 | Instalação vazia/restart usam mesma versão; schema qualificado; migration aplicada não é reescrita |
| OPS-06 | Observabilidade e operação pela interface | P5, S | P1 | Erros/jobs/unknown/gates têm dono, idade e ação; logs usam request/trace sem dados sensíveis |
| OPS-07 | Inventário de dependências/licenças e recursos | U, K | P0 | SHA/licença da referência e versão de dependência documentados; limites do host são observados |

## Sequência de entrega e prova

1. **Fundação:** ambiente, Git, contratos, configuração, autenticação real, modelo de dados, tenancy/RBAC, migrations, CI e deploy isolado.
2. **Primeiro fluxo de receita:** site → formulário → contato/oportunidade → tarefa → pipeline → ganho/perda → relatório, pela interface e banco reais.
3. **Operação completa:** inbox, tarefas, catálogo/propostas, entrega, integrações API/n8n, busca, importação e auditoria.
4. **Automações externas:** conectores configurados, webhook assinado, compliance, idempotência, reconciliação, campanhas e opt-out.
5. **IA governada:** budget atômico, política e gates, Ruflo/Graphify com fronteira de dados, provedores reais, custos observados.
6. **Ampliação:** retenção, conhecimento pessoal, canais adicionais, verticais, escala e critérios de SLO medidos.

## Limites de aceitação

- Tela, schema e serviço não registrado não contam como recurso entregue.
- Build verde não comprova fluxo; teste unitário não comprova isolamento real ou entrega em plataforma.
- Connector sem credencial/configuração pode ser entregue como adaptador validado com testes, mas deve aparecer como desconectado.
- Dados e métricas de demonstração devem ser identificados e separados do estado operacional.
- Regras Meta/WhatsApp, licenças e versões não são congeladas por um documento de agosto: são verificadas na fonte quando a integração é ativada.
- As provas mínimas críticas incluem isolamento entre dois tenants, login inválido/expirado, replay/409, timeout sem duplicação, opt-out entre agendamento e envio, reserva concorrente de orçamento, restauração de backup e reinício de worker sem perda.
- O indicador de negócio herdado do Palantyr é reduzir a execução operacional manual de Walfredo. A meta histórica de menos de dez horas semanais é um indicador a medir, não um resultado prometido.
