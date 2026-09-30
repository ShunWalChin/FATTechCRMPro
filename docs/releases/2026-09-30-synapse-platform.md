# SYNAPSE — publicação da identidade da plataforma

Data: 30/09/2026. Ambiente: Oracle, produção.

## Resultado

Publicado o commit `b5bcb51a03d0407c566c410234adf4585cdfd36f`, com imagens
`0.7.0-20260930-synapse`. A versão funcional da API permanece **0.7.0**.
A reorganização estabelece SYNAPSE como plataforma e CRM/ERP como módulos.

- Acesso: https://fattechcrmpro.64.181.178.125.nip.io/login
- Entrada após autenticação: `/crm/inicio`.
- Navegação: Início, CRM, ERP, Comunicação, Inteligência, Equipes e Configurações.
- Os 34 destinos anteriores permanecem; a entrada da plataforma resulta em 35 destinos únicos.
- `/crm` continua sendo o painel comercial; `/crm/synapse` passa a ser apresentado como
  **Implantação comercial**, dentro de Configurações.

Não houve alteração de contrato da API, modelo de dados ou migração nova nesta rodada.
O site público não teve seus arquivos nem apontamentos DNS alterados por este deploy.

Modelo do produto e navegação: [SYNAPSE_PLATFORM_MODEL.md](../SYNAPSE_PLATFORM_MODEL.md).
Próxima rodada: [SYNAPSE_UPGRADES_0.8.md](../SYNAPSE_UPGRADES_0.8.md).

## Artefato e execução

| Item | Evidência |
| --- | --- |
| Release anterior | `234c97e`, imagens `0.7.0-20260928-audit2` |
| Release publicado | `b5bcb51a03d0407c566c410234adf4585cdfd36f` |
| Arquivo | `/home/opc/synapse-b5bcb51.tar.gz` |
| SHA-256 | `22d1ef9d41334a45d0665f3e5a7cbc93cc337caa367b87b7077ac843d75f0ab1` |
| Tamanho | 4.368.500 bytes |
| Inventário do artefato | 457 arquivos conferidos, nenhuma divergência |
| Instalação | `infra/install-release.sh` e `infra/deploy.sh` existentes |
| Log remoto | `/home/opc/deploy-synapse-b5bcb51.log` |
| Código de saída | `0`, em `/var/run/fattechcrmpro-deploy-b5bcb51.status` |
| Marcador remoto | `/opt/fattechcrmpro/RELEASE` contém o commit publicado |

O pacote foi gerado a partir de árvore Git limpa, sem arquivos locais de acesso.
A publicação reutilizou o terminal do Ruflo após indisponibilidade do executor local.
O instalador validou o checksum, conferiu o inventário, construiu as imagens e aguardou
a saúde dos serviços antes de registrar a release.

## Backup e recuperação

Antes da instalação, foi criado e efetivamente restaurado o backup
`/var/backups/fattechcrmpro/fattech-20260930T113214Z.dump` em banco temporário exclusivo.
Resultado: `restore_verified`, 1 organização, 10 usuários, 81 registros; verificação em 2 segundos.
O banco temporário foi removido ao final. O instalador criou ainda
`/var/backups/fattechcrmpro/fattech-20260930T113217Z.dump`.

Os artefatos da instalação anterior estão protegidos em
`/var/backups/fattechcrmpro/releases/synapse-b5bcb51-predeploy`:

- `previous-tree.tar.gz` e checksum: código anterior.
- `previous.env`: configuração anterior, contém segredos; nunca publicar ou imprimir.
- `previous-commit.txt` e `previous-services.txt`: referência anterior e imagens.
- `verified-backup.txt`: identificação do backup restaurado.

Não foi necessário rollback. Para uma reversão, o operador deve primeiro conferir esses
artefatos, a compatibilidade do schema e os logs; restaurar código/configuração anterior e
reutilizar o procedimento de deploy, validando saúde e login. Como esta release não mudou
o schema, uma reversão de aplicação não exige restaurar o banco. Restauração de dados deve
ser uma decisão separada, considerando as gravações posteriores ao backup. O instalador
atual não executa rollback automático.

## Verificação em produção

Verificações efetuadas aproximadamente entre 11:41 e 11:44 UTC (08:41–08:44 de Brasília).

| Verificação | Resultado |
| --- | --- |
| Serviços Docker | API, web, worker, core-worker e PostgreSQL saudáveis |
| `/api/health` e `/api/v1/health` | `status=ok`, `version=0.7.0`, `environment=production` |
| Login real | Sucesso; título “Entrar no SYNAPSE”; redirecionamento para `/crm/inicio` |
| Rotas autenticadas | Os 35 destinos da navegação responderam HTTP 200 |
| Renderização representativa | Início, painel comercial, pipeline, financeiro, conversas, conhecimento, IA, equipe e integrações |
| Erros JavaScript observados | Nenhum erro de página capturado no percurso |
| Mobile | 390 × 844; menu em cascata levou à operação do agente; largura total 390 px |
| Auditoria da organização | 307 linhas conferidas, cadeia íntegra, zero linhas faltantes, zero problemas |
| Core-Engine | 306 entregas concluídas; zero pendentes, em processamento ou dead-letter |
| Heartbeats internos | `bi`, `messaging` e `scheduler` saudáveis |
| Site público | `https://fattech.com.br/` respondeu HTTP 200 |

Antes da publicação: build/typecheck do frontend aprovados; 48 testes Playwright aprovados,
mais 4 verificações após o ajuste final de CSS. O teste em produção foi de leitura e
navegação; não enviou mensagens, criou propostas nem executou transações financeiras.
HTTP 200 em uma rota não representa homologação completa de todos os seus fluxos.

As evidências locais e capturas ficam em `.local/`, fora do Git:
`deploy-browser-check.json`, `deploy-api-check.json`, `deployed-synapse-desktop.png` e
`deployed-synapse-mobile.png`. Credenciais foram lidas de arquivo privado, sem exposição.

## Limites operacionais confirmados

- `external_sends_enabled=False` no processo da API: este deploy não habilitou disparos.
- `n8n_configured=false` no Core-Engine da organização verificada.
- Serviços saudáveis e tela de IA disponível não provam funcionamento de um provedor
  externo, do runtime OpenClaw ou de uma conversa autônoma real.
- Os testes utilizaram a organização e uma conta autorizada existentes; não substituem
  homologação com múltiplas organizações e perfis.
- A nova classificação ERP reúne projetos, catálogo e financeiro interno. Não cria
  emissão fiscal, contabilidade ou gestão de estoque.
- Os documentos deste fechamento são versionados depois da publicação; o marcador
  `RELEASE` identifica o código efetivamente instalado, não o commit posterior dos relatórios.
