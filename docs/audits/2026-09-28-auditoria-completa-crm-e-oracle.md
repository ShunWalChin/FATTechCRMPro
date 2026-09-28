# Auditoria completa: o CRM e o servidor Oracle

**Medido em 2026-09-28.** Pedido: *"tudo pronto? Avalie tudo / Todo o CRM / E todo o servidor
oracle tbm"*.

**Resposta curta: não.** O que está construído está sadio e medido. O que falta não é código —
é publicação, uma credencial e uma decisão de DNS. As cinco lacunas estão no fim, com o custo de
cada uma.

---

## 1. O repositório

| Medida | Valor |
|---|---|
| HEAD | `22b39a1` |
| Árvore de trabalho | 0 arquivos alterados |
| Testes de API | **400 passando, 12 pulados, 0 falhando** (194 s) |
| Typecheck do web | limpo |
| Rotas | **133**, das quais **131 exercidas por teste (98%)**, 118 chamadas por tela (89%) |
| Rotas órfãs | **0** — nenhuma sem tela, sem teste e sem documento |
| Rotas sem teste nenhum | **0** |
| Paridade de mercado | **173 de 349 (60%)**; IA 57%, PIPELINE 82%, SEGURANÇA 66%, CANAIS 34% |
| Grafo de conhecimento | 120 nós / 84 arestas em 12 arquivos → **168 nós / 122 arestas** exportados para a API |

## 2. O que roda no Oracle (64.181.178.125)

| Medida | Valor |
|---|---|
| Uptime | 12 semanas e 6 dias |
| Memória | 12,9 GB de 22,4 GB (58%), **9,5 GB disponíveis** |
| Disco | 91 GB de 183 GB (50%), 93 GB livres |
| Carga | 4,89 / 2,96 / 2,61 em 4 vCPU |
| Contêineres | **71 rodando**, 88 existentes, **0 unhealthy, 0 reiniciando** |
| Pilha FAT Tech | 6 contêineres, os 4 de serviço **healthy** há 19 h |
| nginx | 27 `server_name`, `nginx -t` **ok** |
| Certificados | 14 ativos, o mais próximo do fim em **30 dias** (`medify`), renovação por `certbot-renew.timer` |
| Backup | `fattechcrmpro-backup.timer` ativo, **último em 28/09 04:42**, 189 KB com `.sha256` ao lado |

A carga de 4,89 em 4 vCPU merece registro: é o host inteiro, com ~70 contêineres de projetos não
relacionados. A pilha do CRM consome pouco — os doze maiores consumidores de memória são todos de
outros projetos, e o maior deles (`supabase_analytics_wal_chat_prod`, 622 MB) usa mais que os quatro
contêineres do CRM somados.

### Lixo acumulado, medido e não removido

`docker system df` reporta **23,25 GB de build cache recuperável** e **11,58 GB em imagens**, entre
elas **47 imagens `fattechcrmpro-*`** de releases antigas. Com 93 GB livres isso não é urgência, e
**não removi nada**: a regra de zero destruição vale aqui. `docker builder prune` resolveria os
23 GB sem tocar em contêiner nenhum, e é decisão sua.

## 3. O banco em produção

| Medida | Valor |
|---|---|
| Migrações aplicadas | `0001`…`0010`, **todas as dez** |
| RLS forçada | **16 de 23 tabelas** — exatamente as 16 de `TENANT_TABLES` |
| Papel da aplicação | `fattech_app`, `superuser=False`, `bypassrls=False`, **não é dona de tabela** (dona é `fattech_owner`) |
| Trilha de auditoria | **301 linhas, seq 1..301, 0 sem selo** |
| Reconferência do encadeamento | `íntegra=True`, **301 de 301 conferidas, 0 faltando, 0 problemas** |
| Registros de negócio | 81 em 10 domínios (22 contatos, 18 negócios, 11 conversas, 11 mensagens) |
| Organizações | 1 (`fattech`), 10 usuários |

As sete tabelas fora da RLS: `schema_migrations` e `tenants` não têm coluna `tenant_id`; as cinco
de identidade (`users`, `login_sessions`, `api_keys`, `rate_limits`, `instagram_accounts`) são lidas
**antes** de haver tenant na sessão — uma política que usa `fattech.tenant_id` nunca responderia a
pergunta "de quem é este e-mail?". O isolamento delas é da aplicação, não do banco. Isso já estava
documentado, mas o `ARCHITECTURE.md` ainda dizia **quatro** tabelas com RLS quando são dezesseis, e
o `DATA_MODEL.md` nomeava três das cinco de identidade. Os dois foram corrigidos com o número medido
e o denominador.

