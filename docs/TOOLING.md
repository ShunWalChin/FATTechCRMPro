# Ferramentas de engenharia

## O que pertence a cada ferramenta

| Ferramenta | Uso neste projeto | Instalação reproduzível |
|---|---|---|
| Ruflo 3.41.2 | Coordenação, registro de tarefas, memória e catálogo de agentes | `npm install --prefix .local/tooling --save-exact ruflo@3.41.2` |
| Ponytail 4.9.0 | Reutilização, recursos nativos, revisão de complexidade preservando validação | Plugin Codex `ponytail@ponytail` |
| HeroUI React/Styles 3.2.5 | Componentes reais da interface React e tokens acessíveis | `npm ci` pelo lockfile |
| Graphify 0.9.57 | Grafo AST consultável de funções, módulos e dependências | `uv tool install graphifyy==0.9.57 --python 3.12` |

Ruflo é o coordenador: cadastrar um agente não executa implementação por si só.
Os agentes de execução do Codex implementam e verificam o código. A aplicação de negócio
é executada sem depender de um processo Ruflo ativo. Isso mantém a disponibilidade do CRM
independente da estação de engenharia.

`python scripts/bootstrap-tooling.py` instala as versões acima. Os clones ficam em
`.local/references`; não são incorporados ao código autoral nem à imagem de produção.
Os SHAs e as licenças estão em `docs/discovery/repositories.md`.

## Ruflo

O wrapper `node scripts/ruflo.mjs` usa o binário local e guarda estado em `.local/engineering`.
Exemplos:

```text
node scripts/ruflo.mjs status
node scripts/ruflo.mjs swarm init --topology hierarchical --max-agents 4 --strategy specialized
node scripts/ruflo.mjs agent spawn --type architect --name fattech-architecture
node scripts/ruflo.mjs memory init --backend hybrid
node scripts/ruflo.mjs task list
node scripts/ruflo.mjs mcp start
```

Na instalação observada, `init --codex --full --all-agents` instalou 6 skills canônicas
e informou que 103 entradas do catálogo não possuem assets empacotados. Essas entradas
não estão disponíveis por efeito da flag `--full`; não declarar todas as capacidades
instaladas sem verificar o catálogo e seus requisitos.

O autodetector da versão instalada não encontrou o Codex no Windows, embora o executável
esteja no PATH. O servidor MCP pode ser registrado explicitamente apontando para este wrapper.
Não habilitar serviços cloud, cadastro de contas ou execução paga apenas por existirem no catálogo.

### Limite observado no Windows (12/09/2026)

`memory store` funciona até o daemon subir e criar os sidecars `-wal`/`-shm`. A partir daí toda
escrita falha com *"refusing an unsafe sql.js whole-image write"*, porque a ponte nativa
better-sqlite3 está desabilitada no Windows após a issue #3024 do projeto. Parar o daemon não
resolve: a própria invocação seguinte do CLI o reinicia.

Consequência prática: as nove entradas gravadas antes do primeiro `status` persistem e a busca
semântica funciona sobre elas, mas atualizações posteriores são perdidas silenciosamente se o código
de saída não for conferido. `doctor` sinaliza o mesmo problema por outro ângulo, ao notar que o banco
tem 11 tabelas — formato do fallback sql.js — em vez das ~47 do schema nativo.

Existe a opção `CLAUDE_FLOW_ENABLE_NATIVE_BRIDGE_ON_WINDOWS=1`, que não foi ativada: habilitar uma
ponte que o próprio projeto desligou por segurança é decisão do operador, não do agente.

## Graphify

```text
graphify update . --no-cluster
graphify query "require_auth"
graphify path "require_auth" "set_tenant"
graphify export html
```

O grafo é gerado de código local por AST e não necessita de uma chave de IA.
`graphify-out/` fica fora do Git por conter caminhos locais e artefatos regeneráveis.
`.graphifyignore` exclui clones, bancos, ambientes, segredos e dependências.
O inventário publicado de arquivos é produzido separadamente com `npm run inventory`.

## Ponytail

Instalado via marketplace oficial do projeto, versão 4.9.0. A skill foi lida e aplicada:
usar recursos existentes da plataforma, evitar dependências que não tragam benefício,
preservar limites de confiança, integridade, acessibilidade e todo requisito explícito.
Os hooks do plugin são carregados pelo Codex conforme o ciclo de vida da instalação;
não confundir instalação com evidência de execução de um hook nesta tarefa.

## Atualizações

Atualizar uma ferramenta de cada vez, registrar versão/commit, rodar o conjunto de verificações
e revisar mudanças de licença. Métricas promocionais de ferramentas não são benchmarks do CRM.
