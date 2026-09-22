# Manual de Execução — PALANTYR v4

> Convertido de `docs/sources/Manual_Execucao_v4.docx`, que é o original e continua no repositório.
> Esta versão existe para ser pesquisável e diffável; em caso de divergência, o .docx manda.

**Este manual não descreve o FAT Tech CRM Pro.** Ele descreve a infraestrutura Palantyr — n8n,
Evolution API, Doppler, Ollama, MCP Gateway — que roda em outro host (163.176.163.204) e atende
a operação de tráfego da agência. O que dele foi trazido para o CRM está registrado em
`docs/knowledge/posiciona-operacao.json` e implementado em `apps/api/fattech/audit_chain.py`.

FAT TECH
//  G R O W T H   H U B  //
MANUAL DE EXECUÇÃO
PALANTYR v4 sobre a infraestrutura FAT Tech
Passo a passo operacional com comandos reais
COMPANHEIRO OPERACIONAL DO BLUEPRINT
PALANTYR_BRAIN / 01_FATTECH_CORE / manual_execucao_v4.docx
Walfredo Figueiredo Neto  //  CEO
Januária — Minas Gerais — Brasil
Maio de 2026  //  v1.0

### Como usar este manual

Este documento é o companheiro operacional do blueprint Palantyr v4. O blueprint responde POR QUÊ e O QUÊ. Este manual responde COMO, em qual ordem, em qual host e com quais comandos. Foi construído para ser seguido linha a linha, do alto ao baixo, sem improvisação.
Princípios de leitura
Cada passo declara: objetivo, pré-requisitos, host de execução, comandos exatos, validação e rollback (quando aplicável).
Os comandos são reais. Copie e cole. Substitua apenas variáveis explicitamente marcadas entre chaves {ASSIM}.
Não pule a validação. Cada passo só está concluído quando a validação retorna o esperado. Pular validação é convidar falha em produção.
O host está sempre declarado. Tarja superior de cada passo informa onde executar: Oracle Cloud, WSL Ubuntu, Windows PowerShell, navegador, etc.
Comandos destrutivos têm aviso. Antes de executar, ler até o fim do passo.
Hosts da operação FAT Tech
Apelido
Onde está
Quando usar
ORACLE
Oracle Cloud ARM64 — IP 163.176.163.204
Toda configuração de Docker, n8n, Evolution API, Postgres, deploy de serviços
WSL
WSL Ubuntu (Windows 11 + RTX 4060)
Dev local, Ollama, Git, build de skills, Claude Code
WIN
PowerShell ou cmd Windows nativo
Casos pontuais — instalação de Claude Desktop, configuração de drivers GPU
BROWSER
Navegador (Chrome) em qualquer host
Painéis SaaS — Cloudflare, Doppler, Slack, GitHub, Meta Business
CLAUDE
Claude Desktop
Execução de Skills, Computer Use, comandos operacionais do agente
Convenções de notação
Notação
Significado
{VARIAVEL}
Variável que VOCÊ substitui antes de executar
→
Próximo subpasso dentro do mesmo passo
✓ Validação
Comando de verificação — resultado esperado descrito
⚠ Rollback
Como desfazer caso algo dê errado
🔒 Segredo
Valor sensível — nunca commitar em Git, sempre Doppler
Pré-voo — inventário e validação do estado atual
Antes de iniciar a Fase 0, é mandatório validar o estado atual da infraestrutura. Os passos abaixo confirmam que cada componente do Palantyr v3 está acessível e operacional. Falha em qualquer um requer correção antes de prosseguir.

#### PV-01

Validar acesso SSH ao Oracle Cloud
5 min
Host: WSL — Objetivo: confirmar SSH funcional para Oracle e ver containers rodando.
 WSL → Oracle
# Substituir {KEY_PATH} pelo caminho da sua chave Oracle
ssh -i {KEY_PATH} ubuntu@163.176.163.204
# Após conectar, listar containers ativos
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
✓ Validação — Devem aparecer pelo menos: n8n, evolution_api, postgres, nginx-proxy-manager, portainer. Status "Up" em todos.

#### PV-02

Validar Ollama local no WSL
5 min
Host: WSL — Objetivo: confirmar que Ollama responde e tem os modelos canônicos.
 WSL
# Verificar serviço
systemctl --user status ollama 2>/dev/null || sudo systemctl status ollama
# Listar modelos instalados
ollama list
# Teste de inferência
ollama run gemma3:12b 'Responda apenas: OK' --verbose 2>&1 | tail -5
✓ Validação — ollama list mostra gemma3:12b e qwen2.5:14b. A inferência responde "OK" em menos de 10 segundos.
ATENÇÃO — Se Ollama não responde
Reinicie com 'ollama serve &' em segundo plano. Se modelos faltarem, baixe com 'ollama pull gemma3:12b' (cerca de 8 GB) e 'ollama pull qwen2.5:14b' (cerca de 9 GB). Confirme espaço em disco antes — modelos ficam em ~/.ollama/models/.

#### PV-03

Validar Cloudflare DNS e Tunnel
5 min
Host: WSL — Objetivo: confirmar resolução DNS de subdomínios pltr e túnel ativo.
 WSL
# Testar subdomínios principais
for sub in n8n evolution portainer nginx; do
  echo -n "${sub}.pltr.fattech.com.br → "
  dig +short ${sub}.pltr.fattech.com.br | head -1
done
# Testar HTTPS
curl -sI https://n8n.pltr.fattech.com.br | head -3
✓ Validação — Todos os subdomínios resolvem para IPs Cloudflare (172.x ou 104.x). HTTPS retorna 200, 301 ou 401, não erro.

#### PV-04

Validar acesso GitHub fattech org
3 min
Host: WSL — Objetivo: confirmar gh CLI autenticado e org acessível.
 WSL
# Verificar autenticação
gh auth status
# Listar repos da org
gh repo list fattech --limit 50
# Confirmar permissão de criar repo
gh api user --jq '.login'
✓ Validação — Auth status "Logged in to github.com". Listagem retorna repos existentes (mesmo que poucos). API retorna seu login.

#### PV-05

Inventário de credenciais necessárias
10 min
Host: BROWSER + bloco de notas — Objetivo: ter à mão todas as credenciais que serão usadas nas próximas 72h.
Liste em um arquivo temporário (NÃO commitar) as credenciais abaixo. Elas serão movidas para Doppler na Fase 0.
Credencial
Onde obter
Para que serve
Meta System User Token (FAT Tech BM)
business.facebook.com → Configurações da Empresa → Usuários do Sistema
MCP Meta Marketing, CAPI
Meta App ID + Secret
developers.facebook.com → seu app
OAuth e callbacks
Google Ads Developer Token
ads.google.com → Ferramentas → Centro API
Reports e management
Google Cloud Service Account JSON
console.cloud.google.com → IAM → Service Accounts
Drive, Sheets, Ads
WhatsApp Number 9098369 (Evolution)
Painel Evolution já configurado
Disparo e atendimento — SAGRADO, não alterar
Kommo API Token
kommo.com → Integrações → API
CRM atual de qualificação
Cloudflare API Token (Zone:Edit)
dash.cloudflare.com → My Profile → API Tokens
Automação de DNS
Oracle SSH key
já no seu ~/.ssh/
Acesso ao servidor
HostGator FTP/SSH
Painel HostGator
Apenas se editar site WordPress
Postgres Oracle (palantyr DB)
Variáveis do docker-compose atual
Conexão para schemas multi-tenant
PERIGO — Tratamento obrigatório destes valores
Não cole nenhum desses valores em Slack, WhatsApp, comentário em código, prompt de Claude online, ou arquivo .env commitado. Eles ficam no bloco de notas LOCAL por no máximo 4 horas — tempo de carregar no Doppler na Fase 0.

## Fase 0 — Fundações (7 dias)

A Fase 0 estabelece os trilhos sobre os quais tudo será construído: repositório versionado, gestão de segredos, workspace de comunicação operacional e estrutura canônica do PALANTYR_BRAIN. Ao final desta fase, qualquer Skill pode ser criada, versionada e disparada com segurança.
Cronograma da Fase 0
Dia
Foco
Entregáveis
1
Repositório + estrutura
Repo palantyr-brain criado, estrutura canônica commitada
2
Segredos + comunicação
Doppler configurado, Slack workspace fattech operacional
3
Skills Registry v1
Estrutura 20_SKILLS_GLOBAIS e _REGISTRY.md publicados
4
Migração de skills existentes
4 skills (Mago Tráfego, Caçador, Mago Meta, Mago Supremo) versionadas
5
Documentação canônica
Blueprint v4 + manual + STACK_VIBE_CODING dentro do repo
6
Smoke test integrado
Skill simples disparada com sucesso (audit log preenchido)
7
Buffer + retrospectiva
Ajustes finais e ADR de Fase 0 escrito

### Dia 1 — Repositório e estrutura canônica


#### F0-01

Criar repositório palantyr-brain no GitHub fattech
10 min
Host: WSL
 WSL
# Definir variáveis
export BRAIN_DIR=$HOME/fattech/palantyr-brain
mkdir -p $HOME/fattech && cd $HOME/fattech
# Criar repo privado na org
gh repo create fattech/palantyr-brain \
  --private \
  --description 'PALANTYR Brain — cofre canônico FAT Tech' \
  --clone
cd palantyr-brain
git config user.name 'Walfredo Figueiredo Neto'
git config user.email 'wal@fattech.com.br'
✓ Validação — gh repo view fattech/palantyr-brain retorna o repo. Pasta local existe em ~/fattech/palantyr-brain.

#### F0-02

Criar estrutura canônica de diretórios
10 min
Host: WSL
 WSL