## 4. O motor central

`event_outbox.status` está em `pending` nas 301 linhas, e **isso não é atraso**: a linha do outbox é
o log do evento, e o consumo é registrado em `core_deliveries`, uma entrega por papel. Medir o
outbox mediria a coisa errada e acusaria 301 de fila onde não há fila nenhuma.

| Medida | Valor |
|---|---|
| Entregas `bi` | **301 completed** |
| Atrasadas (`pending` com `available_at` no passado) | **0** |
| Presas (`processing` com lease vencido) | **0** |
| `dead_letter` | **0** |
| Falhas registradas | **0** |
| Batimento dos quatro trabalhadores | `bi`, `messaging`, `openclaw`, `scheduler` — todos vistos há **menos de 3 s** |
| Fatos de evento / eventos processados | 301 / 301 |

`messaging` e `openclaw` têm **zero entregas**, e isso é a trava de rollback funcionando:
`messaging` só recebe `messages.received` de origem interna ou webhook, e `openclaw` só recebe os
tipos que **algum agente ativo observa**. Não há agente ativo. Nada foi entregue porque nada devia
ser entregue.

## 5. Os agentes

Sete agentes cadastrados. **Todos `paused`, todos em `sugestao`.** E dois números que importam mais:

| Agente | ferramentas | gatilhos |
|---|---|---|
| SYNAPSE · Copiloto comercial | **0** | — |
| Marvin | 16 | **—** |
| SDR | 12 | `contacts.created`, `messages.received`, `contacts.qualification_pending` |
| Tráfego Pago | 7 | — |
| Conteúdo | 8 | `content_ideas.created` |
| Cobrança & Higiene | 9 | — |
| Sentinela | 4 | — |

**Cinco dos sete não têm gatilho nenhum.** Um agente sem gatilho nunca acorda por evento, mesmo
ativo — ele parece configurado e não é. O Marvin, que é o agente do briefing das 08h, é um deles:
tem as dezesseis ferramentas e nenhum gatilho. Ativar a operação exige preencher isso antes.

**0 corridas, 0 passos.** O núcleo de agentes nunca processou um evento em produção.

### As seis chaves órfãs

| Chave | revogada | expira | escopos |
|---|---|---|---|
| Verificacao 1789237744 | **sim** | 2026-12-11 | 35 |
| OpenClaw · Marvin | não | 2026-12-26 | 14 |
| OpenClaw · SDR | não | 2026-12-26 | 12 |
| OpenClaw · Tráfego Pago | não | 2026-12-26 | 8 |
| OpenClaw · Conteúdo | não | 2026-12-26 | 9 |
| OpenClaw · Cobrança & Higiene | não | 2026-12-26 | 8 |
| OpenClaw · Sentinela | não | 2026-12-26 | 6 |

As seis estão **ativas e inutilizáveis**: o script gravou o arquivo de token depois do `commit`, a
gravação falhou por permissão, e o segredo se perdeu com o processo. Os seis usuários-agente
correspondentes têm papel `root`. Uma chave `root` ativa cujo token ninguém tem não é um risco de
uso indevido — é um risco de inventário: ela aparece na lista de acessos vivos e não corresponde a
nada. O script já foi corrigido (grava antes do commit, e `--revogar-antigas`), mas **a execução
depende de permissão de escrita remota** que este ambiente recusou.

## 6. Os acessos web

| Endereço | HTTP | veredicto |
|---|---|---|
| `https://fattechcrmpro.64.181.178.125.nip.io/` | 200 | site institucional |
| `…/crm` | 200 | aplicação |
| `…/api/v1/health` | 200 | `{"status":"ok","version":"0.7.0","environment":"production"}` |
| `…/api/openapi.json` | 200 | esquema |
| `https://grana.64.181.178.125.nip.io/` | 200 | Grana OS |
| `https://claw.64.181.178.125.nip.io/` | **200 — e vazio** | **não é o OpenClaw** |

