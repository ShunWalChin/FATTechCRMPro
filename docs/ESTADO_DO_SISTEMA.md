# Estado do sistema — 2026-09-21

Medido, não lembrado. Cada número abaixo sai de um script que você pode rodar agora:

```bash
python scripts/ordem-principal-matriz.py   # paridade de engenharia com o mercado
python scripts/paridade-site.py            # o que o site vende × o que o sistema entrega
python scripts/inventario-funcoes.py       # toda função e quem a usa
```

Versão `0.5.1`, 8 migrações versionadas, 117 rotas, 21 domínios, 20 tabelas, 22 telas.
7.465 linhas de API, 5.066 de teste de API, 2.216 de web, 1.445 de teste de navegador.

---

## Os dois números, e por que eles discordam

| Medida | Resultado | O que significa |
|---|---|---|
| **Paridade de engenharia** | **57%** — 156 TEM, 68 PARCIAL, 111 AUSENTE de 335 | quanto do que um HubSpot/Pipedrive/RD faz, este CRM faz |
| **Paridade comercial** | **44%** — 4 TEM, 7 PARCIAL, 6 AUSENTE de 17 | quanto do que o site já cobra, o sistema cumpre |

A distância entre os dois é o resumo do problema: **o sistema é mais forte do que o site vende em
algumas áreas, e muito mais fraco em outras — e são áreas diferentes.**

O que o sistema faz melhor é contrato, qualificação de lead e funil. O que o site anuncia em 25
páginas é WhatsApp API Oficial e Agentes Neurais. Nenhum dos dois é o outro.

---

## Onde o sistema está forte

| Subgrupo | Prontidão | O que existe |
|---|---|---|
| **COMERCIAL/Contratos** | **96%** | modelo com variáveis, revisão com o texto de cada versão, cadeia de aprovação, renovação, assinatura que recusa com 503 em vez de simular |
| **COMERCIAL/Qualificação** | **87%** | pontuação que devolve todo critério com o que leu e o que esperava |
| **PIPELINE (envio)** | **82%** | idempotência, outbox transacional, worker com carta morta, compliance antes de tudo |
| **COMERCIAL/Leads** | **81%** | fila com SLA medido no servidor, distribuição por menor carga, ciclo de vida separado do status |
| **COMERCIAL/Kanban** | **80%** | funil configurável, requisitos por etapa, radar de risco por tempo parado |
| **PARIDADE/Vendas** | **80%** | previsão ponderada, motivo de perda obrigatório, metas por vendedor |
| **CLIENTES/Cadastro** | **78%** | campos próprios da organização, deduplicação, fusão com referências repontadas |

Isso não é pouco. **Contratos a 96% é melhor que o Pipedrive**, que não tem ciclo de contrato
nativo. A qualificação explicável — cada critério com o valor lido — não existe em nenhum dos três
concorrentes: eles devolvem um número.

E a base é sólida de um jeito que não aparece em demonstração: RLS forçada no banco com role sem
`BYPASSRLS`, concorrência otimista com 409 em toda escrita, trilha inalterável e agora encadeada
por hash, verificável por terceiro.

## Onde o sistema está fraco

| Subgrupo | Prontidão | O buraco |
|---|---|---|
| **IA/Modo** | **0%** | não há modo de operação de agente: nem sugestão, nem copiloto, nem execução |
| **IA/Guardrail** | **7%** | nenhuma checagem de entrada ou saída de modelo |
| **CANAIS/Email** | **8%** | não há e-mail: nem conexão, nem envio, nem caixa, nem SPF/DKIM |
| **PARIDADE/Inteligência** | **14%** | sem copiloto, resumo de conversa, enriquecimento, previsão por modelo, churn |
| **IA/Agente** | **29%** | `agents` guarda persona, autonomia e orçamento; **não há executor** |
| **CLIENTES/Financeiro** | **30%** | lançamento manual; sem cobrança, conciliação ou recorrência |
| **COMERCIAL/Clientes** | **37%** | cliente é `contacts.status='customer'`, não entidade: sem LTV, renovação, churn |
| **CANAIS/WhatsApp** | **41%** | compliance conhece janela de 24h e template; **nada é entregue à Meta** |

