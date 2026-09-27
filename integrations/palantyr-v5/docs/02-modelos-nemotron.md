# 02 · Modelos — Nemotron-first, por nível de privacidade

## A regra

Todo dado de lead e cliente é **dado pessoal (LGPD)**. O nível do modelo é escolhido pelo que o
dado permite, não pelo que o modelo sabe fazer.

| Nível | Onde roda | Modelo | Para quê | Custo |
|---|---|---|---|---|
| **T0** | CRM | nenhum (regra) | compliance, pontuação explicada, SLA, radar | zero |
| **T1** | desktop RTX 4060 (`node_inference`) | `nemotron-3-nano:4b` (2,8 GB) | classificação, extração, resumo interno — dado não sai da FAT Tech | zero |
| **T2** | OpenRouter com `data_collection: deny` + `zdr: true` | **Nemotron 3 Super 120B-A12B** (Marvin) · **Nemotron 3.5 Lightning 30B-A3B** (squad) | orquestração, qualificação, copy, análise | centavos |
| **T3** | OpenRouter (mesma política) | Claude Sonnet 4.6 | fallback automático e texto crítico ao cliente se o Nemotron reprovar no eval | alto |

## Preços medidos (OpenRouter, 27/09/2026)

| Modelo | Entrada / 1M tokens | Saída / 1M tokens | Contexto | Provedores |
|---|---|---|---|---|
| Nemotron 3 Super 120B-A12B | US$ 0,080–0,085 | US$ 0,40–0,45 | 262 K | DekaLLM, DeepInfra |
| Nemotron 3.5 Lightning 30B-A3B | US$ 0,065 | US$ 0,18 | 1 M | 6 (inclui DeepInfra, CoreWeave) |
| Claude Sonnet (fallback) | ordem de US$ 3 | ordem de US$ 15 | — | Anthropic |

⚠ Os preços do OpenRouter mudam. O teto real é o `budget_month_cents` de cada agente no CRM e o
limite de gasto da chave no painel do OpenRouter — os dois precisam estar configurados.

## Custo mensal estimado (premissas explícitas)

| Agente | Turnos/dia | Tokens de entrada/turno | Modelo | US$/mês |
|---|---|---|---|---|
| Marvin | 5 ciclos + 14 heartbeats ≈ 20 | ~25 k | Super | ~1,6 |
| SDR | ~30 (hook + rede de segurança de 30 min) | ~15 k | Lightning | ~1,0 |
| Sentinela | ~70 rondas | ~10 k | Lightning | ~1,4 |
| Tráfego, Conteúdo, Cobrança | ~2 cada | ~30 k | Lightning | ~0,4 |
| Saídas somadas | — | — | — | ~1,5 |
| **Total Nemotron** | | | | **~US$ 6/mês** |
| Margem para fallback em Sonnet (10% dos turnos) | | | | +US$ 5–15 |

**Faixa realista: US$ 10–25/mês.** O mesmo volume inteiro em Sonnet ficaria em torno de US$ 150–300.
O número que importa para o Wal: o custo de modelo de operar a FAT Tech inteira é menor que o
ticket mensal de **um** cliente do Ecossistema CRM (R$ 499).

## Três alertas que decidiram o desenho

### 1. A API gratuita da NVIDIA não serve para produção
Os **termos da API trial** (build.nvidia.com) dizem, em resumo:
- só teste e avaliação interna, **não produção** (§1.4);
- a NVIDIA **usa o conteúdo enviado para melhorar seus modelos** (§3.3);
- é **proibido enviar dado pessoal**, financeiro ou de saúde (§4.3).

Consequência: o provedor `nvidia` do OpenClaw fica **fora** do `openclaw.json5` de produção, e o
`bootstrap-h1.sh` **aborta** se encontrar `NVIDIA_API_KEY` no ambiente de produção. A API trial
só aparece em `evals/ptbr`, com casos sintéticos. Produção usa o Nemotron **pago**, via OpenRouter,
com política de não coleta e retenção zero.

### 2. Português não está na lista do Nemotron 3 Nano
O card do `nemotron-3-nano` no Ollama lista inglês, alemão, espanhol, francês, italiano e japonês.
Por isso T1 começa em tarefas internas (classificar, extrair, resumir) e **nenhum modelo** assume
texto que o cliente lê sem passar em `evals/ptbr` (média ≥ 4,0 e zero crítico reprovado).
O mesmo vale para Super e Lightning — a nota deles em PT-BR é **[A MEDIR]** na Onda 1.

### 3. O Nano 30B não cabe na RTX 4060
`nemotron-3-nano:30b` tem 24 GB. Com 8 GB de VRAM, o Ollama descarregaria quase tudo para os 28 GB
de RAM, travando o desktop e entregando poucos tokens por segundo. O 4B cabe com folga.

## Roteamento no `openclaw.json5`

```json5
models: { providers: { openrouter: { params: { provider: {
  data_collection: "deny", zdr: true, require_parameters: true, sort: "price" } } } } },
agents: {
  defaults: { model: { primary: "openrouter/nvidia/nemotron-3.5-lightning",
                       fallbacks: ["openrouter/anthropic/claude-sonnet-4.6"] } },
  entries: { marvin: { model: { primary: "openrouter/nvidia/nemotron-3-super-120b-a12b",
                                fallbacks: ["openrouter/anthropic/claude-sonnet-4.6"] } } } }
```

`require_parameters: true` faz o OpenRouter recusar provedor que não suporte os parâmetros pedidos
(por exemplo, chamada de ferramenta) em vez de ignorá-los em silêncio.

**[A CONFIRMAR no primeiro boot]:** `openclaw models list --provider openrouter` para conferir os
IDs exatos `nvidia/nemotron-3-super-120b-a12b`, `nvidia/nemotron-3.5-lightning` e
`anthropic/claude-sonnet-4.6` no catálogo do dia, e se os provedores com ZDR suportam ferramentas
para os dois Nemotron. Se nenhum provedor ZDR suportar ferramentas para um deles, o agente cai no
fallback — o `SEMANAL` do Marvin mostra a taxa de fallback por agente.
