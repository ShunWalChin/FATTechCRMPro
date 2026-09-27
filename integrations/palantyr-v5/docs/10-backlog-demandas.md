# 10 · Backlog — todas as demandas da FAT Tech, com dono

Cada demanda tem um **dono no runtime** (agente OpenClaw), um **dono de construção** (swarm Ruflo,
quando há código) e uma **pessoa** que decide. Prioridade pelo Norte: 1 dinheiro entrando ·
2 dinheiro em risco · 3 entrega · 4 infra · 5 interno.

## Operação comercial

| Demanda | Prior. | Agente | Engenharia | Pessoa | Próximo passo |
|---|---|---|---|---|---|
| **Meta: 1 implantação do Ecossistema CRM por semana** | 1 | Marvin (placar), SDR (fila) | — | Wal | Marvin mede 0/1 toda quarta; 🔴 automático sem proposta aberta |
| Schellworth & Rodrigues — Google (CAPAG/Simples) + Meta (Simulador de CAPAG) | 1–2 | Tráfego, SDR, Cobrança (trava 6 meses) | simulador: fora deste repositório | Wal | Tráfego lê 2×/dia; lead sem retorno > 24h = escalada |
| Silva & Rocha Advogados — tráfego + funil | 1–2 | Tráfego, SDR, Cobrança | — | Wal | idem |
| Carpes & Mathias, LOGUS Retail — Meta Ads | 2 | Tráfego | — | Wal | recomendação com impacto em R$ no rascunho de campanha |
| Grupo WF / Wil 4.0 | 2 | SDR (herda o tom) | — | Wal | Wil segue como produto do cliente; SDR da FAT Tech usa o mesmo tom |
| Prospecção Golden Templates (Januária, empresas sem site) e curadoria Sentinela Hub | 1 | SDR (qualifica), Conteúdo (abordagem) | sites: swarm por nicho | Wal | lista vira contatos no CRM com origem `golden-templates` |
| Propostas abertas — Avance 360, Presente em Flor, Sabor & Massa | 1 | Cobrança (follow-up), Marvin | — | Wal | tarefa com próxima ação e data por proposta |
| Futura AI Conference 2026 | 2 | Tráfego, Conteúdo | dashboards: D-07 | Wal | incluir contas no ciclo LEITURA quando o Marvin delegar |
| Medjoul Agro (financiamento rural) | 3 | Marvin (prazo e gargalo) | — | Wal | projeto no CRM com marcos; Marvin cobra no SEMANAL |
| Parceria NextComm (Pedro Ventura) | 3 | Marvin | — | Wal | oportunidade no CRM com próxima ação |

## Entrega e conteúdo

| Demanda | Prior. | Agente | Engenharia | Pessoa |
|---|---|---|---|---|
| Resenha Barranqueira T1 (out–dez) | 3 | Conteúdo (pauta, perguntas, cortes) | — | Wal, Deivisson |
| Instagram @walfredonetto | 5 | Conteúdo | — | Wal |
| Conteúdo de clientes (Barra CT, Gata Malhada, Sabor & Massa) | 3 | Conteúdo | — | Iasmim / Wal |
| Vertente de posicionamento da Iasmim + vitrine januariamg.com.br | 3 | Conteúdo (apoio sob demanda) | — | **Iasmim** (sócia decide) |
| MoneyPrinterTurbo — vídeo PT-BR automatizado | 5 | Conteúdo (roteiros) | integração: swarm dedicado | Wal |
| Sites no ar: Minas Peças, Barra CT, Gata Malhada | 4 | Sentinela | correções: swarm | — |
| Gata Malhada — WooCommerce | 3 | — | swarm SPARC | Wal |
| WiseRH — SEO | 3 | Conteúdo | — | Wal |

## Engenharia (Ruflo) — ver `ruflo/swarms.md`

| ID | Demanda | Prior. | Onda |
|---|---|---|---|
| D-01 | E3 `execucao_interna` no portão | 1 | 3 |
| D-02 | reciclagem de corrida presa | 2 | 3 |
| D-03 | **WhatsApp API oficial (BSP)** | 1 | 4 |
| D-04 | E5 `execucao_externa` | 1 | 4 |
| D-05 | ponte MCP com `aidefence` | 3 | 3 |
| D-06 | testes de campanhas + rotas órfãs | 3 | 3 |
| D-07 | workflows n8n de borda como ferramentas MCP | 1 | 2 |
| D-08 | revisão do plano de limpeza do H1 | 1 | 0 |
| D-09 | observabilidade OTel + alerta de custo | 3 | 3 |
| D-10 | agenda + Google Calendar | 2 | 4 |

## Infra e sistema

| Demanda | Onda | Dono |
|---|---|---|
| Limpeza do H1 (walchat, medify, walhospeda) | 0 | Wal + runbook |
| Destino do Supabase avulso | 0 | Wal |
| CÓRTEX / PALANTYR_BRAIN montado só leitura no gateway | 1 | eng |
| Aposentar o blackboard do v2 (`_fila/`, `_squad_status/`, `_ordens/`) | 1 | Wal |
| JARVIS → Marvin (sucessão concluída; desligar resíduos no WSL) | 1 | Wal |
| Healthcheck externo do H1 pelo H2 | 2 | eng |

## Fora do escopo do Palantyr, de propósito

- **Impulse BPO** (CRM e playbook): é outro empregador; dado da Impulse não entra no CRM da FAT Tech.
- **Projetos pessoais** (mudança para a Espanha, busca de cidade): o Marvin não lê nem guarda.
