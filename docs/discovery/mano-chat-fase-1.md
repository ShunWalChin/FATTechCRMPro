# Mano Chat — Fase 1: conta Instagram por organização

Data: 16/09/2026 · Versão entregue: 0.5.1 · Situação: implementada, testada, não publicada ainda

A Fase 0 concluiu que a lacuna real não era o webhook — que já existia assinado, idempotente e com
outbox — mas a associação entre uma conta Instagram e uma organização. Esta fase fecha essa lacuna.

## As três decisões que estavam pendentes

O diagnóstico deixou três escolhas com o dono do sistema. Como nenhuma delas é irreversível e todas
travavam a fase, assumi-as e registro aqui o que decidi e com que fundamento. Qualquer uma pode ser
trocada numa migração seguinte.

**1. Tabela real, não `kind` em `records`.** Toda `kind` em `RESOURCES` ganha automaticamente
`GET /api/v1/{kind}`, que serializa a coluna `data` inteira. Uma credencial guardada assim seria
devolvida pela API. Além disso, duas coisas aqui só o banco garante: que duas organizações não
reivindiquem a mesma conta Instagram (restrição `UNIQUE`), e que o webhook encontre o dono antes de
existir dono na sessão.

**2. Chave do cofre em `/etc/fattechcrmpro.env`.** O arquivo já é 0600 e gerado no servidor. O banco
guarda só texto cifrado; um dump do banco sozinho não devolve token nenhum.

**3. Conta desconhecida é recusada com 404.** Guardar a mensagem de um terceiro que ninguém no
sistema possui é pior, sob a LGPD, do que descartá-la. A recusa fica auditada com o id da conta e
sem o corpo.

## O que passou a existir

| Tabela | RLS | Por quê |
|---|---|---|
| `instagram_accounts` | **não** | O webhook precisa descobrir o dono antes de haver dono na sessão. Uma política que usa `fattech.tenant_id` nunca responderia essa pergunta. Mesma classe de `users`, que também tem `tenant_id` sem RLS; o escopo é aplicado em toda consulta da aplicação. |
| `instagram_credentials` | **sim, forçada** | Só é lida dentro de um contexto de tenant. É o que carrega segredo, então é o que vai para `TENANT_TABLES`. |

Cifra: AES-256-GCM, `cryptography==46.0.5`, chave de 32 bytes em `FATTECH_CREDENTIAL_KEY`. O dado
adicional autenticado é `instagram:{tenant_id}:{account_id}`, de modo que uma linha copiada para
outra organização **falha ao decifrar** em vez de decifrar em silêncio.

## Endpoints

Todos sob `/api/v1/integrations/instagram`, escopo `integrations:read` para ler e
`integrations:write` mais papel administrativo para escrever.

| Método | Rota | O que faz |
|---|---|---|
| GET | `/accounts` | Lista as contas da organização. Nunca traz token. |
| GET | `/accounts/{id}` | Detalha uma conta. |
| POST | `/accounts` | Conecta. Recebe o token, guarda cifrado, devolve a conta sem ele. 409 se a conta já pertence a alguém; 503 se não há cofre. |
| PATCH | `/accounts/{id}` | Renomeia ou pausa. Exige `version`. |
| POST | `/accounts/{id}/token` | Troca o token. Exige `version`. |
| DELETE | `/accounts/{id}` | Desconecta e apaga a credencial de verdade. |

O que se vê de um token é a **impressão digital**: 16 caracteres hexadecimais de SHA-256. Serve para
confirmar que uma rotação trocou o valor; não serve para reconstruí-lo. A auditoria da rotação
guarda as duas impressões, anterior e atual, e nenhum token.

## Mudança de comportamento

O webhook `/api/public/webhooks/instagram` **deixou de entregar tudo ao tenant público**. Agora
resolve o dono pelo id da conta em `entry[].id` e recusa com 404 o que não reconhece. Uma entrega
que mistura contas de organizações diferentes também é recusada: escolher uma seria decidir no lugar
do dono.

Em produção isso é inerte hoje: `FATTECH_META_APP_SECRET` nunca foi passado ao contêiner, então o
webhook já respondia 503 a tudo. A partir desta versão as variáveis da Meta existem no `compose.yml`.

## Um defeito corrigido de passagem

O webhook nunca chamava `set_tenant`. Sob RLS forçada no PostgreSQL, as gravações de idempotência,
outbox e auditoria seriam recusadas pela política assim que o Instagram fosse ligado de verdade —
um defeito latente que só apareceria no primeiro evento real. Agora o contexto é definido logo após
a organização ser resolvida.

## Evidência

- `199 passed` contra PostgreSQL real, zero ignorados (`python scripts/validate-postgres.py`).
- Dez testes novos em `apps/api/tests/test_instagram_accounts.py`, entre eles uma varredura de
  **todos os bytes do arquivo do banco** procurando o token em claro — depois de conectar e
  rotacionar. Uma asserção sobre o corpo da resposta prova que aquela rota não vazou; a varredura
  prova que nenhuma escreveu o segredo em lugar nenhum.
- Um teste novo em `test_postgres.py` prova o contrato assimétrico: sem tenant na sessão a
  credencial some e o diretório de contas continua respondendo.
- `ruff check` limpo; `npm run build` limpo; `tsc --noEmit` limpo.

## Rollback

Sem `FATTECH_CREDENTIAL_KEY` no servidor, conectar uma conta responde 503 e nada é gravado. Sem
conta conectada, o webhook recusa e o CRM opera exatamente como na 0.5.0. Rollback é uma variável
ausente, não uma republicação. As duas tabelas são aditivas: nenhuma linha existente mudou.

## O que a fase 1 não fez

Não envia nada para a Meta. O worker continua entregando ao n8n, e `external_sends_enabled`
continua `false`. Trazer mensagem da Meta para dentro de `conversations` é a Fase 2.

## Para ligar no servidor

A chave do cofre é gerada no servidor pelo dono, e eu não a vejo. Em instalações novas,
`infra/provision_env.py` já a cria. Na instalação que existe, o comando é uma linha:

```bash
python3 -c "import base64,secrets;print('FATTECH_CREDENTIAL_KEY='+base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())" | sudo tee -a /etc/fattechcrmpro.env >/dev/null
```

Depois disso, `infra/deploy.sh` recria os contêineres com a variável. Perder essa chave torna os
tokens já guardados ilegíveis — que é precisamente o que se espera de um cofre.