cd $BRAIN_DIR
# Estrutura canônica
mkdir -p 01_FATTECH_CORE/governanca
mkdir -p 10_CLIENTES/_TEMPLATE_
mkdir -p 20_SKILLS_GLOBAIS/{tracking,copy,trafego,crm,conteudo,devops}
mkdir -p 30_PROJETOS_INTERNOS/{resenha_barranqueira,fat_tech_crm,mcp_gateway}
mkdir -p 40_DEVOPS/{runbooks,snippets,postmortems,adr}
mkdir -p 90_AUDIT
mkdir -p 99_INBOX
# Tenants iniciais (vazios — preenchemos na Fase 1)
for cliente in silva_rocha wiserh fufikids da_modas musa_moda_intima \
               braseiro_bbq ozovitae marli_mello schellworth_rodrigues; do
  mkdir -p 10_CLIENTES/$cliente
done
tree -L 2 -d
✓ Validação — tree -L 2 mostra todos os 6 diretórios numerados e 9 subdirs em 10_CLIENTES.

#### F0-03

Criar .gitignore e arquivos sentinela
5 min
Host: WSL
 WSL
cd $BRAIN_DIR
cat > .gitignore <<'EOF'
# Segredos NUNCA no Git — sempre via Doppler
*.env
*.env.local
.env*
*credentials*
*secret*
*token*
*.key
*.pem
# Sistema operacional
.DS_Store
Thumbs.db
# Obsidian local
.obsidian/workspace*
.obsidian/cache
.trash/
# Build artifacts
node_modules/
__pycache__/
*.pyc
.venv/
# Audit logs locais (vão para Postgres em produção)
90_AUDIT/local/
# Inbox bruto pode conter PII
99_INBOX/raw/
EOF
# README raiz
cat > README.md <<'EOF'
# PALANTYR_BRAIN
Cofre canônico da operação FAT Tech.
Documento mestre: `01_FATTECH_CORE/arquitetura_v4.docx`
Manual: `01_FATTECH_CORE/manual_execucao_v4.docx`
## Estrutura
\`\`\`
01_FATTECH_CORE/      — manifesto, identidade, governança
10_CLIENTES/          — um diretório por tenant
20_SKILLS_GLOBAIS/    — registry de skills versionadas
30_PROJETOS_INTERNOS/ — iniciativas FAT Tech
40_DEVOPS/            — runbooks, snippets, ADRs
90_AUDIT/             — trilhas de auditoria
99_INBOX/             — captura bruta
\`\`\`
Toda mudança passa por PR. Credenciais NUNCA aqui — apenas no Doppler.
EOF
# Manter dirs vazios no Git
find . -type d -empty ! -path './.git*' -exec touch {}/.gitkeep \;
git add -A
git commit -m 'chore: estrutura canônica inicial Palantyr v4'
git push origin main
✓ Validação — Push bem-sucedido. gh repo view fattech/palantyr-brain --web abre o repo no navegador com a estrutura visível.

#### F0-04

Conectar Obsidian ao repositório
10 min
Host: WIN + BROWSER
Abrir Obsidian no Windows.
Open another vault → Open folder as vault.
Selecionar pasta: \\wsl$\Ubuntu\home\{seu_user}\fattech\palantyr-brain (substituir {seu_user})
Instalar plugins essenciais:
Templater (registrar templates do _TEMPLATE_)
Dataview (consultas dinâmicas sobre skills e tenants)
Obsidian Git (auto-commit a cada 15 min)
Tag Wrangler (curadoria de tags)
✓ Validação — Obsidian abre o vault, vê todos os diretórios, e o plugin Git mostra status "clean".
ATENÇÃO — Atenção ao path WSL no Windows
Se o Windows não montar automaticamente o filesystem WSL em \\wsl$\, abrir o Explorador de Arquivos, digitar \\wsl$ na barra e o Ubuntu deve aparecer. Caso contrário, executar 'wsl --shutdown' e iniciar novamente.

### Dia 2 — Doppler e Slack


#### F0-05

Provisionar workspace Doppler
15 min
Host: BROWSER + WSL
Acessar dashboard.doppler.com → criar conta com email corporativo.
Criar workspace 'fattech'.
Criar projetos iniciais:
palantyr-core — credenciais compartilhadas (Cloudflare, GitHub, Oracle)
palantyr-clientes — projeto pai dos tenants (subconfigs por cliente)
palantyr-internal — projetos internos FAT Tech (Resenha, CRM, MCP Gateway)
Para cada projeto, criar três ambientes: dev, stg, prd.
Em seguida, instalar Doppler CLI no WSL:
 WSL
# Instalar CLI
curl -Ls https://cli.doppler.com/install.sh | sudo sh
# Login (abre navegador)
doppler login
# Validar
doppler me
✓ Validação — doppler me retorna seu usuário Doppler.

#### F0-06

Carregar credenciais inventariadas no Doppler
20 min
Host: BROWSER
No painel Doppler, projeto palantyr-core, ambiente prd, criar os secrets abaixo. NÃO digitar via CLI (deixa histórico). Sempre via painel web.
Nome do secret
Valor (do inventário PV-05)
META_SYSTEM_USER_TOKEN
Token do System User da BM FAT Tech
META_APP_ID
ID do app Meta FAT Tech
META_APP_SECRET
App Secret
GOOGLE_ADS_DEVELOPER_TOKEN
Developer token
GOOGLE_SERVICE_ACCOUNT_JSON
JSON inteiro do service account (sem quebras)
EVOLUTION_API_KEY
Key da Evolution API atual
EVOLUTION_WHATSAPP_NUMBER
9098369 — número sagrado
KOMMO_API_TOKEN
Token Kommo CRM
CLOUDFLARE_API_TOKEN
Zone:Edit token
POSTGRES_PALANTYR_URL
postgres://user:pass@163.176.163.204:5432/palantyr
GITHUB_TOKEN
Personal access token org-scoped
✓ Validação — Painel Doppler mostra 11+ secrets em palantyr-core/prd.
PERIGO — Após carregar — apagar o bloco de notas
As credenciais do inventário PV-05 não devem mais existir em arquivo de texto puro local. Após confirmar todos os secrets no Doppler, apagar definitivamente o bloco de notas usado no inventário.

#### F0-07

Configurar Slack workspace fattech
20 min
Host: BROWSER
Acessar slack.com/get-started → criar workspace 'fattech'.
Adicionar email primário do CEO.
Criar canais iniciais:
Canal
Propósito
#ops
Operação geral, alertas do agente, decisões arquiteturais
#audit
Eventos do audit log (ações críticas do agente)
#inspiracao
Mineração diária de criativos virais
#cli-silva-rocha
Tenant Silva & Rocha — métricas, relatórios, anomalias
#cli-wiserh
Tenant WiseRH (Impulse BPO L99)
#cli-fufikids
Tenant Fufikids
#cli-da-modas
Tenant DA Modas
#cli-musa
Tenant Musa Moda Íntima
#cli-braseiro
Tenant Braseiro BBQ
#cli-ozovitae
Tenant Ozovitae
#cli-marli
Tenant Marli Mello (Santuário da Beleza)
#cli-schellworth
Tenant Schellworth & Rodrigues
#dev-palantyr
Desenvolvimento da própria infra (não confundir com #ops)
#dev-mcp-gateway
Construção do MCP Gateway
Em Apps → adicionar 'Doppler' e 'GitHub'.
Em Apps → buscar 'Slack MCP' (oficial Anthropic) — guardar OAuth token gerado, carregar no Doppler como SLACK_BOT_TOKEN.
✓ Validação — Slack workspace acessível em fattech.slack.com com todos os canais criados. SLACK_BOT_TOKEN salvo no Doppler.

### Dia 3 — Skills Registry v1


#### F0-08

Criar Skills Registry e template canônico
15 min
Host: WSL
 WSL
cd $BRAIN_DIR/20_SKILLS_GLOBAIS
cat > _REGISTRY.md <<'EOF'
# Skills Registry — Palantyr v4
Índice canônico de todas as skills versionadas da FAT Tech.
Toda skill nova é adicionada aqui via PR.
## Convenções
- ID em snake_case
- Versionamento semver (1.2.0)
- Status: draft | hml | producao | deprecated
- Categoria: tracking | copy | trafego | crm | conteudo | devops
## Skills em produção
| Skill ID | Versão | Categoria | Trigger natural | LLM | Custo médio |
|----------|--------|-----------|-----------------|-----|-------------|
| _(vazio — preenchido após F0-09)_ |
## Skills em homologação
_(vazio)_
## Skills depreciadas
_(vazio)_
EOF
Criar o template canônico para novas skills:
 WSL
cd $BRAIN_DIR/20_SKILLS_GLOBAIS
cat > _TEMPLATE_skill.md <<'EOF'
---
skill_id: nome_da_skill
versao: 0.1.0
status: draft
categoria: trafego
tags: [meta, relatorio]
autor: Mago Supremo
criado_em: YYYY-MM-DD
atualizado_em: YYYY-MM-DD
trigger:
  natural:
    - "frase de invocação 1"
    - "/comando_curto"
  cron: []
  webhook: []
inputs:
  obrigatorios:
    - cliente_slug
  opcionais:
    - periodo
outputs:
  - tipo: arquivo
    formato: pdf
    destino: drive://relatorios/
mcps_required:
  - meta_marketing_api
llm_requirement: simples
permissoes: confirmar
audit: obrigatorio
custo_estimado_tokens: 1500
---
# Skill: Nome legível
## Objetivo
[O que a skill faz, em uma frase]
## Pré-condições
[O que precisa estar verdade antes]
## Prompt operacional
[Prompt que vai para o LLM]
## Pós-execução
[O que precisa ser registrado, notificado, atualizado]
EOF
git add _REGISTRY.md _TEMPLATE_skill.md
git commit -m 'feat(skills): registry inicial e template canônico'
git push
✓ Validação — Arquivos visíveis no GitHub.

#### F0-09

Criar template canônico de tenant
10 min
Host: WSL
 WSL
cd $BRAIN_DIR/10_CLIENTES/_TEMPLATE_
cat > briefing.md <<'EOF'
---
tenant_slug: TEMPLATE
razao_social: ""
cnpj: ""
contato_principal: ""
whatsapp_principal: ""
email_principal: ""
inicio_contrato: ""
plano: ""
mensalidade_brl: 0
canal_slack: "#cli-TEMPLATE"
grupo_whatsapp_id: ""
doppler_namespace: "palantyr-clientes/TEMPLATE"
postgres_schema: "TEMPLATE"
---
# Briefing — {Razão Social}
## Sobre o cliente
[História, posicionamento, segmento]
## Produtos / serviços
[O que vende, ticket médio, sazonalidades]
## Persona / ICP
[Quem é o cliente do cliente]
## Acessos liberados
- Meta BM: __SIM__/NÃO
- Google Ads: __SIM__/NÃO
- Site/WP: __SIM__/NÃO
- Pixel/CAPI: __SIM__/NÃO
## Histórico
[O que já foi feito, o que deu certo, o que falhou]
EOF
cat > metricas_alvo.md <<'EOF'
# Métricas alvo
## KPIs primários
- CPA alvo: R$ ___
- ROAS alvo: ___x
- Volume mensal de leads: ___
## KPIs secundários
- CTR mínimo: ___%
- CPM máximo: R$ ___
- Taxa de conversão LP: ___%
EOF
cat > playbook.md <<'EOF'
# Playbook operacional
## Skills habilitadas
- [ ] relatorio_meta_semanal
- [ ] qualificar_lead
- [ ] criativo_ig (se aplicável)
## Cadência de relatórios
- Semanal: sábado 09h via Slack + grupo WhatsApp
- Mensal: dia 1 via PDF formal
## Escalation
- Anomalia detectada → #cli-{slug} + DM para Sir Wal
- Cliente sinaliza insatisfação → DM imediato para Sir Wal
EOF
cat > credenciais.ref.md <<'EOF'
# Referências de credenciais (NÃO conter valores)
Todas as credenciais deste cliente estão no Doppler:
\`palantyr-clientes/{tenant_slug}/prd\`
## Variáveis esperadas
- META_AD_ACCOUNT_ID
- META_PIXEL_ID
- GOOGLE_ADS_CUSTOMER_ID
- KOMMO_PIPELINE_ID
- WEBSITE_URL
EOF
touch auditoria.log
echo "# Audit log local — sincronizado com Postgres palantyr.audit_log" > auditoria.log
git add -A
git commit -m 'feat(tenants): template canônico de tenant'
git push
✓ Validação — 4 arquivos criados em 10_CLIENTES/_TEMPLATE_/.

### Dia 4 — Migração das skills existentes

As quatro skills já em uso (Mago do Tráfego, Caçador de Leads, Mago do Meta, Mago Supremo) serão migradas para o formato canônico v4. O processo é o mesmo para todas — descrito uma vez em F0-10 e replicado nas variações F0-11 a F0-13.

#### F0-10

Migrar 'Mago do Tráfego' para formato v4
30 min
Host: WSL
 WSL
cd $BRAIN_DIR/20_SKILLS_GLOBAIS/trafego
# Copiar template
cp ../_TEMPLATE_skill.md gestao_trafego_diaria.md
Em seguida, editar gestao_trafego_diaria.md com o frontmatter abaixo (em VSCode ou Obsidian):
 skill markdown
---
skill_id: gestao_trafego_diaria
versao: 1.0.0
status: producao
categoria: trafego
tags: [meta, google_ads, gestao_diaria, otimizacao]
autor: Mago Supremo
criado_em: 2026-05-27
atualizado_em: 2026-05-27
trigger:
  natural:
    - "rodar gestao diaria do tenant {slug}"
    - "/gestao {slug}"
  cron:
    - "0 8 * * *"   # todo dia 08h
inputs:
  obrigatorios:
    - cliente_slug
  opcionais:
    - acao_especifica   # 'somente_relatorio' | 'somente_otimizacao' | 'tudo'
outputs:
  - tipo: mensagem
    destino: slack://cli-{cliente_slug}
  - tipo: registro
    destino: postgres://palantyr.audit_log
mcps_required:
  - meta_marketing_api
  - google_ads_api
  - slack
llm_requirement: complexo
permissoes: confirmar_acoes_destrutivas
audit: obrigatorio
custo_estimado_tokens: 4000
---
# Skill: Gestão de Tráfego Diária
## Objetivo
Auditar campanhas ativas do cliente, identificar anomalias
(CPA acima do alvo, CTR abaixo do piso, frequência alta),
sugerir otimizações e — se autorizado — aplicá-las.
[Colar abaixo o conteúdo do prompt original Mago do Tráfego,
adaptado para receber cliente_slug como variável]
Após editar, atualizar o registry:
 WSL
# Atualizar _REGISTRY.md adicionando linha:
# | gestao_trafego_diaria | 1.0.0 | trafego | "rodar gestao diaria" | complexo | ~R$ 0,12 |
cd $BRAIN_DIR
git add 20_SKILLS_GLOBAIS/
git commit -m 'feat(skills): migra Mago do Tráfego para gestao_trafego_diaria@1.0.0'
git push
✓ Validação — Arquivo gestao_trafego_diaria.md no GitHub, com frontmatter válido (YAML lint passa). Registry atualizado.

#### F0-11

Migrar 'Caçador de Leads' (prospecção)
30 min
Mesmo processo do F0-10. Variações:
Campo
Valor para esta skill
skill_id
prospeccao_b2b_local
categoria
crm
trigger.natural
"caça leads em {nicho} {regiao}"
mcps_required
apify (eventual), google_drive, slack
llm_requirement
medio
custo_estimado_tokens
3000
ATENÇÃO — Compliance LGPD desta skill
Esta skill coleta dados de empresas via fontes públicas. Base legal: legítimo interesse. Retenção: 12 meses. Adicionar nota no header da skill: 'Os dados coletados destinam-se exclusivamente a contato comercial inicial e são descartados após 12 meses ou opt-out'.

#### F0-12

Migrar 'Mago do Meta' (subida e otimização)
30 min
Variações:
Campo
Valor para esta skill
skill_id
subir_campanha_meta
categoria
trafego
trigger.natural
"sobe campanha de {produto} no padrão {clientes_slug}"
mcps_required
meta_marketing_api, google_drive
llm_requirement
complexo
permissoes
confirmar_sempre — campanha publicada custa dinheiro
custo_estimado_tokens
5000

#### F0-13

Migrar 'Mago Supremo' (orquestrador)
20 min
O Mago Supremo NÃO vira uma skill executora — vira o SYSTEM PROMPT do agente. Ele deve ser referenciado, não invocado.
 WSL
cd $BRAIN_DIR/01_FATTECH_CORE
mkdir -p prompts
cp $BRAIN_DIR/20_SKILLS_GLOBAIS/_TEMPLATE_skill.md prompts/_TEMPLATE_prompt.md
# Criar o system prompt canônico
cat > prompts/system_mago_supremo.md <<'EOF'
---
prompt_id: mago_supremo
versao: 2.6.0
papel: system_prompt
escopo: agente_orquestrador_principal
atualizado_em: 2026-05-27
---
# System Prompt — Mago Supremo das IAs
[Colar aqui o WAL_Prompt_v2_5_texto_1.txt já existente,
adaptado para referenciar:
- A estrutura PALANTYR_BRAIN
- O registry de skills
- A camada de routing de LLM
- O audit log obrigatório]
EOF
git add prompts/
git commit -m 'feat(prompts): registra Mago Supremo como system prompt versionado'
git push
✓ Validação — 4 skills + 1 system prompt versionados no Git. Registry refletindo o estado real.

### Dia 5 — Documentação canônica no repo


#### F0-14

Mover blueprint v4 e manual para 01_FATTECH_CORE
10 min
Host: WSL
 WSL
cd $BRAIN_DIR/01_FATTECH_CORE
# Copiar o blueprint (que está em /mnt/user-data/outputs)
# Para o ambiente de produção, fazer upload via Obsidian ou cp direto
cp /caminho/para/PALANTYR_v4_Blueprint.docx ./arquitetura_v4.docx
cp /caminho/para/Manual_Execucao_v4.docx ./manual_execucao_v4.docx
# Manifesto
cat > manifesto.md <<'EOF'
# Manifesto FAT Tech — Palantyr v4
## Nossa tese
Engenharia de sistemas aplicada à aquisição.
Cada lead é um pacote. Cada cliente é um tenant.
Cada decisão é versionada.
## Princípios inegociáveis
1. Soberania de infraestrutura
2. Multi-tenant by design
3. Stateless agent, stateful brain
4. Skills versionadas
5. Auditoria total
6. LLM roteado por tarefa
7. Computer Use é exceção
8. Compliance LGPD declarado
## Documentos canônicos
- arquitetura_v4.docx — o blueprint
- manual_execucao_v4.docx — o manual de execução
- governanca/lgpd.md — bases legais e retenção
- governanca/seguranca.md — políticas de segredos
- governanca/auditoria.md — schema e procedimentos do audit log
EOF
# Identidade visual canônica
cat > identidade_visual.md <<'EOF'
# Identidade visual FAT Tech
## Paleta
- Background: #06060e (near-black cyberpunk)
- Primário: #00f0ff (neon cyan) — em DOCX usar #00B8C4
- Secundário: #ff2d78 (hot pink/magenta) — em DOCX usar #C42060
- Texto neutro: #1A1A24 (graphite)
- Apoio: #808088 (silver)
## Tipografia
- Display: Orbitron (web), Aptos Display (Office)
- Body: Rajdhani (web), Calibri (Office)
- Mono: JetBrains Mono (code), Consolas (Office)
## Aesthetic
Cyberpunk técnico, mas legível.
Glows radiais sobre near-black.
Cantos geométricos.
Sem gradientes pasteis.
EOF
git add -A
git commit -m 'docs: blueprint v4, manual, manifesto e identidade visual canônicos'
git push
✓ Validação — Documentos visíveis no GitHub e no Obsidian.

#### F0-15

Criar governança inicial (LGPD, segurança, auditoria)
30 min
Host: WSL + Obsidian
Criar três documentos de governança em 01_FATTECH_CORE/governanca/. Eles serão expandidos na Fase 4, mas precisam existir desde já como referência:
 WSL
cd $BRAIN_DIR/01_FATTECH_CORE/governanca
cat > lgpd.md <<'EOF'
# Política LGPD — FAT Tech
DPO: Walfredo Figueiredo Neto (CEO)
Email: dpo@fattech.com.br
Atualizada em: 2026-05-27
## Bases legais por tipo de dado
| Tipo | Base legal | Retenção |
|------|-----------|----------|
| Lead inbound (form opt-in) | Consentimento | 24 meses |
| Lead outbound (CNPJ público) | Legítimo interesse | 12 meses |
| Cliente ativo | Execução de contrato | Vigência + 5 anos |
| Conversas WhatsApp | Consentimento (lead iniciou) | 12 meses |
| Audit log Palantyr | Legítimo interesse (segurança) | 5 anos |
## Direitos do titular
SLA de atendimento: 48 horas
Canal: dpo@fattech.com.br
## Subprocessadores declarados
- Oracle Cloud (Brasil)
- Cloudflare (USA)
- Anthropic (USA)
- OpenAI (USA)
- Meta (USA)
- Google (USA)
- Doppler (USA)
EOF
cat > seguranca.md <<'EOF'
# Política de Segurança — FAT Tech
## Gestão de segredos
- TUDO no Doppler — namespace por tenant
- ZERO segredos em Git, código, prompts ou .env locais
- Rotação obrigatória a cada 90 dias
- Acesso por princípio do menor privilégio
## Acesso à infraestrutura
- Oracle Cloud: SSH key only, fail2ban ativo
- GitHub: 2FA obrigatório, branch protection na main
- Doppler: SSO + 2FA
- Slack: SSO + 2FA
## Incidentes
- Vazamento suspeito → revogar credencial em <15min
- Postmortem obrigatório em 40_DEVOPS/postmortems/
- Comunicação ao titular em até 72h se PII envolvida
EOF
cat > auditoria.md <<'EOF'
# Política de Auditoria — Palantyr v4
## Schema canônico (Postgres palantyr.audit_log)
[copiar da Parte 6 do blueprint v4]
## Eventos auditados
- TODA execução de Skill
- TODA chamada de MCP custom
- TODA decisão de roteamento LLM
- TODA mudança de credencial via Doppler
- TODO acesso a tenant fora da jornada normal
## Imutabilidade
- Hash encadeado entre registros
- Append-only via trigger Postgres
- Backup diário cifrado em Oracle Object Storage
EOF
git add .
git commit -m 'docs(governanca): LGPD, segurança e auditoria — versão inicial'
git push
✓ Validação — Três arquivos em 01_FATTECH_CORE/governanca/, visíveis no GitHub.

### Dia 6 — Smoke test integrado


#### F0-16

Instalar Claude Desktop e conectar aos MCPs
15 min
Host: WIN
Baixar Claude Desktop de claude.ai/download (instalar no Windows nativo, não WSL).
Login com conta Anthropic FAT Tech.
Settings → Developer → Edit Config — vai abrir claude_desktop_config.json.
Substituir conteúdo por:
 claude_desktop_config.json
{
  "mcpServers": {
    "slack": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-slack"],
      "env": {
        "SLACK_BOT_TOKEN": "{COLAR_DO_DOPPLER}",
        "SLACK_TEAM_ID": "{TEAM_ID_DO_WORKSPACE}"
      }
    },
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "\\\\wsl$\\Ubuntu\\home\\{seu_user}\\fattech\\palantyr-brain"
      ]
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "{COLAR_DO_DOPPLER}"
      }
    }
  }
}
Salvar arquivo, reiniciar Claude Desktop completamente.
Em Settings → Developer, confirmar status 'running' para os 3 MCPs.
✓ Validação — No chat do Claude Desktop, perguntar: "Liste os arquivos em 01_FATTECH_CORE". Deve responder com a estrutura do PALANTYR_BRAIN.
ATENÇÃO — Erro comum
Se o MCP filesystem não enxergar a pasta, é problema de path Windows-vs-WSL. Verificar que o path no JSON usa \\wsl$\Ubuntu\... com barras duplas escapadas (na verdade quatro: \\\\). Alternativa: mover o brain para uma pasta nativa Windows e fazer git pull lá.

#### F0-17

Smoke test 1 — Listagem via MCP
5 min
Host: CLAUDE — Comando ao agente:
 prompt no Claude Desktop
Liste todas as skills atualmente em produção no
PALANTYR_BRAIN/20_SKILLS_GLOBAIS/. Para cada uma,
extraia: skill_id, versão, categoria e trigger natural primário.
Formate como tabela markdown.
✓ Validação — Claude lê os 4 arquivos via MCP filesystem, extrai o frontmatter e devolve tabela com 4 linhas (gestao_trafego_diaria, prospeccao_b2b_local, subir_campanha_meta, system_mago_supremo).

#### F0-18

Smoke test 2 — Mensagem no Slack via MCP
5 min
Host: CLAUDE
 prompt no Claude Desktop
Poste no canal #ops do Slack a seguinte mensagem:
"✅ Smoke test F0-18 — Palantyr v4 Fase 0 operacional.
4 skills versionadas, Doppler ativo, MCPs filesystem+slack+github
conectados. Próxima fase: multi-tenant."
✓ Validação — Mensagem aparece no #ops com timestamp coerente. Pode ser enviada pelo bot ou pelo seu próprio usuário, ambos são aceitáveis nesta fase.

#### F0-19

Smoke test 3 — Commit via MCP GitHub
5 min
Host: CLAUDE
 prompt no Claude Desktop
Crie um arquivo em fattech/palantyr-brain no path
99_INBOX/2026-05-27_smoke_test_f0.md com o conteúdo:
# Smoke Test F0 — concluído
Data: 2026-05-27
Status: aprovado
Observações: três MCPs operacionais
Faça o commit direto na branch main com a mensagem:
"test(smoke): F0-19 validação via MCP GitHub"
✓ Validação — git pull no WSL traz o arquivo novo. Histórico do GitHub mostra o commit autorado pelo bot.

### Dia 7 — ADR e fechamento da Fase 0


#### F0-20

Escrever ADR-0001 — fechamento da Fase 0
30 min
Host: WSL + Obsidian
 WSL
cd $BRAIN_DIR/40_DEVOPS/adr
cat > 0001-fase-zero-fundacoes.md <<'EOF'
# ADR-0001 — Fase 0 Concluída: Fundações Palantyr v4
**Data**: 2026-05-27
**Status**: Aceito
**Autor**: Walfredo Figueiredo Neto
## Contexto
Migração da FAT Tech da operação Palantyr v3 (infraestrutura)
para Palantyr v4 (camada de inteligência operacional multi-tenant).
## Decisões tomadas
1. Repositório canônico: github.com/fattech/palantyr-brain (privado)
2. Estrutura de pastas: 01_FATTECH_CORE, 10_CLIENTES, 20_SKILLS_GLOBAIS,
   30_PROJETOS_INTERNOS, 40_DEVOPS, 90_AUDIT, 99_INBOX
3. Gestão de segredos: Doppler (não HashiCorp Vault)
4. Comunicação operacional: Slack (workspace fattech)
5. Cliente Desktop: Claude Desktop no Windows (não Claude.ai web)
6. MCPs ativos na Fase 0: filesystem, slack, github
## Consequências
- Toda credencial sai dos .env locais e vai para Doppler
- Toda skill nova passa por PR no GitHub
- WhatsApp pessoal deixa de ser canal operacional (vira pessoal)
- Slack #ops vira mission control
## Pendências para Fase 1
- Multi-tenant Postgres (schemas por cliente)
- Cofre Doppler com namespaces por tenant
- Audit log table no Postgres
- Router de Intent (parser de comandos)
- Onboarding técnico de Silva & Rocha + WiseRH
## Aprovação
Aprovado por: Walfredo Figueiredo Neto (CEO)
EOF
git add .
git commit -m 'docs(adr): ADR-0001 fechamento da Fase 0'
git push
✓ Validação — ADR commitada. Postar resumo no #ops via Slack.
VALIDAÇÃO — Fase 0 concluída — checklist final
Antes de avançar para Fase 1, garantir: (a) gh repo view fattech/palantyr-brain mostra repo populado; (b) doppler secrets em palantyr-core/prd lista 11+ secrets; (c) Slack workspace fattech tem 14 canais; (d) Claude Desktop com 3 MCPs ativos; (e) 4 skills versionadas + 1 system prompt; (f) ADR-0001 commitada.

## Fase 1 — Multi-tenant funcional (14 dias)

A Fase 1 transforma o vault canônico em operação multi-tenant real. Cada cliente passa a ter: cofre próprio no Doppler, schema próprio no Postgres, canal Slack próprio, fila lógica própria, audit log próprio. Ao final desta fase, dois tenants pilotos (Silva & Rocha e WiseRH) estarão operacionais com a primeira Skill validada em produção.
Cronograma da Fase 1
Dia
Foco
Entregáveis
1-2
Postgres palantyr DB
DB criado, role palantyr_app, RLS configurado
3-4
Audit log + hash chain
Tabela palantyr.audit_log com triggers de hash
5-6
Doppler multi-tenant
Namespaces fattech/clientes/{slug}/prd para todos
7-8
Router de Intent (v1)
Serviço básico que identifica tenant e skill
9-10
Onboarding Silva & Rocha
Tenant completo + skill relatorio_meta_semanal
11-12
Onboarding WiseRH
Tenant completo + skill diagnostico_anomalia
13-14
Validação e ADR-0002
Smoke tests E2E + ADR fechando a fase

### Dias 1-2 — Provisionar Postgres palantyr DB


#### F1-01

Criar database e roles no Postgres do Oracle
20 min
Host: ORACLE
 ORACLE → docker exec
# Conectar ao Postgres do Palantyr v3 (já rodando)
docker exec -it postgres psql -U postgres
# Dentro do psql:
CREATE DATABASE palantyr;
CREATE ROLE palantyr_app WITH LOGIN PASSWORD '{SENHA_FORTE}';
GRANT CONNECT ON DATABASE palantyr TO palantyr_app;
\\c palantyr
CREATE SCHEMA palantyr;
GRANT USAGE ON SCHEMA palantyr TO palantyr_app;
GRANT CREATE ON SCHEMA palantyr TO palantyr_app;
-- Extensão para hash chain do audit log
CREATE EXTENSION IF NOT EXISTS pgcrypto;
-- Extensão para embeddings (Fase 2)
CREATE EXTENSION IF NOT EXISTS vector;
\\q
✓ Validação — \l lista "palantyr" e \du lista "palantyr_app". Após sair, atualizar Doppler com a senha em POSTGRES_PALANTYR_PASSWORD.
ROLLBACK — Rollback F1-01
Em caso de erro, executar: DROP DATABASE palantyr; DROP ROLE palantyr_app; e refazer.

#### F1-02

Criar schemas por tenant (placeholders)
15 min
Host: ORACLE
 ORACLE
docker exec -it postgres psql -U postgres -d palantyr
-- Schema por tenant — cada cliente tem o seu
CREATE SCHEMA silva_rocha;
CREATE SCHEMA wiserh;
CREATE SCHEMA fufikids;
CREATE SCHEMA da_modas;
CREATE SCHEMA musa_moda_intima;
CREATE SCHEMA braseiro_bbq;
CREATE SCHEMA ozovitae;
CREATE SCHEMA marli_mello;
CREATE SCHEMA schellworth_rodrigues;
-- palantyr_app pode usar todos
DO $$
DECLARE
  s TEXT;
BEGIN
  FOR s IN SELECT schema_name FROM information_schema.schemata
           WHERE schema_name NOT IN ('palantyr','public','pg_catalog','information_schema','pg_toast')
  LOOP
    EXECUTE format('GRANT USAGE, CREATE ON SCHEMA %I TO palantyr_app', s);
  END LOOP;
END$$;
\\dn
✓ Validação — \dn lista 9 schemas além de palantyr/public.

#### F1-03

Criar tabela palantyr.audit_log com hash chain
20 min
Host: ORACLE
 ORACLE
docker exec -it postgres psql -U postgres -d palantyr
CREATE TABLE palantyr.audit_log (
  id              BIGSERIAL PRIMARY KEY,
  ts              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  tenant_slug     TEXT NOT NULL,
  actor_type      TEXT NOT NULL CHECK (actor_type IN ('human','agent','cron','webhook')),
  actor_id        TEXT,
  skill_id        TEXT,
  skill_version   TEXT,
  command_raw     TEXT,
  llm_used        TEXT,
  mcps_used       TEXT[],
  status          TEXT NOT NULL CHECK (status IN ('ok','fail','partial','aborted')),
  tokens_in       INTEGER,
  tokens_out      INTEGER,
  cost_usd        NUMERIC(10,6),
  duration_ms     INTEGER,
  result_summary  TEXT,
  error_message   TEXT,
  hash_prev       TEXT,
  hash_self       TEXT NOT NULL
);
CREATE INDEX idx_audit_tenant_ts ON palantyr.audit_log (tenant_slug, ts DESC);
CREATE INDEX idx_audit_skill_ts ON palantyr.audit_log (skill_id, ts DESC);
-- Trigger para append-only (impede UPDATE e DELETE)
CREATE FUNCTION palantyr.audit_immutable() RETURNS TRIGGER AS $$
BEGIN
  RAISE EXCEPTION 'audit_log is append-only';
END;
$$ LANGUAGE plpgsql;
CREATE TRIGGER trg_audit_no_update BEFORE UPDATE ON palantyr.audit_log
  FOR EACH ROW EXECUTE FUNCTION palantyr.audit_immutable();
CREATE TRIGGER trg_audit_no_delete BEFORE DELETE ON palantyr.audit_log
  FOR EACH ROW EXECUTE FUNCTION palantyr.audit_immutable();
-- Trigger para hash encadeado
CREATE FUNCTION palantyr.audit_hash_chain() RETURNS TRIGGER AS $$
DECLARE
  prev_hash TEXT;
  hash_input TEXT;
BEGIN
  SELECT hash_self INTO prev_hash FROM palantyr.audit_log
    ORDER BY id DESC LIMIT 1;
  NEW.hash_prev := COALESCE(prev_hash, 'GENESIS');
  hash_input := concat_ws('|',
    NEW.ts::text, NEW.tenant_slug, NEW.actor_type, NEW.actor_id,
    NEW.skill_id, NEW.command_raw, NEW.status, NEW.hash_prev
  );
  NEW.hash_self := encode(digest(hash_input, 'sha256'), 'hex');
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;
CREATE TRIGGER trg_audit_hash BEFORE INSERT ON palantyr.audit_log
  FOR EACH ROW EXECUTE FUNCTION palantyr.audit_hash_chain();
-- Permissão para palantyr_app
GRANT INSERT, SELECT ON palantyr.audit_log TO palantyr_app;
GRANT USAGE ON SEQUENCE palantyr.audit_log_id_seq TO palantyr_app;
Testar:
 ORACLE
-- Inserção teste
INSERT INTO palantyr.audit_log
  (tenant_slug, actor_type, actor_id, skill_id, command_raw, status)
VALUES
  ('_test_','human','wal','smoke_test','f1-03 setup','ok');
SELECT id, ts, tenant_slug, status, hash_prev, hash_self
FROM palantyr.audit_log;
-- Tentar UPDATE — deve falhar
UPDATE palantyr.audit_log SET status='fail' WHERE id=1;
-- ERRO esperado: audit_log is append-only
✓ Validação — Insert funciona, hash_prev='GENESIS', hash_self é SHA256 hex de 64 chars. UPDATE retorna erro.

### Dias 3-4 — Estrutura Doppler multi-tenant


#### F1-04

Criar namespaces Doppler por tenant
30 min
Host: BROWSER
No Doppler, abrir projeto palantyr-clientes.
Criar uma configuração por tenant: silva_rocha_prd, wiserh_prd, fufikids_prd, etc.
Em cada configuração, criar os secrets canônicos do tenant:
Secret
Valor (exemplo Silva & Rocha)
TENANT_SLUG
silva_rocha
POSTGRES_SCHEMA
silva_rocha
META_AD_ACCOUNT_ID
act_XXXXXXXXX
META_PIXEL_ID
XXXXXXXXXX
GOOGLE_ADS_CUSTOMER_ID
XXX-XXX-XXXX
KOMMO_PIPELINE_ID
XXXXX
WHATSAPP_GROUP_ID
120363@g.us
SLACK_CHANNEL_ID
C0XXXXXXX (canal #cli-silva-rocha)
WEBSITE_URL
https://srgestaotributaria.com
CPA_ALVO_BRL
350
ROAS_ALVO
3.0
✓ Validação — Cada tenant tem sua configuração com no mínimo 11 secrets. CLI test: doppler secrets --project palantyr-clientes --config silva_rocha_prd.

### Dias 5-7 — Router de Intent v1


#### F1-05

Criar serviço router-intent (Python FastAPI)
60 min
Host: WSL
 WSL
mkdir -p $HOME/fattech/router-intent
cd $HOME/fattech/router-intent
# venv
python3 -m venv .venv
source .venv/bin/activate
pip install fastapi uvicorn pydantic httpx pyyaml psycopg2-binary python-dotenv
pip freeze > requirements.txt
Criar app.py:
 router-intent/app.py
# app.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2, os, yaml, re, json
from datetime import datetime
app = FastAPI(title="Palantyr Router de Intent v1")
# Carrega registry de tenants e skills do brain
BRAIN = os.environ.get("BRAIN_PATH", "/home/ubuntu/fattech/palantyr-brain")
def list_tenants():
    base = f"{BRAIN}/10_CLIENTES"
    return [d for d in os.listdir(base)
            if os.path.isdir(f"{base}/{d}") and not d.startswith("_")]
def list_skills():
    skills = {}
    base = f"{BRAIN}/20_SKILLS_GLOBAIS"
    for root, _, files in os.walk(base):
        for f in files:
            if f.endswith(".md") and not f.startswith("_"):
                path = f"{root}/{f}"
                with open(path) as fp:
                    content = fp.read()
                m = re.match(r"^---\n(.+?)\n---", content, re.S)
                if not m: continue
                meta = yaml.safe_load(m.group(1))
                skills[meta["skill_id"]] = meta
    return skills
class IntentRequest(BaseModel):
    raw_command: str
    actor_id: str
    actor_type: str = "human"
@app.post("/intent")
def parse_intent(req: IntentRequest):
    tenants = list_tenants()
    skills = list_skills()
    # Detectar tenant
    tenant_detected = None
    for t in tenants:
        if t in req.raw_command.lower():
            tenant_detected = t
            break
    # Detectar skill por trigger natural
    skill_detected = None
    for sid, meta in skills.items():
        for trigger in meta.get("trigger", {}).get("natural", []):
            pat = trigger.replace("{slug}","\\S+").replace("{cliente_slug}","\\S+")
            if re.search(pat, req.raw_command, re.I):
                skill_detected = sid
                break
        if skill_detected: break
    if not tenant_detected:
        raise HTTPException(400, "Tenant não identificado no comando")
    if not skill_detected:
        raise HTTPException(400, "Skill não identificada")
    skill_meta = skills[skill_detected]
    # Audit
    log_audit(tenant_detected, req.actor_type, req.actor_id,
              skill_detected, skill_meta.get("versao","?"),
              req.raw_command, "intent_parsed")
    return {
        "tenant": tenant_detected,
        "skill_id": skill_detected,
        "skill_version": skill_meta.get("versao"),
        "llm_requirement": skill_meta.get("llm_requirement","simples"),
        "mcps_required": skill_meta.get("mcps_required",[]),
        "permissoes": skill_meta.get("permissoes","confirmar"),
    }
def log_audit(tenant, atype, aid, sid, sver, cmd, status):
    conn = psycopg2.connect(os.environ["POSTGRES_PALANTYR_URL"])
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO palantyr.audit_log
        (tenant_slug, actor_type, actor_id, skill_id, skill_version, command_raw, status)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
    """, (tenant, atype, aid, sid, sver, cmd, status))
    conn.commit()
    cur.close(); conn.close()
@app.get("/health")
def health():
    return {
        "status": "ok",
        "tenants": len(list_tenants()),
        "skills": len(list_skills()),
        "ts": datetime.utcnow().isoformat()
    }
Testar localmente com Doppler:
 WSL
# Rodar com secrets do Doppler injetados
doppler run --project palantyr-core --config prd -- \
  uvicorn app:app --host 0.0.0.0 --port 8088 --reload
# Em outro terminal:
curl http://localhost:8088/health
curl -X POST http://localhost:8088/intent \
  -H 'Content-Type: application/json' \
  -d '{
    "raw_command": "roda gestao diaria do tenant silva_rocha",
    "actor_id": "wal"
  }'
✓ Validação — /health retorna 4+ skills e 9 tenants. POST /intent retorna tenant=silva_rocha, skill_id=gestao_trafego_diaria. Registro aparece em palantyr.audit_log.

### Dias 8-10 — Onboarding Silva & Rocha


#### F1-06

Preencher briefing real do Silva & Rocha
30 min
Host: WSL + Obsidian
 WSL
cd $BRAIN_DIR/10_CLIENTES/silva_rocha
# Copiar do template
cp ../_TEMPLATE_/*.md .
# Editar briefing.md com dados reais:
# - razao_social: Schellworth & Rodrigues Gestão e Consultoria Tributária Ltda
# - cnpj: [do contrato]
# - whatsapp: 41 984486931
# - email: contato@srgestaotributaria.com
# - inicio_contrato: [data assinatura]
# - plano: Tráfego e Funil R$ 899/mês
# - canal_slack: #cli-silva-rocha
# - postgres_schema: silva_rocha
# Preencher metricas_alvo.md com KPIs reais
# Preencher playbook.md com skills habilitadas inicialmente
git add 10_CLIENTES/silva_rocha/
git commit -m 'feat(tenant): onboard Silva & Rocha — briefing e playbook'
git push
✓ Validação — Briefing real commitado. Obsidian mostra o tenant com dados.

#### F1-07

Criar e versionar skill 'relatorio_meta_semanal'
60 min
Host: WSL
 WSL
cd $BRAIN_DIR/20_SKILLS_GLOBAIS/tracking
cp ../_TEMPLATE_skill.md relatorio_meta_semanal.md
# Editar com:
# - skill_id: relatorio_meta_semanal
# - versao: 1.0.0
# - status: hml
# - categoria: tracking
# - trigger natural: "manda relatorio semanal do {slug}"
# - cron: "0 9 * * SAT"
# - mcps_required: meta_marketing_api, slack
# - llm_requirement: medio
# - prompt operacional: instruções de como extrair métricas Meta,
#   comparar com semana anterior, gerar 3 insights, postar no Slack
Esqueleto do prompt operacional (corpo da skill):
 trecho de relatorio_meta_semanal.md
## Prompt operacional
Você é o agente FAT Tech encarregado de gerar o relatório
semanal de tráfego para o tenant {cliente_slug}.
### Passos
1. Conectar via MCP Meta Marketing API usando credenciais
   do namespace palantyr-clientes/{cliente_slug}/prd
2. Extrair métricas dos últimos 7 dias (CPA, CTR, CPM, ROAS,
   gasto total, vendas, leads)
3. Comparar com os 7 dias anteriores — calcular delta % por métrica
4. Identificar as 2 melhores e 2 piores adsets
5. Gerar 3 insights acionáveis (não genéricos)
6. Postar no canal #cli-{cliente_slug} com formato:
   - Resumo executivo (3 linhas)
   - Tabela KPIs com deltas
   - Top performers
   - Pontos de atenção
   - Recomendações
### Limites
- NÃO sugerir mudanças destrutivas sem confirmação humana
- NÃO citar valores absolutos de orçamento em canais públicos
- SE delta CPA > +30% em qualquer campanha ATIVA →
  alertar Sir Wal via DM Slack imediatamente
### Registro
- Persistir relatório final em PDF em
  drive://relatorios/{cliente_slug}/{YYYY-MM-DD}.pdf
- Inserir registro em palantyr.audit_log
✓ Validação — Skill commitada com status "hml". Registry atualizado.

#### F1-08

Execução piloto da skill em Silva & Rocha
30 min
Host: CLAUDE Desktop
 prompt
# Comando ao agente:
"Executa a skill relatorio_meta_semanal versão 1.0.0
para o tenant silva_rocha, modo dry-run (não posta no Slack
real ainda). Mostra o output completo aqui para validação."
Revisar a saída visualmente. Se aprovada:
 prompt
"Executa a skill relatorio_meta_semanal versão 1.0.0
para o tenant silva_rocha em modo produção.
Posta no canal #cli-silva-rocha conforme spec."
✓ Validação — Relatório aparece no Slack. SELECT * FROM palantyr.audit_log WHERE tenant_slug='silva_rocha' ORDER BY id DESC LIMIT 5; mostra a execução com status=ok. Promover skill de hml → producao no registry.

### Dias 11-12 — Onboarding WiseRH


#### F1-09

Onboarding técnico WiseRH (Impulse BPO L99)
60 min
Replicar F1-06 com dados WiseRH. Atenção especial:
Branding dos deliverables: Impulse BPO (não FAT Tech direto)
Foco prioritário: anomalia desktop vs mobile no Google Ads — desktop com gasto alto e zero conversões. Skill principal:diagnostico_anomalia_canal
Slack: #cli-wiserh
Postgres schema: wiserh

#### F1-10

Criar skill 'diagnostico_anomalia_canal'
60 min
Host: WSL
Frontmatter chave desta skill:
Campo
Valor
skill_id
diagnostico_anomalia_canal
categoria
trafego
trigger.natural
"diagnostica anomalia em {slug}"
trigger.cron
"0 7 * * *" (diário 07h, antes do horário comercial)
mcps_required
google_ads_api, meta_marketing_api, slack
llm_requirement
complexo (raciocínio causal)
custo_estimado_tokens
6000
Prompt operacional (lógica):
Extrair últimos 7 dias por canal (desktop / mobile / tablet)
Calcular: spend, conversões, CPA por canal
Identificar canais com spend > 30% e conversões = 0
Cross-check: existe pixel desse canal? CAPI conectado? LP é responsive?
Gerar hipóteses ranqueadas com plano de ação
Postar diagnóstico em #cli-wiserh com tags @canal se urgente

### Dias 13-14 — Validação final e ADR-0002


#### F1-11

Smoke test E2E dos dois tenants
30 min
Executar os ciclos completos a seguir e validar cada um:
Cenário
Comando
Validação esperada
Silva & Rocha — relatório semanal
/skill relatorio_meta_semanal silva_rocha
PDF no Drive, mensagem no #cli-silva-rocha, registro no audit_log
WiseRH — diagnóstico anomalia
/skill diagnostico_anomalia_canal wiserh
Mensagem no #cli-wiserh com hipóteses ranqueadas
Isolamento — comando para tenant A com credenciais B
Tentar forçar leak
Erro de credenciais ausente — Doppler isola corretamente
Audit imutabilidade
UPDATE audit_log SET status='fail' WHERE id=1
Postgres retorna ERROR: audit_log is append-only

#### F1-12

ADR-0002 — fechamento da Fase 1
30 min
Host: WSL
Criar 40_DEVOPS/adr/0002-fase-um-multi-tenant.md documentando:
9 tenants estruturalmente criados (2 operacionais, 7 placeholders)
Audit log funcional com hash chain
Router de intent v1 operacional
Doppler com namespaces por tenant
2 skills validadas em produção (relatorio_meta_semanal, diagnostico_anomalia_canal)
Pendências para Fase 2: MCP Meta custom, LLM Hybrid Router, Flowise, expansão para os 7 tenants restantes
VALIDAÇÃO — Fase 1 concluída
FAT Tech opera multi-tenant. Dois clientes piloto rodando skills via agente com audit log persistido. Próxima fase entrega autonomia: MCP Meta custom + Hybrid LLM router.

## Fase 2 — MCP Gateway e Roteamento Híbrido (21 dias)

A Fase 2 entrega a verdadeira autonomia operacional: o agente passa a controlar Meta e Evolution sem proxies humanos, e a escolha de LLM (Ollama/Claude/GPT) deixa de ser manual e passa a ser declarativa pela skill. Esta é a fase que destrava o ROI real do Palantyr v4.
Cronograma da Fase 2
Dia
Foco
Entregáveis
1-7
MCP Meta Marketing custom
Servidor MCP em Python expondo: list_campaigns, list_adsets, list_ads, get_insights, create_campaign, update_budget, pause_ad
8-12
LLM Hybrid Router
Serviço que decide Ollama/Claude/GPT por llm_requirement da skill, com fallback automático
13-15
Cloudflare Tunnel Ollama → Oracle
Ollama local exposto via tunnel para o router consumir
16-18
Make como proxy de I/O
5 scenarios de scraping/enriquecimento substituindo tokens LLM
19-21
Flowise deploy + ADR-0003
Flowise no Oracle para chains complexas, ADR fechando a fase
Bloco MCP Meta Marketing custom

#### F2-01

Scaffold do servidor MCP em Python
30 min
Host: WSL
 WSL
mkdir -p $HOME/fattech/mcp-meta-marketing
cd $HOME/fattech/mcp-meta-marketing
python3 -m venv .venv
source .venv/bin/activate
# SDK oficial Anthropic MCP
pip install "mcp[cli]" httpx facebook-business pyyaml
# Estrutura
mkdir -p src tests
touch src/__init__.py src/server.py
touch tests/test_server.py
touch pyproject.toml README.md
Esqueleto do servidor (src/server.py):
 src/server.py
from mcp.server.fastmcp import FastMCP
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
import os, json
mcp = FastMCP("meta-marketing-fattech")
def get_api(tenant_slug: str):
    """Carrega credenciais do Doppler para o tenant."""
    token = os.environ.get(f"META_TOKEN_{tenant_slug.upper()}")
    if not token:
        raise ValueError(f"Token Meta não encontrado para tenant {tenant_slug}")
    return FacebookAdsApi.init(access_token=token)
@mcp.tool()
def list_campaigns(tenant_slug: str, status: str = "ACTIVE") -> str:
    """Lista campanhas do tenant filtradas por status."""
    api = get_api(tenant_slug)
    ad_account_id = os.environ[f"META_AD_ACCOUNT_{tenant_slug.upper()}"]
    account = AdAccount(ad_account_id)
    campaigns = account.get_campaigns(
        fields=['id','name','status','objective','daily_budget'],
        params={'effective_status': [status]}
    )
    return json.dumps([dict(c) for c in campaigns], indent=2)
@mcp.tool()
def get_insights(tenant_slug: str, level: str = "campaign",
                 date_preset: str = "last_7d") -> str:
    """Métricas (gasto, CPA, ROAS, CTR) por nível."""
    api = get_api(tenant_slug)
    ad_account_id = os.environ[f"META_AD_ACCOUNT_{tenant_slug.upper()}"]
    account = AdAccount(ad_account_id)
    insights = account.get_insights(
        fields=['campaign_name','spend','impressions','clicks',
                'ctr','cpc','actions','cost_per_action_type'],
        params={'level': level, 'date_preset': date_preset}
    )
    return json.dumps([dict(i) for i in insights], indent=2)
@mcp.tool()
def pause_ad(tenant_slug: str, ad_id: str, reason: str) -> str:
    """Pausa um anúncio com auditoria do motivo."""
    # IMPORTANTE: ações destrutivas exigem confirmação humana
    # explícita no fluxo do agente
    api = get_api(tenant_slug)
    from facebook_business.adobjects.ad import Ad
    ad = Ad(ad_id)
    ad.api_update(params={'status': 'PAUSED'})
    return json.dumps({'ad_id': ad_id, 'status': 'PAUSED', 'reason': reason})
if __name__ == "__main__":
    mcp.run()
Executar localmente:
 WSL
# Carregar credenciais de todos os tenants ao mesmo tempo
doppler run --project palantyr-clientes --config silva_rocha_prd -- \
  doppler run --project palantyr-clientes --config wiserh_prd -- \
  python src/server.py
# Em outro terminal, testar via MCP inspector:
npx @modelcontextprotocol/inspector python src/server.py
✓ Validação — MCP Inspector abre, lista 3 tools (list_campaigns, get_insights, pause_ad). Chamada manual em list_campaigns retorna JSON de campanhas reais.

#### F2-02

Conectar MCP Meta no Claude Desktop
10 min
Host: WIN
Editar claude_desktop_config.json acrescentando:
 claude_desktop_config.json
"meta-marketing": {
  "command": "wsl.exe",
  "args": [
    "bash", "-c",
    "cd ~/fattech/mcp-meta-marketing && doppler run -- python src/server.py"
  ]
}
✓ Validação — Reiniciar Claude Desktop, perguntar: "Use o MCP meta-marketing para listar campanhas ativas do tenant silva_rocha". Deve retornar campanhas reais.
Bloco LLM Hybrid Router

#### F2-03

Expor Ollama local via Cloudflare Tunnel
30 min
Host: WSL + BROWSER
 WSL
# Instalar cloudflared no WSL
curl -L --output cloudflared.deb \
  https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared.deb
# Autenticar
cloudflared tunnel login
# (abre browser, login com conta Cloudflare FAT Tech)
# Criar tunnel
cloudflared tunnel create palantyr-ollama-local
# Anotar o UUID gerado
# Criar config
mkdir -p ~/.cloudflared
cat > ~/.cloudflared/config.yml <<EOF
tunnel: {UUID_AQUI}
credentials-file: /home/{seu_user}/.cloudflared/{UUID_AQUI}.json
ingress:
  - hostname: ollama.pltr.fattech.com.br
    service: http://localhost:11434
  - service: http_status:404
EOF
# Adicionar DNS no Cloudflare (via browser ou CLI)
cloudflared tunnel route dns palantyr-ollama-local ollama.pltr.fattech.com.br
# Rodar
cloudflared tunnel run palantyr-ollama-local
✓ Validação — Do Oracle: curl https://ollama.pltr.fattech.com.br/api/tags retorna lista de modelos do PC local.
ATENÇÃO — Segurança do tunnel
O endpoint Ollama fica público no domínio pltr. Adicionar autenticação Cloudflare Access (gratuito até 50 usuários) restringindo a apenas requisições com header customizado X-Palantyr-Token. Token gerenciado no Doppler.

#### F2-04

Construir o LLM Hybrid Router
90 min
Host: ORACLE
 ORACLE
# Container Python no Oracle
cd /opt/fattech
mkdir -p llm-router
cd llm-router
cat > Dockerfile <<'EOF'
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app.py .
CMD ["uvicorn","app:app","--host","0.0.0.0","--port","8090"]
EOF
cat > requirements.txt <<'EOF'
fastapi
uvicorn[standard]
httpx
anthropic
openai
pydantic
EOF
Núcleo do roteador (app.py):
 app.py do LLM Router
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx, os
from anthropic import Anthropic
from openai import OpenAI
app = FastAPI()
OLLAMA_URL = os.environ.get("OLLAMA_URL", "https://ollama.pltr.fattech.com.br")
OLLAMA_TOKEN = os.environ.get("OLLAMA_ACCESS_TOKEN")
anthropic_client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
openai_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
class CompletionRequest(BaseModel):
    prompt: str
    llm_requirement: str  # simples | medio | complexo | critico | fallback
    max_tokens: int = 2000
    system_prompt: str = ""
ROUTING = {
    "simples": ("ollama", "gemma3:12b"),
    "medio":   ("ollama", "qwen2.5:14b"),
    "complexo":("claude", "claude-sonnet-4-6"),
    "critico": ("claude", "claude-opus-4-7"),
    "fallback":("openai", "gpt-4o"),
}
async def call_ollama(model, prompt, system, max_tokens):
    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(
            f"{OLLAMA_URL}/api/generate",
            headers={"X-Palantyr-Token": OLLAMA_TOKEN},
            json={"model": model, "prompt": prompt, "system": system,
                  "stream": False, "options": {"num_predict": max_tokens}}
        )
        r.raise_for_status()
        return r.json()["response"]
def call_claude(model, prompt, system, max_tokens):
    resp = anthropic_client.messages.create(
        model=model, max_tokens=max_tokens,
        system=system or "",
        messages=[{"role":"user","content":prompt}]
    )
    return resp.content[0].text
def call_openai(model, prompt, system, max_tokens):
    msgs = []
    if system: msgs.append({"role":"system","content":system})
    msgs.append({"role":"user","content":prompt})
    r = openai_client.chat.completions.create(
        model=model, messages=msgs, max_tokens=max_tokens
    )
    return r.choices[0].message.content
@app.post("/complete")
async def complete(req: CompletionRequest):
    provider, model = ROUTING.get(req.llm_requirement, ROUTING["simples"])
    # Tentativa primária
    try:
        if provider == "ollama":
            text = await call_ollama(model, req.prompt, req.system_prompt, req.max_tokens)
        elif provider == "claude":
            text = call_claude(model, req.prompt, req.system_prompt, req.max_tokens)
        else:
            text = call_openai(model, req.prompt, req.system_prompt, req.max_tokens)
        return {"provider": provider, "model": model, "text": text}
    except Exception as e:
        # Fallback automático para o próximo na escala
        fallbacks = {"ollama":"complexo", "claude":"fallback"}
        if req.llm_requirement in fallbacks and provider != "openai":
            req.llm_requirement = fallbacks[provider]
            return await complete(req)
        raise HTTPException(503, f"Todos os providers falharam: {e}")
@app.get("/health")
async def health():
    out = {}
    for prov, (provider, model) in ROUTING.items():
        out[prov] = {"provider": provider, "model": model}
    return out
Subir e expor:
 ORACLE
docker build -t llm-router:v1 .
docker run -d --name llm-router --restart unless-stopped \
  -p 127.0.0.1:8090:8090 \
  -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  -e OLLAMA_URL=https://ollama.pltr.fattech.com.br \
  -e OLLAMA_ACCESS_TOKEN=$OLLAMA_ACCESS_TOKEN \
  llm-router:v1
# Adicionar host no Nginx Proxy Manager via UI:
# llm.pltr.fattech.com.br → 127.0.0.1:8090 → SSL Let's Encrypt
✓ Validação — curl https://llm.pltr.fattech.com.br/health retorna mapa de providers. Teste real: POST /complete com llm_requirement=simples retorna texto do Ollama; com llm_requirement=complexo retorna texto do Claude.
Bloco Make como proxy de I/O

#### F2-05

Configurar 5 scenarios Make essenciais
60 min
Host: BROWSER (make.com)
Cinco scenarios prioritários a montar no Make (free tier 1.000 ops/mês cobre):
Scenario
Função
consulta-cnpj
Webhook → consulta ReceitaWS / CNPJa → retorna dados públicos
enriquece-empresa
Webhook → busca site, redes sociais, Linkedin público → retorna JSON
scraping-instagram-publico
Webhook → Phantombuster ou Apify proxy → retorna posts públicos
geocode-endereco
Webhook → Google Geocoding → retorna lat/lng + bairro normalizado
deduplica-leads
Webhook → checa Kommo + Postgres → retorna se lead já existe
Cada scenario expõe um webhook que o agente chama. O custo (em ops Make) substitui custo (em tokens LLM) para a tarefa equivalente — ordem de magnitude mais barato.
PROTOCOLO — Padrão de chamada
O agente nunca consulta CNPJ diretamente — sempre via webhook Make. Cada webhook é credenciado por token gerado no Make e armazenado no Doppler em palantyr-core/prd como MAKE_HOOK_{NOME}.

## Fase 3 — Computer Use e Automação Avançada (30 dias)

A Fase 3 entrega capacidades que diferenciam radicalmente a FAT Tech: depuração visual de funis concorrentes, mineração de criativos sem API e ações em ferramentas legadas. Computer Use roda em instância Linux dedicada com VNC, nunca na máquina pessoal do CEO.
Provisionar máquina Computer Use

#### F3-01

Provisionar VM Linux com desktop no Oracle
60 min
Host: BROWSER (Oracle Cloud Console)
Compute → Instances → Create Instance
Nome: palantyr-cu-01
Shape: VM.Standard.A1.Flex (ARM) com 2 OCPU / 12 GB RAM (dentro do Always Free Tier expandido)
Image: Ubuntu 22.04
Network: mesma VCN do Palantyr v3 principal
SSH keys: importar a sua já existente
Após criação, conectar:
 ORACLE → VM CU
ssh ubuntu@{IP_DA_NOVA_VM}
# Instalar desktop leve + VNC
sudo apt update && sudo apt upgrade -y
sudo apt install -y xfce4 xfce4-goodies tightvncserver firefox \
  python3-pip python3-venv git curl jq
# Configurar VNC
vncpasswd
# (criar senha forte — guardar no Doppler como CU_VNC_PASSWORD)
# Iniciar VNC server
vncserver :1 -geometry 1920x1080 -depth 24
✓ Validação — Túnel SSH local para a VNC: ssh -L 5901:localhost:5901 ubuntu@{IP_CU}. No Windows, abrir TightVNC Viewer → localhost:5901 → digitar senha → ver desktop Xfce.

#### F3-02

Instalar Claude Computer Use
30 min
Host: ORACLE → VM CU
 VM CU
# Container oficial Anthropic com Computer Use
docker run \
  -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  -v $HOME/anthropic:/home/computeruse/.anthropic \
  -p 5900:5900 \
  -p 8501:8501 \
  -p 6080:6080 \
  -p 8080:8080 \
  -it ghcr.io/anthropics/anthropic-quickstarts:computer-use-demo-latest
✓ Validação — Acessar http://{IP_CU}:8080 (com auth) — interface do Computer Use carrega. Comando teste: "Abra o Firefox e navegue até google.com". Claude controla o desktop via screenshots.
PERIGO — Isolamento e segurança
Esta VM NUNCA tem acesso à rede interna FAT Tech (sem VPN, sem chaves Oracle). Acesso apenas via internet pública através de Cloudflare Access. Snapshots automáticos diários para rollback em caso de algo dar errado.
Skills Computer Use a construir nesta fase
CU-Skill-01 — Depuração de funil concorrente
Recebe URL → abre Firefox → navega pelo funil até o checkout → extrai pixels Meta/Google, tags GTM, eventos JS, formulários, links de checkout → retorna relatório estruturado. Substitui hora de análise manual por minutos de execução.
CU-Skill-02 — Mineração de criativos sem API
Recebe nicho → abre Instagram/TikTok → scroll automatizado por hashtags → identifica vídeos com alto engagement → captura links → arquiva metadados no Drive. Substitui Apify para casos onde API não cobre.
CU-Skill-03 — Operação em ferramenta legada do cliente
Recebe credencial temporária do cliente → opera painel sem API (sistemas de gestão tributária, ERPs antigos, CRMs de nicho) → extrai dados ou executa ações pontuais. Usar apenas mediante autorização contratual explícita.

## Fase 4 — Soberania completa e Compliance (60 dias)

A Fase 4 consolida a operação como sistema profissional. Backup tripartido, disaster recovery testado, LGPD operacional, cláusulas contratuais ajustadas. Ao final, a FAT Tech pode auditar-se externamente sem constrangimento.
Blocos da Fase 4
Bloco
Entregáveis
Backup tripartido
Git diário (já ativo) + snapshot Oracle Object Storage semanal + cópia mensal off-site (Backblaze ou Wasabi)
Disaster recovery test
Cenário 1: Oracle inacessível por 6h — operação resiliente. Cenário 2: Anthropic API offline — Ollama assume. Cenário 3: Doppler offline — fallback de cache cifrado local
LGPD operacional
Endpoint /lgpd/acesso, fluxo de exclusão em cascata, política de retenção automatizada
Rotação de credenciais
Cronjobs gerando novos tokens Meta a cada 90 dias e atualizando Doppler
Observabilidade
Grafana + Prometheus + Loki no Oracle, dashboards por tenant
Sandbox de testes para skills
Ambiente isolado (Docker compose) onde skills novas rodam antes de promover para produção
Contratos atualizados
Cláusula 'Uso de IA' em todos os contratos novos a partir da data X
DPO formal
Processo de DPO terceirizado avaliado para quando atingir 50 clientes
Disaster recovery — cenários obrigatórios
DR-01 — Oracle inacessível por 6h
Sintoma: deploys falham, agente sem audit log.
Resposta esperada: skills com llm_requirement em [simples, medio] continuam funcionando via Ollama local; skills críticas pausam e enfileiram comandos.
Validação: simular shutdown da VM Oracle por 1h em horário comercial, medir downtime real.
DR-02 — Anthropic API offline
Sintoma: skills complexas falham com 503.
Resposta esperada: LLM Hybrid Router faz fallback para Ollama com modelo mais robusto (qwen2.5:14b) e marca a saída como degraded_mode no audit log.
Validação: bloquear DNS da Anthropic via Cloudflare por 30 minutos e validar que operação degrada mas não para.
DR-03 — Doppler offline
Sintoma: aplicações não conseguem inicializar.
Resposta esperada: cache local cifrado de últimos segredos válidos (Doppler tem essa feature nativa) permite operação degradada por até 24h.
Validação: revogar token Doppler do servidor e verificar continuidade.

### Referências Rápidas

Endpoints canônicos
Serviço
Endpoint
Onde
n8n
https://n8n.pltr.fattech.com.br
Oracle (Palantyr v3)
Evolution API
https://evolution.pltr.fattech.com.br
Oracle (Palantyr v3)
Portainer
https://portainer.pltr.fattech.com.br
Oracle (Palantyr v3)
Nginx Proxy Manager
https://nginx.pltr.fattech.com.br:81
Oracle (Palantyr v3)
LLM Router
https://llm.pltr.fattech.com.br
Oracle (Fase 2)
Ollama (via tunnel)
https://ollama.pltr.fattech.com.br
WSL local (Fase 2)
Computer Use
Acesso restrito via Cloudflare Access
VM CU (Fase 3)
Postgres palantyr
163.176.163.204:5432/palantyr
Oracle (Fase 1)
Comandos canônicos do operador
 Cheat sheet
# Slack DM ao agente
/skill <skill_id> <tenant> [args...]
/tenant <slug> info
/tenant <slug> health
/audit <tenant> <horas>
/budget <tenant> <mes>
/rollback <skill_id> <versao_anterior>
# Terminal WSL
cd $BRAIN_DIR && git pull && git status
doppler secrets --project palantyr-clientes --config silva_rocha_prd
curl -X POST http://localhost:8088/intent -d '{...}'
# Em Claude Desktop
"Executa <skill_id> para o tenant <slug>"
"Lista skills em produção"
"Mostra audit log de <tenant> nas últimas 24h"
"Diagnostica anomalia em <tenant>"
Glossário de hosts
Host
IP / endereço
Acesso
ORACLE
163.176.163.204
SSH com chave + Cloudflare para subdomínios
VM CU
(IP fixo da nova VM Fase 3)
SSH + Cloudflare Access
WSL
Localhost dentro do Windows
Acesso direto pelo terminal Ubuntu
WIN
Windows 11 + RTX 4060
Físico
Próxima ação imediata após ler este manual
Validar pré-voo (PV-01 a PV-05). Se tudo OK, iniciar F0-01. Tempo estimado dos primeiros 4 passos: 35 minutos. Ao final, repo criado, estrutura canônica em produção, manual em mãos.
—  FIM DO MANUAL DE EXECUÇÃO  —
PALANTYR v4 — FAT Tech — 2026
Mago Supremo das IAs
