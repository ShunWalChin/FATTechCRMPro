# Operação do FAT Tech CRM Pro

Estado publicado e evidências: [release de 11/09/2026](releases/2026-09-11.md).
Hostname inicial: `fattechcrmpro.64.181.178.125.nip.io`; ingresso em `infra/nginx.oracle.conf`.

Esta aplicação usa serviços, rede, banco e volumes exclusivos. O arquivo `infra/compose.yml`
nunca utiliza a rede do host nem volumes de aplicações vizinhas. Next.js e API escutam
somente em loopback do host. PostgreSQL fica acessível apenas na rede Docker dedicada.

## Desenvolvimento no Windows

1. Node.js 24 e Python 3.12 com uv.
2. `npm ci`.
3. Instalar API: `uv venv --python 3.12 .venv` e
   `uv pip install --python .venv/Scripts/python.exe -r apps/api/requirements.txt`.
4. Definir `FATTECH_BOOTSTRAP_PASSWORD` com uma senha própria de 12 ou mais caracteres.
5. `./scripts/dev.ps1 -Seed` inicia API e dados demonstrativos explicitamente.
6. Em outro terminal, `npm run dev`. Site em `http://localhost:3000`; CRM em `/crm`.

Em Linux, o contrato equivalente é `PYTHONPATH=apps/api`, ambiente development,
`python -m fattech.migrate`, `python -m fattech.seed --demo`,
`uvicorn fattech.main:app --host 127.0.0.1 --port 8000` e `npm run dev`.

## Primeiro provisionamento Oracle

- Auditar portas, CPU, memória, disco e aplicações existentes antes de instalar.
- Copiar somente arquivos versionados para `/opt/fattechcrmpro`.
- Gerar segredos **no servidor** com `sudo python3 infra/provision_env.py --origin URL_HTTPS --email EMAIL_DO_ADMIN`.
- Guardar `/etc/fattechcrmpro.env` com permissão `0600`; o script se recusa a sobrescrever.
- Executar `sudo bash infra/deploy.sh`. A migração usa usuário proprietário e cria permissões
  para o usuário runtime `fattech_app`, que não é superusuário nem dono de tabela.
- Validar API, login, isolamento, lead público, backups e interface antes de apontar DNS.
- A senha inicial fica somente no arquivo protegido. Entregar ao proprietário por canal privado
  ou permitir que ele consulte o arquivo no servidor. Nunca copiar para README ou commits.

## Variáveis de envio e destino externo

`FATTECH_EXTERNAL_SENDS_ENABLED` nasce em `false` e é a trava persistente de modo seguro: mesmo
quando a avaliação de compliance libera a mensagem, nenhum efeito externo sai enquanto ela estiver
desarmada. Armar exige decisão explícita do operador, depois de existir um adaptador homologado.

`FATTECH_BLOCKED_TERMS` aceita termos separados por vírgula. A comparação normaliza o texto e remove
caracteres invisíveis, de modo que um espaço de largura zero entre letras não contorna a lista.

`FATTECH_N8N_OUTBOUND_URL` passa por checagem de faixa reservada quando é um endereço literal, e o
worker recusa iniciar se o host resolver para rede privada ou reservada.

## Migrações e atualização

As migrações são explícitas, não ocorrem implicitamente no início da API em produção.
Esta versão acrescenta a migração `0002`, que cria o funil padrão de cada organização e grava
`pipeline_id` nas oportunidades existentes, sem alterar a versão nem o `updated_at` desses registros.
Rode `python -m fattech.migrate` com o usuário proprietário antes de liberar tráfego: a API de
produção recusa iniciar sem a marca `0002`, porque toda escrita de oportunidade depende de um funil.
Antes de atualizar, execute `infra/backup.sh`, registre commit e imagens anteriores,
construa as novas imagens e valide antes da troca de tráfego. Não execute `down -v`.

Na estação de engenharia: `git add .`, `python scripts/inventory.py`,
`git add docs/FILE_INVENTORY.csv` e commit. O inventário calcula SHA-256 dos blobs
do Git, com finais de linha canônicos. `python scripts/release.py` exige árvore limpa
e usa `git archive HEAD`, evitando diferenças entre o commit e o pacote publicado.

O schema inicial é a base versionada. Alterações futuras exigem nova migração incremental,
teste de compatibilidade e plano de reversão. `create_all` não atualiza colunas existentes.

## TLS, DNS e integração ao site

O arquivo `infra/nginx.conf.example` é o contrato do ingresso para domínio próprio.
Um certificado válido e o controle do DNS são necessários para o corte definitivo.
Se um túnel Cloudflare dedicado já existir, conservar suas rotas e criar uma rota exclusiva
para o novo serviço. Não substituir ingress de clientes nem alterar segurança global do host.

O site renderiza no servidor e encaminha `/api/v1` ao mesmo backend privado. A captação pública
resolve o tenant por configuração, e não por campo enviado pelo visitante. Artigos e landing pages
têm URLs permanentes e redirecionamentos das versões `.html`.

## Backup e restauração

`sudo bash infra/backup.sh` gera dump PostgreSQL custom e SHA-256, com permissões privadas.
Os arquivos ficam em `/var/backups/fattechcrmpro`. Instalar apenas as duas unidades systemd
`fattechcrmpro-backup.service` e `.timer` para agendamento diário. Retenção e cópia fora do
servidor devem ser configuradas conforme o volume de dados e o armazenamento disponível.

Restaurar primeiro em **outro banco vazio**, com `pg_restore --exit-on-error --no-owner`.
`sudo bash infra/verify-backup.sh /var/backups/fattechcrmpro/ARQUIVO.dump` confere hash,
restaura num banco temporário exclusivo, verifica owner/migração/RLS e remove somente esse banco.
Executar migrações/grants, smoke e testes de acesso antes de promover. Validar a restauração
é obrigatório: existência de um arquivo não prova recuperação. Registrar data, tamanho,
hash, resultado do restore e tempo medido; não inventar RPO/RTO.

## Diagnóstico

- `/api/health`: prontidão da API e banco.
- `docker compose ... ps`: saúde dos serviços.
- `docker compose ... logs --tail 100 api worker web`: logs limitados.
- `/api/v1/audit`: ações autorizadas com ator e escopo.
- `/api/v1/events`: eventos duráveis e estado de processamento.

Logs não devem conter senhas, tokens, cabeçalhos de autorização ou texto integral de mensagens.
Falhas externas permanecem visíveis. Uma resposta ambígua de envio nunca vira reenvio cego.

## Controles operacionais

Integrações externas e agentes não ganham credenciais por herança de outro CRM. Cada conta
precisa ser configurada e validada, com orçamento e permissões próprios. O n8n consome APIs
e eventos; não substitui a transação de negócio. Dados demonstrativos são exclusivos do
desenvolvimento e não são carregados automaticamente em produção.
