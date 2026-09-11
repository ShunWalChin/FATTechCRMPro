# Funis configuráveis e motivo de perda — 11/09/2026

Segunda publicação na Oracle, sobre a base de 11/09. Release `git-23c04e6`, commit
[`23c04e6`](https://github.com/ShunWalChin/FATTechCRMPro/commit/23c04e6).
A publicação anterior continua descrita em [2026-09-11.md](2026-09-11.md).

## O que mudou para a equipe

As seis etapas de oportunidade deixaram de ser fixas no código e passaram a ser configuração
da organização, em `/crm/funis`. Cada etapa declara rótulo, probabilidade e se representa
andamento, ganho ou perda. Mover uma oportunidade para uma etapa de perda passa a exigir o
motivo, que fica no histórico do registro; sair dessa etapa limpa o motivo.

O dashboard passou a derivar as colunas do funil em vez de uma lista fixa, e acrescenta a
previsão ponderada: soma `valor × probabilidade` das etapas em andamento e divide uma única
vez por cem, sem acumular arredondamento por linha.

## Migração 0002

`0002` altera apenas dados; `models.py` não mudou e nenhuma tabela ou coluna foi criada.
Ela cria o funil padrão de cada organização com as seis etapas históricas e grava
`pipeline_id` nas oportunidades existentes, sem tocar em `version` nem `updated_at` —
um backfill de schema não é edição de usuário e não deve invalidar a concorrência otimista
de um cliente aberto. Oportunidades já encerradas em perda recebem um `lost_reason` que
declara a ausência do dado em vez de inventar um motivo.

A API de produção passou a exigir a marca `0002` na inicialização. Isso é proposital:
sem o backfill, toda escrita de oportunidade falharia por ausência de funil. O efeito
colateral aceito é que uma migração malsucedida deixa a API fora do ar em vez de servir
comportamento inconsistente.

## Sequência executada

| Etapa | Evidência |
|---|---|
| CI | Execução [34644773915](https://github.com/ShunWalChin/FATTechCRMPro/actions/runs/34644773915), `success`, com PostgreSQL 17, pytest, TypeScript, build, `npm audit` e Playwright |
| Backup prévio | `fattech-20260911T203639Z.dump`, SHA-256 conferido |
| Pacote | `git archive HEAD`, SHA-256 `ddd897f3…61311e`, conferido no servidor após o envio |
| Integridade | 125 arquivos versionados conferidos byte a byte contra `docs/FILE_INVENTORY.csv` |
| Ensaio da 0002 | Dump restaurado em banco descartável `fattech_dryrun_…`, migração executada com a imagem nova, banco removido ao fim |
| Deploy | `infra/deploy.sh`; quatro contêineres saudáveis em `fattechcrmpro-{api,web}:git-23c04e6` |
| Verificação | 19 checagens contra o HTTPS público, todas aprovadas |

### Resultado do ensaio antes de tocar no banco real

Restaurando o dump de produção num banco descartável e rodando a migração com a imagem nova:
`schema_migrations` foi de `0001` para `0001,0002`; as duas oportunidades do dump passaram de
duas sem `pipeline_id` para zero; a soma de `version` das oportunidades permaneceu `6`;
um funil `active` com seis etapas foi criado para a organização FAT Tech; a RLS continuou
forçada nas quatro tabelas; e uma segunda execução da migração manteve um único funil,
comprovando idempotência.

### Verificação contra a publicação

Login do proprietário; funil com as seis etapas e etapa de perda declarada; dashboard com
`weighted_pipeline_cents` e etapas trazendo rótulo e resultado; oportunidade nova adotando o
funil padrão e a probabilidade da etapa (10%); perda sem motivo recusada com 422; perda com
motivo aceita e persistida; retorno à etapa anterior limpando o motivo e ajustando a
probabilidade para 30%; remoção de etapa ocupada bloqueada com 409; site público, `/crm/funis`
e `/crm/pipeline` respondendo 200.

O registro sintético `Verificacao de deploy 23c04e6` foi arquivado por exclusão lógica ao fim
da prova. Permanecem apenas a exclusão lógica e os eventos de auditoria, sem cliente inventado
na operação.

## Limites honestos desta publicação

No instante da migração a organização não possuía oportunidades ativas — as duas presentes no
dump eram registros sintéticos da validação anterior, já excluídos logicamente. O backfill foi
comprovado em PostgreSQL real, com dados reais do dump, mas **não em volume**: a prova é
estrutural, não de carga.

A conferência visual da nova interface em produção não foi feita por navegador, porque isso
exigiria digitar a senha do proprietário num formulário. A interface está coberta pelos oito
testes Playwright, que dirigem o editor de etapas, o seletor de funil e o diálogo de perda
sobre o mesmo código, e pelas respostas 200 das rotas autenticadas em produção.

`deploy.sh` mantém os contêineres antigos servindo enquanto a migração roda. Uma oportunidade
criada nesses segundos nasceria sem `pipeline_id` e não apareceria no quadro até ser editada.
A consulta de órfãs após o deploy retornou zero.

## Rollback

Reverter apenas a imagem funciona sem tocar nos dados: o código anterior continua encontrando
a marca `0001`, e em `update_record` as chaves que ele desconhece (`pipeline_id`, `lost_reason`)
caem em `protected` e sobrevivem às edições. As imagens `fattechcrmpro-{api,web}:git-a9adce7`
permanecem no servidor.

Ressalva: oportunidades movidas para etapas de um funil **personalizado** criado após esta
publicação ficam ineditáveis no código anterior, porque `Deal.stage` volta a ser um `Literal`
das seis etapas fixas e responde 422. As que estiverem nas seis etapas históricas continuam
normais.

## Pendências criadas ou mantidas

- O backfill da `0002` não é exercitado sobre PostgreSQL pela CI: `test_postgres.py` roda a
  migração antes de existir qualquer organização, e o teste de backfill é SQLite.
  A prova continua dependendo do ensaio manual com dump restaurado.
- `infra/verify-backup.sh` passou a exigir também a marca `0002` nos dumps.
- Cópia do backup para fora do servidor, retenção por volume e alerta de falha continuam pendentes.
