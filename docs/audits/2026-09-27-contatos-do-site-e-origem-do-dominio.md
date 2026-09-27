# Os contatos do site, e por que a correção não chegou ao ar

**Medido em 2026-09-27.** Pedido: *"todos os contatos do site devem ser para +55 35 9 9849-1017"*.

## O repositório já está correto — e há dias

| Medida | Repositório |
|---|---|
| Links `wa.me` | **159**, todos `wa.me/5535998491017` |
| Dados estruturados | 2× `"telephone": "+55-35-99849-1017"` |
| Telefone exibido | 7× `(35) 99849-1017` |
| Outro número em ponto de contato | **nenhum** |

Não há um único contato errado no código. O que o Oracle publica é byte a byte esse repositório —
`scripts/audit-site.py` verifica isso comparando o blob do Git com o que o servidor devolve.

## O que o cliente vê é outra coisa

| Host | contatos corretos | número fictício |
|---|---|---|
| `fattechcrmpro.64.181.178.125.nip.io` (Oracle) | **22** na home, 19 no `crm.html` | 0 |
| **`fattech.com.br`** | **0** | **22** |

O site comercial serve **22 CTAs de WhatsApp apontando para `+1-555-909-8369`**. O prefixo `555`
é reservado para ficção nos Estados Unidos: todo botão "falar no WhatsApp" do site aponta para um
número que não existe, e aponta assim desde antes deste trabalho.

Os dados estruturados também: `"telephone": "+1-555-909-8369"`. É o que o Google lê.

## A causa: o domínio não aponta para onde o deploy acontece

Do inventário da própria conta Cloudflare (`references/domains.md` da skill):

```
fattech.com.br  →  108.179.193.44   (cPanel / HostGator)
www             →  fattech.com.br
```

**O site comercial está hospedado no HostGator.** O Oracle publica o site corrigido em
`fattechcrmpro.64.181.178.125.nip.io`, e ninguém publica no HostGator. O nginx do H1 não tem
nenhum server block para `fattech.com.br` — só para `grana.fattech.com.br`.

Isso também explica o HTML antigo: URLs limpas (`/crm`, `/blog/`) são da transcrição em React já
substituída, e `/posiciona.html` responde **301** no domínio contra **200** no Oracle.

> O relatório de deploy de 24/09 registrou *"Site: https://fattech.com.br/ — HTTP 200"*. É verdade
> e é insuficiente: **200 mede disponibilidade, não identidade.** É por isso que o auditor de bytes
> compara conteúdo e não código de resposta.

## Duas saídas, e elas não são equivalentes

### A — apontar o domínio para o Oracle (recomendada)
O repositório volta a ser a única fonte, e todo deploy futuro publica o site automaticamente. O
auditor de bytes já valida o resultado.

### B — publicar no HostGator
Corrige hoje e deixa **duas verdades**: `release.py` conhece um destino, e cada release futura
exigiria uma segunda publicação manual — que é exatamente o que produziu esta divergência.

## A armadilha da opção A

Quatro subdomínios são **CNAME para a raiz** e seguiriam a mudança:

```
cpanel · webmail · whm · ftp   →  fattech.com.br
```

Apontar a raiz para o Oracle **derruba o webmail e o cPanel** junto. A ordem correta é:

1. **Primeiro** converter `cpanel`, `webmail`, `whm` e `ftp` de CNAME(raiz) para **A `108.179.193.44`**
2. Criar no nginx do H1 o server block de `fattech.com.br` e `www`, com certificado
3. **Só então** trocar `@` e `www` para `64.181.178.125`
4. Purgar o cache do Cloudflare
5. Rodar `python scripts/audit-site.py https://fattech.com.br` — ele prova byte a byte

**O e-mail não é afetado**: `mail`, `autoconfig` e `autodiscover` têm registro A próprio para
`108.179.193.44`, não CNAME. O MX continua intacto.

## O que eu não consegui fazer

O token da API Cloudflare tem allowlist de IP e recusa conexões desta máquina (erro 9109,
*"Cannot use the access token from location"*). O diagnóstico acima veio do inventário da conta e
de medição externa. A mudança de DNS precisa do painel, ou de liberar o IP no token.

## Dois números que NÃO devem mudar

`apps/web/public/lp/impulse-crm/index.html` tem `+55 11 99812-3456` em dois lugares, e os dois são
**demonstração de produto**: uma linha de tabela de clientes fictícia ("Mariana Costa, VIP,
R$ 8.400") e um payload de exemplo de webhook (`"evento": "lead.criado"`).

Trocar esses pelo número real seria pior que deixá-los: poria o telefone do dono num exemplo de
integração e faria parecer que existe uma cliente chamada Mariana Costa atendida nele.

## Correção ao ARCHITECTURE_MAP: são três hosts, não dois

O Palantyr v5 fixa H1 (núcleo) e H2 (borda). O inventário mostra que **o n8n está num terceiro
servidor**:

| Serviço | Host |
|---|---|
| CRM, agentes | **64.181.178.125** (H1) |
| Evolution API, NPM | **163.176.163.204** (H2) |
| **n8n** | **69.6.222.167** |
| Site comercial, e-mail | **108.179.193.44** (HostGator) |

A DT-04 do Palantyr ("dois hosts com papéis confundidos na documentação") é maior do que registrada:
são quatro destinos, e o runbook de incidente precisa dizer qual.
