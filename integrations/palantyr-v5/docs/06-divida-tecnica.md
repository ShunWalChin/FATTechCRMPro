# 06 · Dívida técnica — registro

Cada dívida tem dono, gatilho de pagamento e custo de não pagar. Severidade: **S1** bloqueia
go-live · **S2** pagar em 30 dias · **S3** pagar quando o gatilho acontecer.

| ID | Dívida | Sev. | Custo de não pagar | Pagamento | Dono |
|---|---|---|---|---|---|
| DT-01 | **H1 lotado e sem isolamento**: 71 contêineres de 9 projetos, 84% da memória, 3 projetos marcados para remoção ainda de pé | **S1** | OpenClaw entra num host sem folga; vizinho pesado derruba o CRM | `h1-cleanup-plan.sh` com dump verificado (Onda 0) | Wal |
| DT-02 | **Supabase avulso sem dono** (11 contêineres, 1,52 GB, ocupa 5432 em loopback) | S2 | maior economia do host parada por dúvida | confirmar dono; se resíduo, mesmo procedimento da DT-01 | Wal |
| DT-03 | **CRM e agentes no mesmo host** (ponto único de falha) | S2 | queda do H1 para vendas e operação juntos | fase 2: réplica fria do Postgres no H2 + restore ensaiado trimestral | eng |
| DT-04 | **Dois hosts com papéis confundidos na documentação** (briefing tratava H1 e H2 como um) | S2 | runbook errado no incidente | este repositório fixa H1=núcleo, H2=borda; atualizar o manual v4 | eng |
| DT-05 | **Ruflo em versões diferentes** (CRM fixa 3.41.2; Palantyr usa 3.46.1) | S3 | comportamento de hook/gate diverge entre repositórios | alinhar os dois na próxima release do CRM | eng |
| DT-06 | **Reciclagem de corrida presa**: `reclamadas_sem_retorno` é medido mas não reciclado | S2 | corrida abandonada fica em `planning` para sempre | D-02 (swarm Ruflo) | eng |
| DT-07 | **`read_only: true` do gateway não testado** no primeiro boot | S3 | pode exigir afrouxar no dia do deploy | testar em staging; se falhar, mapear caminhos e montar tmpfs em vez de afrouxar | eng |
| DT-08 | **Detector de injeção é heurística local** (regex PT/EN) | S3 | falso negativo em ataque criativo (o portão continua segurando) | D-05: `aidefence` com fallback | eng |
| DT-09 | **Sentinela acorda o modelo a cada ronda** | S3 | ~US$ 1,4/mês e ruído | condition watcher (`--trigger-script`) acorda só na falha | eng |
| DT-10 | **Estágios E3 e E5 do CRM pendentes** | S2 | agentes presos em `sugestao` (rascunho) | D-01 e D-04 | eng |
| DT-11 | **WhatsApp oficial ausente** (promessa em 25 páginas do site) | **S1 comercial** | passivo de venda nº 1 e envio externo impossível | D-03: contratar BSP | Wal |
| DT-12 | **IDs de modelo e suporte a ferramentas nos provedores ZDR não confirmados** | S1 | agente cai em fallback caro sem ninguém perceber | `openclaw models list` + eval na Onda 1; métrica de fallback no SEMANAL | eng |
| DT-13 | **PT-BR do Nemotron não medido** | S1 | SDR soa estrangeiro para o cliente | `evals/ptbr` na Onda 1 antes de ativar SDR | eng |
| DT-14 | **Gatilhos de evento não conferidos** contra o contrato do CRM | S2 | agente ativo que nunca acorda | `GET /api/v1/core/contract` antes de ativar | eng |
| DT-15 | **Canal do Marvin é WhatsApp não oficial** (Baileys) | S3 | banimento do chip dedicado | aceitar (volume mínimo); plano B: Telegram na mesma config | Wal |
| DT-16 | **Monitoramento sem alerta externo**: se o H1 inteiro cair, Sentinela e Marvin caem junto | S2 | ninguém avisa que ninguém avisa | healthcheck externo barato (ex.: n8n no H2 sonda o H1 e manda WhatsApp pela Evolution) | eng |
| DT-17 | **Workflows n8n de borda ainda não exportados** | S2 | Tráfego sem dados de Ads | D-07 | eng |
| DT-18 | **Blackboard em arquivos do v2** fica órfão | S3 | confusão sobre onde está a verdade | aposentar `_fila/`, `_squad_status/`, `_ordens/`; o CÓRTEX volta a ser só conhecimento | Wal |

## Dívidas herdadas do CRM que afetam os agentes

Do `ESTADO_DO_SISTEMA.md` (medido em 21/09): IA/Guardrail 7%, IA/Modo 0%, IA/Agente 29% — o
Palantyr v5 é exatamente o que tira esses números do chão, **desde que** E3/E5 (DT-10) e o
WhatsApp oficial (DT-11) sejam pagos. Campanhas sem teste e duas rotas órfãs entram em D-06.
