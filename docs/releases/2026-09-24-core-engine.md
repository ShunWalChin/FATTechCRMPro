# Deploy Oracle — 24/09/2026 UTC

## Versão publicada

- Commit: `6e8484a0cadd87fd59279b7236086d80af7e6f6b`.
- Tag das imagens: `0.5.1-20260924-core`.
- SHA256 do pacote: `93abe2e0ee488ee53adcd3604d9abd3093875b439cb4bb1e8e7c3109967d12a5`.
- Instalação: `/opt/fattechcrmpro`, Oracle.
- CRM: https://fattechcrmpro.64.181.178.125.nip.io/login
- Site: https://fattech.com.br/

Publicado o conteúdo versionado até esse commit, incluindo Core-Engine, SYNAPSE, ingestão Instagram, auditoria encadeada, infraestrutura de agentes e Posiciona. O deploy passou a iniciar o core-worker e interromper os escritores antigos antes das migrações. O banco de pautas do Posiciona agora acompanha a imagem da API.

## Evidências

- Suíte com validação PostgreSQL configurada: 359 testes passaram, nenhum ignorado; 2 avisos de depreciação. Os testes específicos de PostgreSQL usaram o banco isolado de validação.
- Após a correção do empacotamento Posiciona: 15 testes direcionados passaram.
- Build Docker da API e web concluído; compilação Next e TypeScript concluídas.
- API, web, worker, core-worker e PostgreSQL saudáveis ao fim da instalação.
- Arquivo RELEASE confirmou o commit publicado.
- Health da API: status ok, ambiente production, versão declarada 0.5.1.
- Site público e login: HTTP 200.
- Migrações 0001 a 0010 presentes no banco.
- Preservados 1 organização, 4 usuários e 70 registros.
- Auditoria: 275 linhas conferidas, cadeia íntegra, zero problemas.
- 4 registros de heartbeat do Core-Engine presentes.
- Banco de pautas carregado com sucesso dentro do container de produção.

## Recuperação

- Backup anterior verificado por restauração em banco temporário: `/var/backups/fattechcrmpro/fattech-20260924T024311Z.dump`; hash e contagens conferidos. Banco temporário removido pela rotina.
- Backup adicional criado pelo instalador: `/var/backups/fattechcrmpro/fattech-20260924T024721Z.dump`.
- Código anterior preservado em `/var/backups/fattechcrmpro/code-4828ebb-before-6e8484a.tar.gz`.
- Nenhuma restauração foi executada sobre o banco de produção.

## Limites operacionais

`external_sends_enabled` permanece false. A publicação não habilitou disparos externos, não ativou agentes nem enviou mensagens. O agendamento de execuções de agentes não equivale a um provedor LLM externo configurado e operacional. A verificação pública cobriu disponibilidade do site e login; não foi executada nesta etapa uma nova suíte completa de navegação autenticada em produção.

Este relatório documenta o commit acima; o commit posterior que adiciona o relatório não altera o código publicado.