O `claw.*` devolve 200 com corpo vazio, **exatamente igual a um host inexistente que eu inventei
como controle** (`inexistente-xyz.64.181.178.125.nip.io`). É o `server _` do nginx respondendo por
qualquer nome `nip.io`. Não existe contêiner de gateway: `docker ps` mostra apenas
`walhospeda-gateway`, de outro projeto.

> Esta é a segunda vez neste projeto que um 200 mentiu. **200 mede disponibilidade, não identidade** —
> e a forma de não cair nisso é a que usei aqui: medir um host que não devia existir e comparar.

`grana.fattech.com.br` tem server block no nginx (`/etc/nginx/conf.d/grana.conf`) e **nenhum
registro DNS**. O certificado que existe cobre só `grana.64.181.178.125.nip.io` — confirmado no SAN.

## 7. O site comercial continua errado

| Host | contatos corretos | número fictício |
|---|---|---|
| Repositório (`apps/web/public`) | **138 links `wa.me/5535998491017`** | 0 |
| Oracle | 66 de 66 arquivos byte a byte iguais ao repositório | 0 |
| **`fattech.com.br`** | **0** | **22 `wa.me/15559098369`** + `"telephone": "+1-555-909-8369"` |

Nada mudou desde ontem, e não muda sem DNS: o domínio aponta para o HostGator
(`108.179.193.44`), onde ninguém publica. O plano de cinco passos está em
[`2026-09-27-contatos-do-site-e-origem-do-dominio.md`](2026-09-27-contatos-do-site-e-origem-do-dominio.md),
com a armadilha nomeada — `cpanel`, `webmail`, `whm` e `ftp` são CNAME para a raiz e cairiam junto.

### Um achado do auditor de bytes

O auditor acusou `script.js` divergente do repositório oficial **sem correção declarada**. A
divergência é real e desejada: nosso `script.js` registra o lead em `/api/v1/public/leads` com
`keepalive: true` antes de abrir o WhatsApp. O que faltava era a **declaração** — e faltar
declaração é o alarme funcionando, não falhando. Declarada em `docs/site-patches.json`, o auditor
fecha com *"Nenhum problema: cada byte servido é o byte do arquivo, e cada arquivo é o do original"*.

O `keepalive` merece a linha que ganhou na declaração: sem ele o navegador cancela a captura quando
a aba do WhatsApp assume o foco — ou seja, justamente no caso comum.

---

## As cinco lacunas entre isto e operação real

1. **Produção está dois commits atrás do HEAD.** `RELEASE` = `fe9bc4f`, HEAD = `22b39a1`. Confirmei
   pela imagem, não pelo git: `compliance.decidir_envio`, `reciclar_presas` e `event_catalog` **não
   importam** no contêiner de produção, e o catálogo de lá tem **45 executáveis contra 46** —
   `messages.send` não despacha. O E5, a reciclagem e o catálogo de 108 eventos existem, passam nos
   testes e **não estão no ar**. Custo: um `release.py` + `install-release.sh`.
2. **Seis chaves `root` ativas sem token.** Bloqueado em permissão de escrita remota.
3. **O OpenClaw nunca subiu.** Falta a chave do OpenRouter, o bridge compilado em contêiner (o Node
   do host é v22.22.2; o bridge exige ≥ 24.16) e o server block de `claw.*`. Sem isso o núcleo de
   agentes é uma porta trancada com a fechadura pronta.
4. **Nenhum agente tem gatilho utilizável.** Cinco dos sete com zero, o Marvin entre eles.
   Não depende de host nem de credencial — depende de decidir o que cada agente observa.
5. **`fattech.com.br` serve 22 CTAs para um número que não existe.** É a única lacuna que custa
   dinheiro hoje, a cada visitante.

E duas que não bloqueiam: Tailscale ausente (ADR-008), e `grana.fattech.com.br` sem DNS.

## O que está pronto de verdade

O CRM em produção responde, sela cada linha da trilha, reconfere as 301 sem um problema, força RLS
nas dezesseis tabelas que declara forçar, roda os quatro trabalhadores com batimento de segundos,
drena as 301 entregas sem uma carta morta, faz backup diário verificado por hash e serve 66 arquivos
byte a byte iguais ao repositório. **Isso não é pouco e não é o suficiente**: é uma base sadia com
cinco coisas por cima dela, e a primeira delas é publicar o que já passou nos testes.
