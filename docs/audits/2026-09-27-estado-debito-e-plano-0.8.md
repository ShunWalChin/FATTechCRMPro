# Estado atual, débito técnico e plano da 0.8 — 27/09/2026

## Como este estado foi verificado

- Repositório `main` limpo em `c5bd3b6` (`package.json` e `apps/api/pyproject.toml`: 0.7.0).
- GitHub Actions [run 37](https://github.com/ShunWalChin/FATTechCRMPro/actions/runs/36314036284) concluído com sucesso: 377 testes de API com PostgreSQL, Ruff, typecheck, build, auditoria npm, 20 testes MCP e Playwright.
- Suíte local com cobertura de branches: 365 testes aprovados, 12 ignorados pela ausência de URLs PostgreSQL descartáveis nesta estação; cobertura combinada da API de **87%**. Os 12 testes executam na CI.
- Inventário textual: 131 rotas, 21 domínios, 22 tabelas, 23 páginas; zero rotas classificadas como órfãs ou sem teste. Presença de uma URL em um teste não prova cobertura de todos os cenários da rota.
- Acesso público ao login do CRM verificado no navegador. A consulta de leitura a `/api/health` na Oracle retornou `{"status":"ok","version":"0.5.1","environment":"production"}`. Portanto o código 0.7.0 **não está implantado**.
- A chave Oracle fornecida foi novamente recusada para `opc` (`Permission denied (publickey,...)`). Não foi possível inspecionar contêineres, migrações, fila, logs ou backups do host.
- `graphify update .` reconstruiu o grafo local. Ainda há extração parcial de `apps/web/components/crm-ui.tsx` e 174 avisos de schema no grafo derivado; o build TypeScript e os testes passaram.

## Capacidade real do código 0.7.0

| Área | Implementado no código | Limite operacional |
| --- | --- | --- |
| CRM comercial | Captura do site, deduplicação e fusão, campos personalizados, qualificação explicável, distribuição, kanban, propostas, contratos, metas, relatórios, tarefas e projetos | Não há prova de que as evoluções após 0.5.1 estejam no host; venda autônoma e pagamento não existem |
| Segurança e dados | Sessões revogáveis, RBAC e chaves por escopo, RLS PostgreSQL em dados sensíveis, CSRF, idempotência, auditoria encadeada | Sem MFA; política de retenção/exportação por titular incompleta; restauração real não comprovada |
| Canais | Contas Instagram por organização, webhook assinado e ingestão idempotente de DMs em contatos, conversas e mensagens | Sem envio homologado; WhatsApp oficial não tem adaptador de entrada/saída; `messages/{id}/send` termina em 503 mesmo com a trava externa ligada |
| IA/SYNAPSE | Busca lexical com citações e rascunho generativo opcional para revisão humana; eventos criam corridas de agente e o portão permite ações internas com escopos e limites | Provedor IA não configurado por esta release; OpenClaw/Palantyr não implantado; agente sem lease de recuperação, reserva atômica de custo e avaliação contínua; nenhum envio autônomo |
| Agenda e produto | Calendário editorial, tarefas e catálogo com recorrência declarada | Sem agenda de reuniões/Google Calendar, cobrança recorrente, habilitação por plano ou provisionamento automático de cliente |
| Operação | Compose isolado, healthchecks, scripts de backup, restauração de ensaio e instalação com inventário | O estado desses mecanismos na Oracle não foi inspecionado nesta sessão |

Esses limites vêm principalmente de `main.py`, `instagram_ingest.py`, `agent_dispatch.py`, `agent_gate.py`, `ai_provider.py`, `synapse.py`, `infra/compose.yml` e `integrations/palantyr-v5/INTEGRATION_STATUS.md`. A home pública anuncia serviços além do que este CRM sozinho executa; não se deve tratar uma promessa do site como capacidade comprovada do produto.

## Débito técnico priorizado

| Prioridade | Débito e impacto | Critério de quitação |
| --- | --- | --- |
| P0 | **Desvio de release:** produção 0.5.1, código/CI 0.7.0. A equipe e os clientes não usam a implementação nova. | SSH `opc` funcional, inventário e backup verificado, deploy versionado, migrações, smoke real de dois papéis/tenants e rollback ensaiado; `/api/health` responde 0.7.0 antes de iniciar 0.8. |
| P0 | **Sem entrega oficial de mensagens:** o endpoint recusa com 503 e não existe conector WhatsApp. O produto não cumpre no CRM a principal promessa de automação de conversa. | Uma organização piloto recebe, responde e registra um evento real com credenciais próprias, consentimento/opt-out, janela/template, idempotência, tentativas limitadas e comprovante do provedor. |
| P0 | **Executor Palantyr ainda não opera no host:** corridas podem ficar em `planning` sem lease; orçamento soma custo depois, sem reserva concorrente. | Provisionamento isolado, lease/reclaim, teto de custo reservado de forma atômica, kill switch, avaliação e trilha completa; ensaio de queda/retomada. |
| P1 | **Visibilidade de produção e recuperação não demonstradas:** health externo prova só API/banco básico, não filas, backup restaurável, latência ou efeito no provedor. | Painel e alertas por fila/idade/erros/custo, rotina de restore em ambiente isolado com RTO/RPO medidos e smoke pós-deploy. |
| P1 | **Medição de paridade contraditória:** `scripts/paridade-site.py` ainda diz que DM Instagram não vira conversa, e `scripts/ordem-principal-matriz.py` contém linhas novas de modos de agente e linhas antigas com o mesmo conceito marcado ausente. Os percentuais 44%/59% não são confiáveis como estado atual. | Um registro único de capacidades com estado `código`, `CI`, `homologado`, `produção`, evidência e data; gerar as matrizes dele, sem vereditos duplicados. |
| P1 | **Segurança de conta e privacidade:** sem MFA, exportação/retenção por titular e política completa de eliminação. Credenciais compartilhadas nesta conversa devem ser rotacionadas antes de ampliar integrações. | MFA de administradores, fluxo auditável de exportação/retenção/eliminação, segredos rotacionados e nenhum valor sensível no Git/log. |
| P1 | **Venda modular ainda manual:** catálogo e propostas existem, mas contratação recorrente não concede módulos nem cria automaticamente um workspace isolado para o comprador. | Entitlements por plano com vigência e trilha, provisionamento idempotente por organização e reconciliação do estado comercial com o acesso; cobrança externa só após homologação própria. |
| P1 | **Cobertura concentrada:** 87% combinado local, mas `migrate.py` 68%, `provision_access.py` 69%, `ai_provider.py` 76% e `instagram_webhook.py` 77%. Não há teste de carga ou gate de cobertura no CI. | Testes de falha e concorrência nos caminhos de integração/migração, carga com metas explícitas, cobertura mínima por módulo crítico. |
| P2 | **Manutenção e documentação:** `main.py` (~57 KB), `services.py` (~42 KB) e `schemas.py` (~31 KB) concentram domínios; `docs/ARCHITECTURE.md` e `docs/ESTADO_DO_SISTEMA.md` são snapshots antigos; Graphify extrai `crm-ui.tsx` parcialmente. | Separar domínios por fronteira transacional, atualizar documentação viva e eliminar avisos do extrator sem sacrificar o build. |
| P2 | **Higiene da CI:** GitHub avisa sobre actions ainda baseadas em Node 20 e a migração futura de `ubuntu-latest`; há aviso de depreciação no testclient. | Atualizar actions compatíveis, fixar imagem de runner intencionalmente, revisar dependências de teste após validação. |

## Plano recomendado para a 0.8

**Objetivo da 0.8: um SYNAPSE piloto que conversa pelo WhatsApp oficial com controle humano e auditoria ponta a ponta.** A 0.8 não deve ser declarada pronta para todos os clientes apenas porque uma chamada à API do provedor funcionou.

1. **Fechar a implantação da 0.7.** Autorizar a chave pública fornecida para `opc` ou fornecer outra chave válida; inspecionar host e backup; publicar o artefato de `c5bd3b6`; executar migrações e smoke; provar restore e rollback. Registrar versão e evidências no release.
2. **Limpar as medidas antes de comparar progresso.** Consolidar a matriz de capacidades e separar `existe em código`, `passa na CI`, `homologado` e `ativo em produção`. Adicionar teste de contrato para os estados publicados pelo SYNAPSE e atualizar documentos antigos.
3. **Entregar um canal vertical completo.** Credencial WhatsApp por tenant cifrada; validação de webhook e dedupe por ID do provedor; ingestão em contato/conversa/mensagem; caixa operacional; outbox de envio com idempotência, política vigente do provedor, opt-out e observabilidade. Envio desligado até homologação com conta piloto.
4. **Ligar a autonomia de forma graduada.** Primeiro sugestão e escrita interna; depois resposta externa com aprovação/limites. O trabalhador Palantyr reclama corridas com lease recuperável, registra custo reservado e efetivo, recusa excesso e oferece handoff humano. Evals em PT-BR cobrem resposta sem fonte, dado pessoal, opt-out, janela fechada, replay e indisponibilidade do provedor.
5. **Liberar por evidência.** Testes PostgreSQL e navegador, cenários de dois tenants, falha/retry sem dupla entrega, teste de carga básico, métricas de fila e custo, piloto real monitorado, backup/restore e rollback. Só então ligar o canal por organização e publicar `/api/health` como 0.8.0.

Google Agenda/reuniões, cobrança/assinaturas e ativação automática de clientes são importantes, mas formam contratos externos próprios. Recomendo especificá-los durante a 0.8 e entregá-los em incrementos posteriores, evitando chamar uma integração não homologada de pronta.
