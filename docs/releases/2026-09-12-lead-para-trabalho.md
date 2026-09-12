# Do lead ao trabalho, kanban arrastável e ferramental — 12/09/2026

Quarta publicação na Oracle. Fecha o primeiro fluxo de receita, liga o campo de ordenação que a
rodada anterior deixou sem uso e corrige um artefato de design que induzia ao erro.

## Captação do site abre trabalho, não só registro

O WEB-03 pede que uma submissão válida crie contato, oportunidade e atividade. Havia só o contato.
Agora o lead entra com uma oportunidade na primeira etapa aberta do funil padrão e uma tarefa de alta
prioridade vencendo no dia seguinte.

Duas travas impedem que isso vire ruído, e a segunda só apareceu porque um teste existente quebrou:

- Um reenvio **não** abre segunda oportunidade; anexa-se à que já está correndo. Sem isso, dez
  preenchimentos do formulário inflariam o pipeline que a equipe comercial lê.
- Um reenvio só cria tarefa se o contato não tiver nenhuma em aberto. A primeira versão criava uma
  tarefa por submissão — dez reenvios, dez lembretes idênticos. O teste de rate limit, que dispara
  dez leads iguais, expôs isso antes de chegar a produção.

Fechada a tarefa pela equipe, um contato que volta a procurar gera uma próxima ação nova. Está coberto
por `test_website_lead_becomes_an_opportunity_and_a_next_action`.

`FATTECH_CAPTURE_CREATES_DEAL` nasce em `true` e permite reduzir a captação ao contato, caso a equipe
prefira manter o pipeline exclusivamente manual.

## Kanban arrastável

A rodada anterior acrescentou `position` ao schema e não usou o campo — débito que este release paga.
Agora a listagem de oportunidades ordena por posição e depois por data, de modo que a coluna reflete a
prioridade do operador e não a idade do registro. Cartões novos entram no fim da coluna com intervalo
de 1000, deixando espaço para soltar entre vizinhos.

Arrastar um cartão para outra coluna muda a etapa; soltar sobre um cartão insere antes dele. Soltar em
uma etapa de perda abre o mesmo diálogo de motivo já existente, levando junto a posição pretendida.

O seletor "Mover para" **continua existindo** e foi alinhado ao mesmo cálculo de posição: arrastar não
é acessível por teclado, então remover o seletor teria trocado uma melhoria por uma regressão.

## Design system alinhado ao que existe

`design-system/fat-tech-crm-pro/MASTER.md` prescrevia Fira Code/Fira Sans com paleta azul e âmbar. A
interface publicada usa Inter com navy, mint e teal desde o primeiro release. O arquivo foi reescrito a
partir de `globals.css`, que passa a ser declarado como fonte de verdade, e as especificações de
componente deixaram de citar cores que nunca existiram no produto.

## Ferramental Ruflo nesta rodada

O Ruflo foi usado no papel que o nosso próprio `TOOLING.md` define — coordenação e memória, não
execução. O que ele produziu de concreto:

| Comando | Resultado observado |
|---|---|
| `doctor` | Ambiente saudável; apontou que o banco de memória tem 11 tabelas, formato do fallback sql.js, e que criptografia em repouso está desligada |
| `security scan apps` | Um achado MEDIUM de React XSS em `page.tsx` |
| `analyze complexity` | `crm-ui.tsx` com complexidade ciclomática 65; `resource-page.tsx` com 38 |
| `analyze circular` | Nenhuma dependência circular na API |
| `memory` | Nove entradas de estado verificado, com busca semântica funcional |
| `task` | Backlog registrado; tipos `ops` e `refactor` foram recusados silenciosamente pelo CLI |

**O achado de XSS é falso positivo, e verificar custou pouco.** Os dois usos de
`dangerouslySetInnerHTML` são conteúdo confiável de build: o JSON-LD é objeto literal estático com `<`
escapado, e o blog renderiza conteúdo que passa por allowlist na importação. Conferindo os 22 artigos
publicados: apenas oito tags — `blockquote, br, em, h2, li, p, strong, ul` — e zero ocorrências de
`<script`, `onerror=`, `onload=`, `javascript:`, `<iframe` ou `srcdoc`. A ferramenta apontou uma
categoria; a evidência veio da verificação.

A complexidade de `crm-ui.tsx` é real e ficou registrada como tarefa, não atacada agora: o arquivo
acabou de receber os seletores de relação de outra frente, e refatorar sobre trabalho recém-entregue
troca risco por estética.

## Evidências

| Verificação | Resultado |
|---|---|
| Testes Python | 81 passaram, 2 pulados |
| Testes de navegador | 11 passaram |
| TypeScript e build | Limpos |
| Migração | Nenhuma; `position` resolve para zero quando ausente e a ordenação usa `coalesce` |

## Limites honestos

Arrastar-e-soltar usa HTML5 nativo e não funciona por toque em todos os navegadores móveis; o seletor
de etapa continua sendo o caminho garantido em qualquer dispositivo e por teclado.

O cálculo de posição usa o ponto médio entre vizinhos. Com intervalos de 1000 isso comporta muitas
reordenações, mas posições adjacentes podem colidir depois de muitos movimentos entre os mesmos dois
cartões; o desempate por data de criação mantém a ordem estável, e uma renumeração periódica resolveria
em definitivo se algum dia fizer falta.