As 111 ausências se concentram: CANAIS 24, CLIENTES 22, PARIDADE 22, IA 19, COMERCIAL 19, e só 5
entre segurança e pipeline. **O sistema é bem construído e estreito** — falta superfície, não
qualidade.

---

## O que o site cobra e o sistema não entrega

Ordenado pelo tamanho da exposição — em quantas páginas a promessa aparece:

| Promessa publicada | Páginas | Situação |
|---|---|---|
| **WhatsApp API Oficial da Meta** | **25** | **AUSENTE** — compliance conhece a janela; não há entrega à Meta |
| CRM Kanban autônomo | 16 | PARCIAL — o quadro existe, nada se move sozinho |
| Integração com Instagram | 11 | PARCIAL — conta e webhook resolvem o dono; mensagem não vira conversa |
| Agentes Neurais de IA com RAG | 4 | **AUSENTE** — sem executor e sem RAG |
| Fecha vendas enquanto você dorme | 2 | **AUSENTE** — nada comercial acontece sem uma pessoa |
| Disparo em massa via API oficial | 2 | **AUSENTE** — campanhas são cadastro |
| Agenda automática via IA | 2 | **AUSENTE** — não há agenda nem calendário |
| Vendas e cobranças no chat | 1 | **AUSENTE** — sem cobrança nem envio |

**WhatsApp API Oficial em 25 páginas é o passivo comercial número um.** É a promessa mais repetida
do site e é a única que, sozinha, destravaria quatro linhas desta tabela: disparo em massa, kanban
autônomo de verdade, "fecha vendas enquanto você dorme" e a metade do que "Agentes Neurais"
significa para quem lê.

Do outro lado, duas promessas entraram como TEM ontem: conteúdo integrado ao CRM e calendário
editorial. São da vertente Posiciona e já estão inteiras.

---

## Saúde do que existe

```
Rotas chamadas por alguma tela   107 de 117  (91%)
Rotas exercidas por algum teste  111 de 117  (95%)
Rotas descritas na API.md         80 de 117  (68%)

290 testes de API passam, 12 pulados, nenhum vermelho. 42 testes de navegador passam.
```

Duas rotas órfãs — nenhuma tela, nenhum teste, nenhuma linha de documento:
`GET /api/v1/core/contract` e `POST /api/v1/knowledge/{id}/index`. A segunda é antiga e ninguém
chama. Campanhas têm tela e zero teste: quebram em silêncio na próxima refatoração.

Órfã significa "ninguém explicou para que serve", não "pode apagar".

---

## O que eu faria, em ordem

Isto é recomendação, não plano aprovado. A ordem de engenharia original coloca IA na Onda 6; eu
inverteria, e o motivo é comercial, não técnico.

**1. WhatsApp API Oficial.** Fecha a promessa de 25 páginas e destrava quatro outras. Todo o
caminho já existe — compliance, outbox, worker, janela, template, opt-out. O que falta é o último
salto: entregar ao provedor. **Depende de contratar um BSP, e de você decidir sobre o número.**

**2. O executor de agente em modo sugestão e interno.** Tira IA de 20% sem depender de provedor
nenhum e é exatamente o que o OpenClaw vai operar. O desenho está em `ARCHITECTURE_MAP.md`.

**3. Agenda.** Três ausências de paridade num item só (agenda, Google Calendar, agendamento
público), e é a pergunta que todo cliente de serviço faz na primeira demonstração.

**4. Cliente como entidade.** Hoje cliente é um status em `contacts`. Isso trava LTV, renovação,
expansão e churn — sete ausências de uma vez, e é o que separa CRM de agenda de contatos.

**E-mail eu deixaria por último**, apesar dos 8%. É caro (SPF/DKIM/DMARC, reputação de domínio,
caixa, threads) e não é o que a FAT Tech vende. Vender WhatsApp e entregar e-mail seria resolver o
problema errado muito bem.

---

## O que não está medido aqui

- **O estado dos dois servidores.** Não há SSH nesta sessão. O inventário de contêineres é de
  2026-09-15.
- **O site em produção.** O repositório está corrigido; o que está no ar é o build anterior, com
  69 links de WhatsApp mortos e o número errado.
- **Desempenho sob carga.** Nenhum número deste documento fala de latência ou concorrência real.
