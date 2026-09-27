# fattech-crm-mcp

Ponte MCP (stdio) entre o **OpenClaw** e o **portão de agente do FAT Tech CRM Pro**
(`/api/v1/agent/*`). Uma instância por agente, cada uma com a chave e o `agent_id` daquele agente.
Inclui a **palantyr-probe**, sonda de saúde sem shell para o Sentinela.

## Ferramentas

| Ferramenta | Rota do CRM | Efeito |
|---|---|---|
| `crm_catalogo` | `GET /agent/tools` | leitura |
| `crm_fila` (`agente?`) | `GET /agent/{id}/queue` | leitura própria; outra fila requer `agent:observe` e `agents.read` |
| `crm_orcamento` | `GET /agent/{id}/budget` | leitura |
| `crm_corrida` | `GET /agent/runs/{id}` | leitura |
| `crm_reclamar_corridas` | `POST /agent/runs/claim` | move corridas para `planning` |
| `crm_abrir_corrida` | `POST /agent/runs` | abre corrida (replay-safe) |
| `crm_agir` | `POST /agent/act` | uma tentativa pelo portão; sempre grava passo |
| `crm_encerrar_corrida` | `POST /agent/runs/{id}/finish` | fecha com tokens e custo |
| `probe_alvos`, `probe_verificar` | alvos de `PROBE_TARGETS` | leitura (GET, sem redirecionamento) |

## Decisões de segurança

- `agent_id` de operação vem do ambiente, nunca de argumento.
- POST nunca é repetido automaticamente (duplicaria passo ou prenderia corrida); GET repete em
  408/425/429/5xx com espera exponencial.
- Conteúdo do CRM volta como `<<DADO_EXTERNO_CRM>>` com achados de injeção (PT/EN) à frente.
- Logs no stderr passam por `redactForLog` (CPF, CNPJ, cartão, e-mail, telefone, chaves).
- Limitador local de tentativas por minuto (`FATTECH_CRM_MAX_ACTS_PER_MINUTE`, padrão 30);
  o teto real continua sendo o do CRM.
- Nome de ferramenta validado (`kind.operacao`) e argumentos limitados a 32 KB antes da rede.

## Ambiente

| Variável | Obrigatória | Padrão |
|---|---|---|
| `FATTECH_CRM_BASE_URL` | sim | — (`http://api:8000` na rede do CRM) |
| `FATTECH_CRM_API_KEY` | sim | — |
| `FATTECH_CRM_AGENT_ID` | sim | — |
| `FATTECH_CRM_TIMEOUT_MS` | não | 20000 |
| `FATTECH_CRM_MAX_ACTS_PER_MINUTE` | não | 30 |
| `PROBE_TARGETS` (sonda) | não | vazio |

## Desenvolvimento

```bash
npm ci
npm test        # build + 20 testes (guard, cliente, servidor MCP real ↔ dublê do CRM, sonda)
```

O dublê `test/fake-crm.mjs` segue o contrato de `apps/api/fattech/agent_api.py` do Fattech-CRM.
Quando o contrato mudar lá, o dublê muda aqui no mesmo PR.
